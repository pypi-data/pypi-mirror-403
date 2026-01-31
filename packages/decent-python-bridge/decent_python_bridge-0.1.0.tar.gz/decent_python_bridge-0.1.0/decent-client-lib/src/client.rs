use crate::chat::ChatMessage;
use anyhow::Result;
use dashmap::DashMap;
use rand::{rngs::OsRng, RngCore};
use relay_lib::api::packager::Packager;
use relay_lib::block::block::Block;
use relay_lib::crypto::asymmetric::AsymCrypt;
use relay_lib::crypto::asymmetric::{SigningKey, VerifyingKey};
use relay_lib::crypto::symmetric::AESCipher;
use relay_lib::crypto::SymmetricCipher;
use relay_lib::pow::difficulty::Difficulty;
use relay_lib::pow::policy::PowPolicy;
use relay_lib::transport::QuicClient;
use relay_lib::util::constants::{CMD_HANDSHAKE_INIT, CMD_HANDSHAKE_RESP, CMD_PING};
use std::sync::Arc;
use std::time::Instant;

#[derive(Clone, Debug)]
pub struct RelayClient {
    pub client: Arc<QuicClient>,
    pub relay_addr: String,
    pub keys: KeyPair,
    pub session_cipher: Option<AESCipher>,
    pub pending_pings: DashMap<u64, Instant>,
    pub pow_policy: Arc<PowPolicy>,
    pub current_difficulty: Arc<std::sync::RwLock<Difficulty>>,
    pub circuit_manager: Arc<relay_lib::circuit::CircuitManager>,
    pub relay_id: std::sync::Arc<std::sync::RwLock<Option<String>>>,
    /// Session ephemeral private key (generated once per session)
    pub session_ephemeral_key: relay_lib::crypto::asymmetric::SecretWrapper,
    /// Cached ephemeral PUBLIC key (computed once from session_ephemeral_key)
    pub session_ephemeral_pub: relay_lib::crypto::asymmetric::PublicKey,
    /// Cached X25519 private key derived from Ed25519 signing key (computed once)
    pub cached_x25519_priv: relay_lib::crypto::asymmetric::SecretWrapper,
    /// Cache of recipient X25519 public keys to avoid per-message Ed25519->X25519 conversion
    pub recipient_x25519_cache: DashMap<String, relay_lib::crypto::asymmetric::PublicKey>,
    /// Cache of derived AES-256 keys per recipient (from ECDH + HKDF, computed once per recipient)
    pub recipient_aes_cache: DashMap<String, [u8; 32]>,
}

#[derive(Clone, Debug)]
pub struct KeyPair {
    pub private: SigningKey,
    pub signing_key: SigningKey, // alias
    pub verifying_key: VerifyingKey,
}

impl RelayClient {
    // ... public_key removed (duplicate) ... use the one in impl
    pub async fn connect(address: &str, signing_key: SigningKey, pow_policy: Arc<PowPolicy>, circuit_manager: Arc<relay_lib::circuit::CircuitManager>) -> Result<(Self, Arc<QuicClient>, Option<AESCipher>)> {
        let mut q_client = QuicClient::new()?;
        q_client.connect(address).await?;

        // Wrap in Arc
        let client_arc = Arc::new(q_client);

        let vk = signing_key.verifying_key();
        let keys = KeyPair {
            private: signing_key.clone(),
            signing_key: signing_key,
            verifying_key: vk,
        };

        // Generate session ephemeral key ONCE and compute public key ONCE
        let session_eph_priv = relay_lib::crypto::asymmetric::StaticSecret::random_from_rng(&mut rand::rngs::OsRng);
        let session_eph_pub = relay_lib::crypto::asymmetric::PublicKey::from(&session_eph_priv);

        let mut relay_client = RelayClient {
            client: client_arc.clone(),
            relay_addr: address.to_string(),
            keys: keys.clone(),
            session_cipher: None,
            pending_pings: DashMap::new(),
            pow_policy,
            current_difficulty: Arc::new(std::sync::RwLock::new(Difficulty::default())),
            circuit_manager,
            relay_id: std::sync::Arc::new(std::sync::RwLock::new(None)),
            session_ephemeral_key: relay_lib::crypto::asymmetric::SecretWrapper(session_eph_priv),
            session_ephemeral_pub: session_eph_pub,
            cached_x25519_priv: relay_lib::crypto::asymmetric::SecretWrapper(AsymCrypt::ed_priv_to_x25519(&keys.signing_key)),
            recipient_x25519_cache: DashMap::new(),
            recipient_aes_cache: DashMap::new(),
        };

        // Handshake
        let (cipher, relay_pk) = relay_client.perform_handshake().await?;
        relay_client.session_cipher = cipher.clone();
        if let Some(pk) = relay_pk {
            *relay_client.relay_id.write().unwrap() = Some(pk);
        }

        Ok((relay_client, client_arc, cipher))
    }

