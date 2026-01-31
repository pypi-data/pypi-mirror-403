use crate::api::packager::Packager;
use crate::block::block::Block;
use crate::blockchain::blockchain::Blockchain;
use crate::crypto::asymmetric::AsymCrypt;
use crate::crypto::symmetric::{AESCipher, ChaChaCipher, SymmetricCipher};
use crate::pow::difficulty::Difficulty;
use crate::transport::quic_client::QuicClient;


pub struct Beam {
    pub conn_bc: Blockchain,
    pub comm_bc: Option<Blockchain>,
    pub encryptor_relay: Option<Box<dyn SymmetricCipher>>,
    pub encryptor_beacon: Option<Box<dyn SymmetricCipher>>,
    pub client: Option<QuicClient>,
    pub pub_key: String,
    pub target_key: String,
    pub connected: bool,
}

impl Beam {
    pub fn new(_pub_key_id: usize, _pub_key_enc_id: usize, target_key: String) -> Self {
        let signing_keypair = AsymCrypt::generate_key_pair_signing();
        let encryption_keypair = AsymCrypt::generate_key_pair_encryption();
        
        let pub_key = AsymCrypt::verifying_key_to_string(&signing_keypair.public);
        let pub_enc_key = AsymCrypt::encryption_key_to_base64(&encryption_keypair.public);
        
        Beam {
            conn_bc: Blockchain::new(None, Difficulty::default(), Some(pub_enc_key)),
            comm_bc: None,
            encryptor_relay: None,
            encryptor_beacon: None,
            client: None,
            pub_key,
            target_key,
            connected: false,
        }
    }

    pub async fn initialize_outgoing_transmission(&mut self) -> Result<bool, String> {
        self.conn_bc = Blockchain::new(
            Some("CONNECTED"),
            Difficulty::default(),
            self.conn_bc.pub_key_for_encryption.clone(),
        );
        
        let genesis_block = self.conn_bc.get_last().clone();
        let response = self.send_block(&genesis_block, true).await?;
        
        if response.is_none() {
            return Err("Empty response".to_string());
        }

        let resp_bytes = response.unwrap();

        #[derive(minicbor::Decode)]
        struct OuterResponse {
            #[n(2)] data: Vec<u8>, // Matches SerializedData index 2 for 'data'
        }

        // Wait, send_block packs via Packager, which uses SerializedData.
        // SerializedData uses integer keys now. 'data' is index 2.

        let outer: OuterResponse = minicbor::decode(&resp_bytes).map_err(|e| format!("Outer decode error: {}", e))?;

        let block = Block::from_bytes(&outer.data)?;
        if !self.conn_bc.insert(block.clone()).await {
            return Err("Invalid handshake block".to_string());
        }

        #[derive(minicbor::Decode)]
        struct HandshakeData {
            #[n(0)] data: String, // "CONNECTED" key mapped to 0? Or should I use "data"?
        }
        // In this upgrade, I assume we use integer key 0 for the generic 'data' string in handshake

        let block_data: HandshakeData = minicbor::decode(&block.data).map_err(|e| format!("Block data decode error: {}", e))?;

        if block_data.data != "CONNECTED" {
            return Err("Connection failed".to_string());
        }
        
        self.connected = true;
        Ok(true)
    }

    pub async fn send_block(&mut self, block: &Block, request_ack: bool) -> Result<Option<Vec<u8>>, String> {
        let signing_keypair = AsymCrypt::generate_key_pair_signing();
        let data = Packager::pack(&signing_keypair.private, block, Some(&self.target_key), None, false).await?;
        
        if let Some(ref mut client) = self.client {
            match client.send_message(&data, request_ack).await {
                Ok(Some(resp_bytes)) => Ok(Some(resp_bytes)),
                Ok(None) => Ok(None),
                Err(e) => Err(e.to_string()),
            }
        } else {
            Err("No client connection".to_string())
        }
    }

    pub async fn process_handshake_block(&mut self, block_data: &[u8]) -> Result<(), String> {
        #[derive(minicbor::Decode)]
        struct HandshakeCmd {
            #[n(0)] cmd: u16,
            #[n(1)] algo: String,
            #[n(2)] bits: usize,
            #[n(3)] key: String,
        }

        // Try decode
        let h: HandshakeCmd = minicbor::decode(block_data).map_err(|e| format!("Handshake decode error: {}", e))?;

        if h.cmd == 0 {
            let encrypted_key = crate::util::base64_utils::base64_to_bytes(&h.key).map_err(|e| e.to_string())?;
            let encryption_keypair = AsymCrypt::generate_key_pair_encryption();
            let my_x_priv = crate::crypto::asymmetric::StaticSecret::from(encryption_keypair.private);
            // Extract sender's ephemeral pub and derive AES key
            let sender_eph = AsymCrypt::extract_sender_ephemeral(&encrypted_key)?;
            let aes_key = AsymCrypt::derive_aes_key(&my_x_priv, &sender_eph);
            let password = AsymCrypt::decrypt_with_aes(&aes_key, &encrypted_key)?;

            let cipher: Box<dyn SymmetricCipher> = if h.algo == "AES" {
                Box::new(AESCipher::new(&password, h.bits, None))
            } else if h.algo == "CC20" {
                Box::new(ChaChaCipher::new(&password, h.bits, None))
            } else {
                return Err(format!("Unknown algorithm: {}", h.algo));
            };

            self.encryptor_relay = Some(cipher);
            Ok(())
        } else {
            Err("Not a handshake block".to_string())
        }
    }
}


