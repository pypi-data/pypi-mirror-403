use crate::crypto::asymmetric::{AsymCrypt, SigningKeyPair, EncryptionKeyPair};

pub struct KeyManager;

impl KeyManager {
    pub fn generate_signing_key_pair() -> SigningKeyPair {
        AsymCrypt::generate_key_pair_signing()
    }

    pub fn generate_encryption_key_pair() -> EncryptionKeyPair {
        AsymCrypt::generate_key_pair_encryption()
    }
}