    // ... imports
    // Removed serde_cbor, serde_json

    // Handshake over QUIC
    async fn perform_handshake(&self) -> Result<(Option<AESCipher>, Option<String>)> {
        // 1. Send Handshake Init
        let my_pub = AsymCrypt::verifying_key_to_string(&self.keys.verifying_key);

        #[derive(minicbor::Encode)]
        struct HandshakeInit {
            #[n(0)] id: String,
            #[n(1)] n: Vec<u8>,
        }

        let mut rng = OsRng;
        let mut nonce = [0u8; 16];
        rng.fill_bytes(&mut nonce);

        let init_data = HandshakeInit {
            id: my_pub.clone(),
            n: nonce.to_vec(),
        };

        let data = minicbor::to_vec(&init_data)?;

        // Pack (No PoW for handshake init usually, or low)
        let diff = Difficulty::default();
        let my_pub_key = AsymCrypt::verifying_key_to_string(&self.keys.verifying_key);
        let mut block = Block::new(0, vec![0; 32], diff, vec![], data, my_pub_key);
        block.mine();

        let packed = Packager::pack(&self.keys.signing_key, &block, None, Some(CMD_HANDSHAKE_INIT as u16), false)
            .await
            .map_err(|e| anyhow::anyhow!(e))?;

        // Send
        let response = self.send_bytes(&packed).await?;

        if let Some(resp_bytes) = response {
            // Unpack response
            let unpacked = Packager::unpack(&resp_bytes, false).map_err(|e| anyhow::anyhow!(e))?;
            if unpacked.data.cmd == Some(CMD_HANDSHAKE_RESP as u16) {
                // Return Cipher (None for now) and Relay ID (Sender)
                return Ok((None, Some(unpacked.data.pub_key)));
            }
        }

        Ok((None, None))
    }

