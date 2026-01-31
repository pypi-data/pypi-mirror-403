use crate::consensus::network::{AES_FRAME_SIZE, DEFAULT_AES_GCM_NONCE_SIZE, DEFAULT_AES_GCM_TAG_SIZE, DEFAULT_AES_SALT};
use aes_gcm::{aead::Aead as AesAead, Aes256Gcm, KeyInit as AesKeyInit};
use argon2::{Algorithm, Argon2, Params, Version};
use chacha20poly1305::ChaCha20Poly1305;
use generic_array::typenum::U12;
use generic_array::GenericArray;
use rand::rngs::OsRng;
use rand::RngCore;
// Trait for fill_bytes
use std::sync::Arc;

pub trait SymmetricCipher: Send + Sync {
    fn encrypt(&self, plaintext: &[u8]) -> Vec<u8>;
    fn decrypt(&self, ciphertext: &[u8]) -> Result<Vec<u8>, String>;
}

#[derive(Clone, Debug)]
pub struct AESCipher {
    key: Arc<[u8; 32]>,
    salt: [u8; 8],
}

impl AESCipher {
    pub fn new(password: &[u8], key_size: usize, salt: Option<&[u8]>) -> Self {
        let salt_bytes = salt.unwrap_or(DEFAULT_AES_SALT);
        let salt_array = {
            let mut s = [0u8; 8];
            s.copy_from_slice(&salt_bytes[..8.min(salt_bytes.len())]);
            s
        };
        
        let params = Params::new(8, 1, 1, Some(key_size / 8)).unwrap();
        let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);
        let mut key = [0u8; 32];
        argon2.hash_password_into(password, &salt_array, &mut key).unwrap();
        
        AESCipher {
            key: Arc::new(key),
            salt: salt_array,
        }
    }

    pub fn new_from_key(key: [u8; 32]) -> Self {
        AESCipher {
            key: Arc::new(key),
            salt: [0u8; 8],
        }
    }

    fn encrypt_chunk(&self, chunk: &[u8]) -> Vec<u8> {
        let cipher = Aes256Gcm::new_from_slice(&self.key[..32]).expect("Failed to create AES cipher");
        let mut nonce_bytes = [0u8; DEFAULT_AES_GCM_NONCE_SIZE];
        OsRng.fill_bytes(&mut nonce_bytes);
        let nonce = GenericArray::<u8, U12>::from_slice(&nonce_bytes);
        
        let ciphertext = cipher.encrypt(nonce, chunk).expect("Failed to encrypt");
        
        let mut result = Vec::with_capacity(AES_FRAME_SIZE + DEFAULT_AES_GCM_NONCE_SIZE + ciphertext.len());
        result.extend_from_slice(&(ciphertext.len() as u32).to_be_bytes());
        result.extend_from_slice(&nonce_bytes);
        result.extend_from_slice(&ciphertext);
        result
    }

    fn decrypt_chunk(&self, chunk: &[u8]) -> Result<Vec<u8>, String> {
        if chunk.len() < AES_FRAME_SIZE + DEFAULT_AES_GCM_NONCE_SIZE + 1 {
            return Err("Ciphertext too short".to_string());
        }
        
        let ct_len = u32::from_be_bytes(chunk[0..4].try_into().unwrap()) as usize;
        if chunk.len() != AES_FRAME_SIZE + DEFAULT_AES_GCM_NONCE_SIZE + ct_len || ct_len < 1 {
            return Err("Framed chunk length mismatch".to_string());
        }
        
        let nonce_bytes: [u8; DEFAULT_AES_GCM_NONCE_SIZE] = chunk[AES_FRAME_SIZE..AES_FRAME_SIZE + DEFAULT_AES_GCM_NONCE_SIZE].try_into().map_err(|_| "Invalid nonce length")?;
        let ciphertext = &chunk[AES_FRAME_SIZE + DEFAULT_AES_GCM_NONCE_SIZE..];
        
        let cipher = Aes256Gcm::new_from_slice(&self.key[..32]).map_err(|e| format!("Cipher init failed: {}", e))?;
        let nonce = GenericArray::<u8, U12>::from_slice(&nonce_bytes);
        
        cipher.decrypt(nonce, ciphertext).map_err(|e| format!("Decryption failed: {}", e))
    }
}

impl SymmetricCipher for AESCipher {
    fn encrypt(&self, plaintext: &[u8]) -> Vec<u8> {
        const CHUNK_SIZE: usize = 1024 * 1024;
        if plaintext.len() <= CHUNK_SIZE {
            let chunk_ct = self.encrypt_chunk(plaintext);
            let mut result = Vec::with_capacity(self.salt.len() + chunk_ct.len());
            result.extend_from_slice(&self.salt);
            result.extend_from_slice(&chunk_ct);
            return result;
        }
        
        let chunks: Vec<_> = plaintext.chunks(CHUNK_SIZE).collect();
        let mut result = Vec::with_capacity(plaintext.len() + chunks.len() * (AES_FRAME_SIZE + DEFAULT_AES_GCM_NONCE_SIZE + DEFAULT_AES_GCM_TAG_SIZE));
        result.extend_from_slice(&self.salt);
        
        for chunk in chunks {
            result.extend_from_slice(&self.encrypt_chunk(chunk));
        }
        result
    }

