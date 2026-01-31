use crate::block::block::{Block, BlockHash};
use crate::pow::difficulty::Difficulty;
use crate::pow::pow_utils::PowUtils;
use crate::util::constants::TIMESTAMP_TOLERANCE;
use std::collections::VecDeque;
use std::sync::Arc;

pub struct Blockchain {
    pub chain: VecDeque<Block>,
    pub difficulty: Difficulty,
    pub version: Vec<u8>,
    pub pub_key_for_encryption: Option<String>,
}

impl Blockchain {
    pub fn new(
        genesis_data: Option<&str>,
        difficulty: Difficulty,
        pub_key_for_encryption: Option<String>,
    ) -> Self {
        let mut chain = VecDeque::new();
        
        if let Some(genesis_msg) = genesis_data {
            let genesis_block = Self::create_genesis(
                genesis_msg.as_bytes(),
                pub_key_for_encryption.as_deref(),
                difficulty,
            ).unwrap();
            chain.push_back(genesis_block);
        }
        
        Blockchain {
            chain,
            difficulty,
            version: vec![0, 0, 166],
            pub_key_for_encryption,
        }
    }

    pub fn create_genesis(
        data: &[u8],
        owned_public_key_for_encryption: Option<&str>,
        difficulty: Difficulty,
    ) -> Result<Block, String> {
        let mut encoder = minicbor::Encoder::new(Vec::new());
        // Map size: data + optional enc_pub_key
        let size = 1 + if owned_public_key_for_encryption.is_some() { 1 } else { 0 };
        encoder.map(size as u64).map_err(|e| e.to_string())?;

        encoder.str("data").map_err(|e| e.to_string())?
            .str(&String::from_utf8_lossy(data)).map_err(|e| e.to_string())?;
        
        if let Some(pub_key) = owned_public_key_for_encryption {
            encoder.str("enc_pub_key").map_err(|e| e.to_string())?
                .str(pub_key).map_err(|e| e.to_string())?;
        }

        let genesis_data = encoder.writer().clone();

        Ok(Block::new(0, b"0".to_vec(), difficulty, vec![], genesis_data, String::new()))
    }

    pub fn get_last(&self) -> &Block {
        self.chain.back().unwrap()
    }

    pub fn len(&self) -> usize {
        self.chain.len()
    }

    pub fn validate_next_block(&self, block: &mut Block) -> bool {
        if block.index != 0 && block.index != self.len() as u64 {
            return false;
        }

        if block.index > 0 {
            let last_hash = self.get_last().hash.as_ref().map(|h: &Arc<dyn BlockHash>| h.value()).unwrap_or(&[]);
            if block.previous_hash != last_hash {
                return false;
            }
        }

        let hash = block.compute_hash();
        let block_z_bits = PowUtils::get_bit_length(hash.as_ref(), block.nonce.unwrap_or(0) as u64, &block.diff);
        // Python uses self.difficulty for target_bits calculation
        // Python: target_bits = self.difficulty.hash_len_chars * 8 - self.difficulty.n_bits
        let target_bits = (self.difficulty.hash_len_chars as usize * 8) - self.difficulty.n_bits as usize;

        if block_z_bits > target_bits {
            return false;
        }

        if block.diff != self.difficulty {
            return false;
        }

        if block.index > 0 {
            let last_timestamp = self.get_last().timestamp;
            if block.timestamp < last_timestamp - TIMESTAMP_TOLERANCE {
                return false;
            }
        }

        true
    }

    pub async fn insert(&mut self, mut block: Block) -> bool {
        if self.validate_next_block(&mut block) {
            self.chain.push_back(block);
            true
        } else {
            false
        }
    }

    pub fn template_next_block(&self, data: Vec<u8>, requested_diff: Option<Difficulty>) -> Block {
        let diff = requested_diff.unwrap_or(self.difficulty);
        let last = self.get_last();
        let prev_hash = last.hash.as_ref().map(|h: &Arc<dyn BlockHash>| h.value().to_vec()).unwrap_or_default();
        Block::new(last.index + 1, prev_hash, diff, vec![], data, String::new())
    }

    pub fn create_handshake_encryption_block_raw(
        &self,
        public_key_received_for_encryption: &str,
        bits: usize,
        algorithm: &str,
        additional_data: &str,
    ) -> Result<(Block, Vec<u8>), String> {
        use crate::crypto::asymmetric::AsymCrypt;
        use crate::util::base64_utils::bytes_to_base64;
        use rand::RngCore;

        let byte_length = bits / 8;
        let mut password = vec![0u8; byte_length];
        rand::thread_rng().fill_bytes(&mut password);
        password.truncate(byte_length);

        let pub_key_bytes = crate::util::base64_utils::base64_to_bytes(public_key_received_for_encryption)
            .map_err(|e| format!("Invalid public key: {}", e))?;
        // Generate ephemeral keypair for encryption
        let ephemeral_priv = crate::crypto::asymmetric::StaticSecret::random_from_rng(&mut rand::rngs::OsRng);
        let ephemeral_pub = crate::crypto::asymmetric::PublicKey::from(&ephemeral_priv);
        let recipient_pub = crate::crypto::asymmetric::PublicKey::from(
            TryInto::<[u8; 32]>::try_into(pub_key_bytes.as_slice()).map_err(|_| "Invalid key length")?
        );
        let aes_key = AsymCrypt::derive_aes_key(&ephemeral_priv, &recipient_pub);
        let encrypted_password_bytes = AsymCrypt::encrypt_with_aes(&aes_key, &ephemeral_pub, &password)?;
        let encrypted_password_b64 = bytes_to_base64(&encrypted_password_bytes);

        // Handshake Data using INTEGER keys to match Beam protocol upgrade
        /*
          cmd: 0
          algo: 1
          bits: 2
          key: 3
          data: 4
        */
        #[derive(minicbor::Encode)]
        struct HandshakePayload<'a> {
            #[n(0)] cmd: u32,
            #[n(1)] algo: &'a str,
            #[n(2)] bits: usize,
            #[n(3)] key: &'a str,
            #[n(4)] data: &'a str,
        }

        let payload = HandshakePayload {
            cmd: 0,
            algo: algorithm,
            bits,
            key: &encrypted_password_b64,
            data: additional_data,
        };

        let handshake_data = minicbor::to_vec(&payload).map_err(|e| e.to_string())?;

        use tracing::debug;
        debug!("[BLOCKCHAIN] Getting last block for handshake");
        let last = self.get_last();
        // Ensure the last block's hash is computed
        let mut last_mut = last.clone();
        last_mut.compute_hash();
        let prev_hash = last_mut.hash.as_ref().map(|h: &Arc<dyn BlockHash>| h.value().to_vec()).unwrap_or_default();
        debug!("[BLOCKCHAIN] Previous hash for handshake: {} bytes, first 8 bytes: {:?}", 
            prev_hash.len(), if prev_hash.len() >= 8 { &prev_hash[..8] } else { &prev_hash[..] });
        debug!("[BLOCKCHAIN] Creating handshake block with index {}", last.index + 1);
        let mut handshake_block = Block::new(last.index + 1, prev_hash, self.difficulty.clone(), vec![], handshake_data, String::new());
        debug!("[BLOCKCHAIN] Starting to mine handshake block (n_bits={}, express={})", self.difficulty.n_bits, self.difficulty.express);
        handshake_block.mine();
        debug!("[BLOCKCHAIN] Handshake block mining completed, nonce={:?}", handshake_block.nonce);
        
        Ok((handshake_block, password))
    }
}