    // Helper to get route and build block
    fn prepare_routed_block(&self, target: &str, data: Vec<u8>, diff: Difficulty) -> Result<(Block, Option<String>)> {
        // Determine Route
        let relay_id_opt = self.relay_id.read().unwrap().clone();
        tracing::debug!("DEBUG: prepare_routed_block: relay_id_opt={:?}, target={}", relay_id_opt, target);

        let (route, used_circuit_id) = if let Some(relay_id) = relay_id_opt {

            let mut chosen_circuit_id = None;
            let circuits = self.circuit_manager.get_active_circuits();
            tracing::debug!("DEBUG: Active Circuits: {}", circuits.len());
            {
                let mut candidates = Vec::new();
                for c in circuits {
                    // Circuit path is [LocalClient, Relay1, Relay2, ...]
                    // We need to check if the first relay (second node) matches our connected relay
                    if let Some(first_relay) = c.path.get(1) {
                        if first_relay.id == relay_id {
                            candidates.push(c.id.clone());
                        }
                    }
                }

                if !candidates.is_empty() {
                    use rand::seq::SliceRandom;
                    chosen_circuit_id = candidates.choose(&mut OsRng).cloned();
                }
            }
            tracing::debug!("DEBUG: chosen_circuit_id: {:?}", chosen_circuit_id);
            if let Some(cid) = chosen_circuit_id.clone() {
                // Use established circuit
                if let Some(path) = self.circuit_manager.get_circuit(&cid) {
                    self.circuit_manager.record_usage(&cid);
                    // Append Target
                    // Path: [R1, R2] -> [Source, R1, R2, Target]
                    let mut full_path = vec![relay_lib::dht::dht::Node::new("source".to_string(), "0.0.0.0".to_string(), 0, 0)];
                    full_path.extend(path.clone());
                    full_path.push(relay_lib::dht::dht::Node::new(target.to_string(), "0.0.0.0".to_string(), 0, 0));

                    tracing::debug!("DEBUG: Building circuit route len {}", full_path.len());
                    // build_onion_route now expects minicbor internal usage if checking Block structure, 
                    // but CircuitManager.build_onion_route returns Vec<Vec<u8>> (keys).
                    // CircuitManager uses encryption. We should verify it doesn't use serde_cbor internally for the headers?
                    // CircuitManager is in relay-lib. I haven't checked it yet. Assuming it handles bytes.
                    (self.circuit_manager.build_onion_route(&full_path, Some(cid.0.as_bytes())).unwrap_or_default(), Some(cid))
                } else { (Vec::new(), None) }
            } else {
                if target == relay_id {
                    (Vec::new(), None)
                } else {
                    // Routing to Peer via Relay
                    // Path: [Source, Relay, Target]
                    let my_id = AsymCrypt::verifying_key_to_string(&self.keys.verifying_key);
                    let path = vec![
                        relay_lib::dht::dht::Node::new(my_id, "0.0.0.0".to_string(), 0, 0),
                        relay_lib::dht::dht::Node::new(relay_id.clone(), "0.0.0.0".to_string(), 0, 1),
                        relay_lib::dht::dht::Node::new(target.to_string(), "0.0.0.0".to_string(), 0, 0)
                    ];
                    tracing::debug!("DEBUG: Building 2-hop route (1 hop active): {:?}", path.iter().map(|n| &n.id).collect::<Vec<_>>());

                    // Register as circuit (deduplicated by manager)
                    let cid = self.circuit_manager.add_circuit(path.clone());
                    self.circuit_manager.record_usage(&cid);

                    (self.circuit_manager.build_onion_route(&path, Some(cid.0.as_bytes())).unwrap_or_default(), Some(cid))
                }
            }
        } else {
            (Vec::new(), None)
        };

        let my_pub_key = AsymCrypt::verifying_key_to_string(&self.keys.verifying_key);

        Ok((Block::new(0, vec![0; 32], diff, route, data, my_pub_key), used_circuit_id.map(|c| c.0)))
    }

    pub async fn build_message_block(&self, target: &str, msg: &ChatMessage, ack_requested: bool) -> Result<Block> {
        // Use minicbor to encode the message (NO JSON!)
        let payload_bytes = minicbor::to_vec(msg)?;

        #[derive(minicbor::Encode)]
        struct Payload {
            #[n(0)]
            #[cbor(with = "minicbor::bytes")] msg: Option<Vec<u8>>, // Encrypted bytes
            #[n(1)]
            #[cbor(with = "minicbor::bytes")] txt: Option<Vec<u8>>, // Plain/Enc bytes
            #[n(2)] rack: Option<bool>,
        }

        let (data_to_send, _is_encrypted) = {
            // Get or compute cached AES key for recipient
            let aes_key = if let Some(cached) = self.recipient_aes_cache.get(target) {
                *cached
            } else {
                // Need to derive: first get/compute X25519 public key
                let recipient_x_pub = if let Some(cached) = self.recipient_x25519_cache.get(target) {
                    cached.clone()
                } else {
                    match AsymCrypt::verifying_key_from_string(target) {
                        Ok(target_vk) => {
                            match AsymCrypt::ed_pub_to_x25519(&target_vk) {
                                Ok(x_pub) => {
                                    self.recipient_x25519_cache.insert(target.to_string(), x_pub.clone());
                                    x_pub
                                }
                                Err(_) => {
                                    let p = Payload { msg: None, txt: Some(payload_bytes.clone()), rack: if ack_requested { Some(true) } else { None } };
                                    return Ok(self.prepare_routed_block(target, minicbor::to_vec(&p)?, self.current_difficulty.read().unwrap().clone())?.0);
                                }
                            }
                        }
                        Err(_) => {
                            let p = Payload { msg: None, txt: Some(payload_bytes.clone()), rack: if ack_requested { Some(true) } else { None } };
                            return Ok(self.prepare_routed_block(target, minicbor::to_vec(&p)?, self.current_difficulty.read().unwrap().clone())?.0);
                        }
                    }
                };

                // Derive AES key from ECDH + HKDF (ONCE per recipient)
                let key = AsymCrypt::derive_aes_key(&self.session_ephemeral_key, &recipient_x_pub);
                self.recipient_aes_cache.insert(target.to_string(), key);
                key
            };

            // Encrypt using cached AES key and cached ephemeral public key
            match AsymCrypt::encrypt_with_aes(&aes_key, &self.session_ephemeral_pub, &payload_bytes) {
                Ok(ct) => {
                    let p = Payload { msg: Some(ct), txt: None, rack: if ack_requested { Some(true) } else { None } };
                    (minicbor::to_vec(&p)?, true)
                }
                Err(_) => {
                    let p = Payload { msg: None, txt: Some(payload_bytes.clone()), rack: if ack_requested { Some(true) } else { None } };
                    (minicbor::to_vec(&p)?, false)
                }
            }
        };

        let diff = self.current_difficulty.read().unwrap().clone();
        let (mut block, _) = self.prepare_routed_block(target, data_to_send, diff)?;
        tracing::debug!("Mining block for delivery to {} (diff: {:?})", target, block.diff);
        block.mine();
        tracing::debug!("Mining complete.");
        
        Ok(block)
    }