    fn decrypt(&self, ciphertext: &[u8]) -> Result<Vec<u8>, String> {
        if ciphertext.len() < 8 {
            return Err("Ciphertext too short".to_string());
        }
        
        let _salt = &ciphertext[..8];
        let encrypted_data = &ciphertext[8..];
        
        const CHUNK_SIZE: usize = 1024 * 1024 + DEFAULT_AES_GCM_NONCE_SIZE + DEFAULT_AES_GCM_TAG_SIZE;
        
        if encrypted_data.len() <= CHUNK_SIZE {
            return self.decrypt_chunk(encrypted_data);
        }
        
        let mut result = Vec::new();
        let mut i = 0;
        while i < encrypted_data.len() {
            if i + AES_FRAME_SIZE + DEFAULT_AES_GCM_NONCE_SIZE > encrypted_data.len() {
                return Err("Truncated chunk header".to_string());
            }
            let ct_len = u32::from_be_bytes(encrypted_data[i..i+4].try_into().unwrap()) as usize;
            if ct_len < 1 {
                return Err("Invalid ciphertext length".to_string());
            }
            let frame_len = AES_FRAME_SIZE + DEFAULT_AES_GCM_NONCE_SIZE + ct_len;
            if i + frame_len > encrypted_data.len() {
                return Err("Truncated chunk data".to_string());
            }
            let chunk = &encrypted_data[i..i+frame_len];
            result.extend_from_slice(&self.decrypt_chunk(chunk)?);
            i += frame_len;
        }
        Ok(result)
    }
}

#[derive(Clone, Debug)]
pub struct ChaChaCipher {
    key: Arc<[u8; 32]>,
    salt: [u8; 12],
}

impl ChaChaCipher {
    pub fn new(password: &[u8], key_size: usize, salt: Option<&[u8]>) -> Self {
        let salt_bytes = if let Some(s) = salt {
            let mut s_arr = [0u8; 12];
            s_arr[..s.len().min(12)].copy_from_slice(&s[..s.len().min(12)]);
            s_arr
        } else {
            let mut s = [0u8; 12];
            OsRng.fill_bytes(&mut s);
            s
        };
        
        let params = Params::new(8, 1, 1, Some(key_size / 8)).unwrap();
        let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);
        let mut key = [0u8; 32];
        argon2.hash_password_into(password, &salt_bytes, &mut key).unwrap();
        
        ChaChaCipher {
            key: Arc::new(key),
            salt: salt_bytes,
        }
    }

    fn encrypt_chunk(&self, chunk: &[u8], nonce: &[u8; 12]) -> Vec<u8> {
        let cipher = ChaCha20Poly1305::new_from_slice(&self.key[..32]).expect("Failed to create ChaCha cipher");
        let nonce_obj = GenericArray::<u8, U12>::from_slice(nonce);
        let ciphertext = cipher.encrypt(nonce_obj, chunk).expect("Failed to encrypt");
        
        let mut result = Vec::with_capacity(12 + 16 + ciphertext.len());
        result.extend_from_slice(nonce);
        result.extend_from_slice(&ciphertext[..16]);
        result.extend_from_slice(&ciphertext[16..]);
        result
    }

    fn decrypt_chunk(&self, chunk: &[u8]) -> Result<Vec<u8>, String> {
        if chunk.len() < 12 + 16 {
            return Err("Ciphertext too short".to_string());
        }
        
        let nonce = &chunk[..12];
        let tag = &chunk[12..28];
        let encrypted_data = &chunk[28..];
        
        let cipher = ChaCha20Poly1305::new_from_slice(&self.key[..32]).map_err(|e| format!("Cipher init failed: {}", e))?;
        let nonce_obj = GenericArray::<u8, U12>::from_slice(nonce);
        
        let mut full_ciphertext = Vec::with_capacity(tag.len() + encrypted_data.len());
        full_ciphertext.extend_from_slice(tag);
        full_ciphertext.extend_from_slice(encrypted_data);
        
        cipher.decrypt(nonce_obj, full_ciphertext.as_ref()).map_err(|e| format!("Decryption failed: {}", e))
    }
}

impl SymmetricCipher for ChaChaCipher {
    fn encrypt(&self, plaintext: &[u8]) -> Vec<u8> {
        const CHUNK_SIZE: usize = 1024 * 1024;
        if plaintext.len() <= CHUNK_SIZE {
            let mut nonce = [0u8; 12];
            OsRng.fill_bytes(&mut nonce);
            let mut result = Vec::with_capacity(12 + self.salt.len() + plaintext.len() + 16);
            result.extend_from_slice(&self.salt);
            result.extend_from_slice(&self.encrypt_chunk(plaintext, &nonce));
            return result;
        }
        
        let chunks: Vec<_> = plaintext.chunks(CHUNK_SIZE).collect();
        let mut result = Vec::with_capacity(12 + plaintext.len() + chunks.len() * 28);
        result.extend_from_slice(&self.salt);
        
        for chunk in chunks {
            let mut nonce = [0u8; 12];
            OsRng.fill_bytes(&mut nonce);
            result.extend_from_slice(&self.encrypt_chunk(chunk, &nonce));
        }
        result
    }

    fn decrypt(&self, ciphertext: &[u8]) -> Result<Vec<u8>, String> {
        if ciphertext.len() < 12 {
            return Err("Ciphertext too short".to_string());
        }
        
        let _salt = &ciphertext[..12];
        let encrypted_data = &ciphertext[12..];
        
        const CHUNK_SIZE: usize = 1024 * 1024 + 12 + 16;
        
        if encrypted_data.len() <= CHUNK_SIZE {
            return self.decrypt_chunk(encrypted_data);
        }
        
        let mut result = Vec::new();
        let mut i = 0;
        while i < encrypted_data.len() {
            if i + 12 + 16 > encrypted_data.len() {
                return Err("Truncated chunk".to_string());
            }
            let chunk_size = (CHUNK_SIZE).min(encrypted_data.len() - i);
            let chunk = &encrypted_data[i..i+chunk_size];
            result.extend_from_slice(&self.decrypt_chunk(chunk)?);
            i += chunk_size;
        }
        Ok(result)
    }
}

