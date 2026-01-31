use crate::block::hash_type::{MemoryHash, ShaHash};
use crate::consensus::blockchain::*;
use crate::pow::computation::{compute_argon2_pow, compute_sha256_pow};
use crate::pow::difficulty::Difficulty;
use dashmap::DashMap;
use std::io::Write;
use std::sync::Arc;

pub trait BlockHash: Send + Sync {
    fn value(&self) -> &[u8];
    fn value_as_int(&self) -> u64;
    fn diff(&self) -> &Difficulty;
}

#[derive(Clone)]
pub struct Block {
    pub index: u64,
    pub previous_hash: Vec<u8>,
    pub diff: Difficulty,
    pub route: Vec<Vec<u8>>, // Onion routing headers
    pub data: Vec<u8>,
    pub pub_key: String,      // Base64 sender public key
    pub timestamp: i64,
    pub nonce: Option<u32>,
    pub signature: Option<Vec<u8>>,
    pub hash: Option<Arc<dyn BlockHash>>,
}


impl Block {
    pub fn new(
        index: u64,
        prev_hash: Vec<u8>,
        difficulty: Difficulty,
        route: Vec<Vec<u8>>,
        data: Vec<u8>,
        pub_key: String,
    ) -> Self {
        Block {
            index,
            previous_hash: prev_hash,
            route,
            data,
            pub_key,
            diff: difficulty,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos() as i64,
            nonce: Some(0),
            signature: None,
            hash: None,
        }
    }

    pub fn compute_hash(&mut self) -> Arc<dyn BlockHash> {
        let mut buffer = Vec::new();
        buffer.write_all(&self.index.to_le_bytes()[..INDEX_SIZE.min(8)]).unwrap();
        buffer.write_all(&self.diff.to_bytes()).unwrap();
        buffer.write_all(&self.previous_hash).unwrap();
        // Python uses struct.pack('d', timestamp) which packs as f64 (double)
        let timestamp_f64 = self.timestamp as f64;
        buffer.write_all(&timestamp_f64.to_le_bytes()).unwrap();

        // Include route in hash
        // Exclude route from hash to support onion peeling without re-mining
        // for r in &self.route {
        //    buffer.write_all(r).unwrap();
        // }

        buffer.write_all(&self.data).unwrap();
        buffer.write_all(self.pub_key.as_bytes()).unwrap();

        let hash: Arc<dyn BlockHash> = if self.diff.express == 0 {
            Arc::new(MemoryHash::new(self.diff, &buffer))
        } else {
            Arc::new(ShaHash::new(self.diff, &buffer))
        };
        
        self.hash = Some(hash.clone());
        hash
    }

    pub fn mine(&mut self) {
        use tracing::debug;
        debug!("[BLOCK] Starting mining for block #{} (n_bits={}, express={}, hash_len_chars={})", 
            self.index, self.diff.n_bits, self.diff.express, self.diff.hash_len_chars);
        let hash = self.compute_hash();
        let target_bits = (self.diff.hash_len_chars as usize * 8) - self.diff.n_bits as usize;
        debug!("[BLOCK] Target bits: {}", target_bits);
        let mut nonce = 0u64;
        let mut iterations = 0u64;
        loop {
            let computed_nonce = if self.diff.express == 0 {
                compute_argon2_pow(self.diff.n_bits, hash.as_ref(), nonce)
            } else {
                compute_sha256_pow(self.diff.n_bits, hash.as_ref(), nonce)
            };
            iterations += 1;
            if iterations == 1 || iterations % 1000 == 0 {
                debug!("[BLOCK] Mining block #{}: iteration {}, nonce {} -> computed {}", 
                    self.index, iterations, nonce, computed_nonce);
            }
            if computed_nonce == nonce {
                debug!("[BLOCK] Mining completed for block #{}: nonce {} after {} iterations", self.index, nonce, iterations);
                break;
            }
            nonce = computed_nonce;
        }
        self.nonce = Some(nonce as u32);
    }