    pub async fn send_block(&self, block: &Block, target: Option<&str>) -> Result<()> {
        let packed = Packager::pack(&self.keys.signing_key, block, target, None, false)
            .await
            .map_err(|e| anyhow::anyhow!(e))?;

        self.send_bytes(&packed).await?;
        Ok(())
    }

    pub async fn send_message(&self, target: &str, msg: &ChatMessage, ack_requested: bool) -> Result<Option<String>> {
        let block = self.build_message_block(target, msg, ack_requested).await?;
        self.send_block(&block, Some(target)).await?;
        Ok(None) 
    }


    pub async fn send_ack(&self, target: &str, msg_id: &str) -> Result<()> {
        let diff = self.current_difficulty.read().unwrap().clone();

        #[derive(minicbor::Encode)]
        struct AckPayload {
            #[n(1)]
            #[cbor(with = "minicbor::bytes")] txt: Vec<u8>,
            #[n(3)] ack: String,
        }

        // 1. Prepare Payload
        let payload = AckPayload {
            txt: "ACK".as_bytes().to_vec(),
            ack: msg_id.to_string(),
        };
        let payload_bytes = minicbor::to_vec(&payload)?;

        // 2. Encryption using cached AES keys
        let (final_data, _enc) = {
            // Get or compute cached AES key for recipient
            let aes_key = if let Some(cached) = self.recipient_aes_cache.get(target) {
                Some(*cached)
            } else {
                // Need to derive: first get/compute X25519 public key
                let recipient_x_pub = if let Some(cached) = self.recipient_x25519_cache.get(target) {
                    Some(cached.clone())
                } else {
                    match AsymCrypt::verifying_key_from_string(target) {
                        Ok(target_vk) => {
                            match AsymCrypt::ed_pub_to_x25519(&target_vk) {
                                Ok(x_pub) => {
                                    self.recipient_x25519_cache.insert(target.to_string(), x_pub.clone());
                                    Some(x_pub)
                                }
                                Err(_) => None,
                            }
                        }
                        Err(_) => None,
                    }
                };

                if let Some(x_pub) = recipient_x_pub {
                    let key = AsymCrypt::derive_aes_key(&self.session_ephemeral_key, &x_pub);
                    self.recipient_aes_cache.insert(target.to_string(), key);
                    Some(key)
                } else {
                    None
                }
            };

            if let Some(key) = aes_key {
                match AsymCrypt::encrypt_with_aes(&key, &self.session_ephemeral_pub, &payload_bytes) {
                    Ok(ct) => (ct, true),
                    Err(_) => (payload_bytes, false),
                }
            } else {
                (payload_bytes, false)
            }
        };

        // Note: The structure of AckPayload might not match typical MessagePayload indices if we want consistency.
        // But Ack is special.
        // Actually, receiver checks keys. If we use integer keys, we should ideally use a unified enum or struct.
        // But separate structs with distinct keys also works if receiver is flexible or uses Option fields.
        
        let (mut block, _) = self.prepare_routed_block(target, final_data, diff)?;
        block.mine();

        let packed = Packager::pack(&self.keys.signing_key, &block, Some(target), None, false)
            .await
            .map_err(|e| anyhow::anyhow!(e))?;
        self.send_bytes(&packed).await?;
        Ok(())
    }


    pub async fn send_raw(&self, target: &str, data: Vec<u8>) -> Result<()> {
        let diff = self.current_difficulty.read().unwrap().clone();

        let (mut block, _) = self.prepare_routed_block(target, data, diff)?;
        block.mine();

        let packed = Packager::pack(&self.keys.signing_key, &block, Some(target), None, false)
            .await
            .map_err(|e| anyhow::anyhow!(e))?;
        self.send_bytes(&packed).await?;
        Ok(())
    }

    /// Fire-and-forget send for media streaming - doesn't wait for ack
    pub async fn send_raw_oneshot(&self, target: &str, data: Vec<u8>) -> Result<()> {
        let diff = self.current_difficulty.read().unwrap().clone();

        let (mut block, _) = self.prepare_routed_block(target, data, diff)?;
        block.mine();

        let packed = Packager::pack(&self.keys.signing_key, &block, Some(target), None, false)
            .await
            .map_err(|e| anyhow::anyhow!(e))?;
        self.send_bytes_oneshot(&packed).await?;
        Ok(())
    }

    pub fn public_key(&self) -> VerifyingKey {
        self.keys.verifying_key
    }

    pub fn update_difficulty(&self, diff: Difficulty) {
        *self.current_difficulty.write().unwrap() = diff;
    }

    pub fn decrypt_session_message(&self, _sender: &str, ciphertext: Vec<u8>) -> Result<String> {
        if let Some(cipher) = &self.session_cipher {
            let pt = cipher.decrypt(&ciphertext).map_err(|e| anyhow::anyhow!(e))?;
            Ok(String::from_utf8(pt)?)
        } else {
            Err(anyhow::anyhow!("No session cipher"))
        }
    }

    pub async fn announce_identity(&self) -> Result<()> {
        // Just handshake is enough for now
        Ok(())
    }

    pub async fn send_ping(&self) -> Result<()> {
        let now = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_millis() as u64;
        let now_bytes = now.to_be_bytes().to_vec();

        let diff = self.current_difficulty.read().unwrap().clone();
        let my_pub_key = AsymCrypt::verifying_key_to_string(&self.keys.verifying_key);
        let mut block = Block::new(0, vec![0; 32], diff, vec![], now_bytes, my_pub_key);
        block.mine();

        let packed = Packager::pack(&self.keys.signing_key, &block, None, Some(CMD_PING as u16), false)
            .await
            .map_err(|e| anyhow::anyhow!(e))?;

        self.pending_pings.insert(now, std::time::Instant::now());

        self.send_bytes(&packed).await?;
        Ok(())
    }

    async fn send_bytes(&self, data: &[u8]) -> Result<Option<Vec<u8>>> {
        let client = &self.client;
        tracing::debug!("Opening stream to relay...");
        // Open Bi-stream
        let (mut send, mut recv) = client.open_bi().await?;

        // Write Data
        tracing::debug!("Writing {} bytes to stream...", data.len());
        send.write_all(data).await?;
        send.finish()?;

        // Read Response (With Timeout)
        tracing::debug!("Awaiting response from relay...");
        use tokio::time::{timeout, Duration};
        let response_res = timeout(Duration::from_secs(5), recv.read_to_end(10 * 1024 * 1024)).await;

        match response_res {
            Ok(Ok(buf)) => {
                if buf.is_empty() {
                    tracing::debug!("Received empty response (OK/Ack)");
                    Ok(None)
                } else {
                    tracing::debug!("Received {} bytes response", buf.len());
                    Ok(Some(buf))
                }
            }
            Ok(Err(e)) => {
                tracing::warn!("Stream read error: {}", e);
                Err(anyhow::anyhow!("Stream read error: {}", e))
            }
            Err(_) => {
                tracing::warn!("Stream read TIMEOUT (5s)");
                Ok(None) // Treat timeout as success if it was just a one-way message, OR fail?
                // Actually if it's a routed message, relay might not respond.
                // But for now, returning None is safer than hanging.
            }
        }
    }

    pub fn signing_key(&self) -> &SigningKey {
        &self.keys.signing_key
    }

    /// Fire-and-forget send - writes data and immediately returns without waiting for response
    async fn send_bytes_oneshot(&self, data: &[u8]) -> Result<()> {
        let client = &self.client;
        // Open Uni-directional stream (send only, no receive)
        let mut send = client.open_uni().await?;
        send.write_all(data).await?;
        send.finish()?;
        Ok(())
    }
}