    pub fn verify_pow(&self) -> bool {
        if self.hash.is_none() || self.nonce.is_none() {
            return false;
        }
        let hash = self.hash.as_ref().unwrap();
        let nonce = self.nonce.unwrap() as u64;

        // Note: We need to use the hash bytes directly.
        // compute_argon2_pow takes &dyn BlockHash, but internally calls value().
        // Here we have Arc<dyn BlockHash>.

        let computed_nonce = if self.diff.express == 0 {
            compute_argon2_pow(self.diff.n_bits, hash.as_ref(), nonce)
        } else {
            compute_sha256_pow(self.diff.n_bits, hash.as_ref(), nonce)
        };

        computed_nonce == nonce
    }

    /// Serialize block to wire format:
    /// [3B: header_len (LE u24)][CBOR: WireHeader][CBOR: WirePayload]
    pub async fn to_bytes(&self) -> Result<Vec<u8>, String> {
        #[derive(minicbor::Encode)]
        struct WireHeader<'a> {
            #[n(0)] route: &'a [Vec<u8>],
            #[n(1)] pub_key: &'a str,
            #[n(2)] verify_data: Option<&'a [u8]>,
        }

        #[derive(minicbor::Encode)]
        struct WirePayload<'a> {
            #[n(0)] index: u64,
            #[n(1)] diff: Vec<u8>,
            #[n(2)] prev_hash: &'a [u8],
            #[n(3)] nonce: u32,
            #[n(4)] timestamp: i64,
            #[n(5)] data: &'a [u8],
            #[n(6)] signature: Option<&'a [u8]>,
        }

        let verify_data = if !self.data.is_empty() { Some(self.data.as_slice()) } else { None };
        let header = WireHeader {
            route: &self.route,
            pub_key: &self.pub_key,
            verify_data,
        };

        let header_bytes = minicbor::to_vec(&header).map_err(|e| format!("CBOR header error: {}", e))?;

        let payload = WirePayload {
            index: self.index,
            diff: self.diff.to_bytes(),
            prev_hash: &self.previous_hash,
            nonce: self.nonce.unwrap_or(0),
            timestamp: self.timestamp,
            data: &self.data,
            signature: self.signature.as_deref(),
        };

        let payload_bytes = minicbor::to_vec(&payload).map_err(|e| format!("CBOR payload error: {}", e))?;

        // Combine: [3B header_len][header][payload]
        let header_len = header_bytes.len();
        if header_len > 0xFFFFFF {
            return Err("Header too large for 3-byte length".to_string());
        }

        let mut result = Vec::with_capacity(3 + header_len + payload_bytes.len());
        result.push((header_len & 0xFF) as u8);
        result.push(((header_len >> 8) & 0xFF) as u8);
        result.push(((header_len >> 16) & 0xFF) as u8);
        result.extend_from_slice(&header_bytes);
        result.extend_from_slice(&payload_bytes);
        
        Ok(result)
    }

    /// Deserialize block from wire format:
    /// [3B: header_len (LE u24)][CBOR: WireHeader][CBOR: WirePayload]
    pub fn from_bytes(data: &[u8]) -> Result<Self, String> {
        if data.len() < 3 {
            return Err("Data too short for header length".to_string());
        }

        // Parse 3-byte header length
        let header_len = (data[0] as usize)
            | ((data[1] as usize) << 8)
            | ((data[2] as usize) << 16);

        if data.len() < 3 + header_len {
            return Err(format!("Data too short for header: need {}, got {}", 3 + header_len, data.len()));
        }

        #[derive(minicbor::Decode)]
        struct WireHeader {
            #[n(0)] route: Vec<Vec<u8>>,
            #[n(1)] pub_key: String,
            #[n(2
            )] _verify_data: Option<Vec<u8>>, // Ignored during full decode usually, or maybe used?
        }

        // Parse RouteHeader CBOR
        let header_bytes = &data[3..3 + header_len];
        let header: WireHeader = minicbor::decode(header_bytes)
            .map_err(|e| format!("CBOR header parse error: {}", e))?;

        // Parse Payload CBOR
        let payload_bytes = &data[3 + header_len..];

        #[derive(minicbor::Decode)]
        struct WirePayload {
            #[n(0)] index: u64,
            #[n(1)] diff: Vec<u8>,
            #[n(2)] prev_hash: Vec<u8>,
            #[n(3)] nonce: u32,
            #[n(4)] timestamp: i64,
            #[n(5)] data: Vec<u8>,
            #[n(6)] signature: Option<Vec<u8>>,
        }

        let payload: WirePayload = minicbor::decode(payload_bytes)
            .map_err(|e| format!("CBOR payload parse error: {}", e))?;

        let diff = Difficulty::from_bytes(&payload.diff)?;

        Ok(Block {
            index: payload.index,
            previous_hash: payload.prev_hash,
            diff,
            route: header.route,
            data: payload.data,
            pub_key: header.pub_key,
            timestamp: payload.timestamp,
            nonce: Some(payload.nonce),
            signature: payload.signature,
            hash: None,
        })
    }

    /// Zero-copy relay forward: parse header, remove route entry, forward payload verbatim
    /// Returns (new_wire_bytes, next_hop_target, sender_pub_key, verify_data) or error
    ///
    /// This is the fast path for relays - payload bytes are NEVER parsed or copied.
    pub fn relay_forward(
        wire_data: &[u8],
        my_sk: &crate::crypto::asymmetric::SigningKey,
        cache: Option<&DashMap<[u8; 32], [u8; 32]>>,
    ) -> Result<(Vec<u8>, String, String, Option<Vec<u8>>), String> {
        use crate::crypto::asymmetric::AsymCrypt;

        if wire_data.len() < 3 {
            return Err("Data too short".to_string());
        }

        // Parse 3-byte header length
        let header_len = (wire_data[0] as usize)
            | ((wire_data[1] as usize) << 8)
            | ((wire_data[2] as usize) << 16);

        if wire_data.len() < 3 + header_len {
            return Err("Data too short for header".to_string());
        }

        #[derive(minicbor::Decode, minicbor::Encode)]
        struct WireHeader {
            #[n(0)] route: Vec<Vec<u8>>,
            #[n(1)] pub_key: String,
            #[n(2)] verify_data: Option<Vec<u8>>,
        }

        // Parse RouteHeader CBOR ONLY
        let header_bytes = &wire_data[3..3 + header_len];
        let mut header: WireHeader = minicbor::decode(header_bytes)
            .map_err(|e| format!("CBOR header error: {}", e))?;

        // 1. Force Index 0 (First Record Assumption)
        if header.route.is_empty() {
            return Err("Route is empty".to_string());
        }
        let entry = &header.route[0];

        // 2. Decrypt with Caching if available
        let decrypted = if let Some(c) = cache {
            AsymCrypt::decrypt_asymmetric_cached(my_sk, entry, c)
        } else {
            AsymCrypt::decrypt_asymmetric(my_sk, entry)
        };

        if let Ok(decrypted_bytes) = decrypted {
            if decrypted_bytes.len() != 32 {
                return Err("Decrypted hop target invalid length".to_string());
            }
            let next_hop_target = crate::util::base64_utils::bytes_to_base64(&decrypted_bytes);

            // 3. Remove OUR hop (Index 0) so next hop sees their entry at Index 0
            header.route.remove(0);

            // Re-encode Header
            let new_header_bytes = minicbor::to_vec(&header).map_err(|e| format!("CBOR re-encode error: {}", e))?;

            // Get payload bytes VERBATIM
            let payload_bytes = &wire_data[3 + header_len..];

            // Build new wire format
            let new_header_len = new_header_bytes.len();
            let mut result = Vec::with_capacity(3 + new_header_len + payload_bytes.len());
            result.push((new_header_len & 0xFF) as u8);
            result.push(((new_header_len >> 8) & 0xFF) as u8);
            result.push(((new_header_len >> 16) & 0xFF) as u8);
            result.extend_from_slice(&new_header_bytes);
            result.extend_from_slice(payload_bytes);

            Ok((result, next_hop_target, header.pub_key, header.verify_data))
        } else {
            Err("Failed to decrypt first hop (not for us?)".to_string())
        }
    }
}

