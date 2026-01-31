use crate::util::base64_utils;
use generic_array::GenericArray;
use rand::rngs::OsRng;
use rand::RngCore;
use ring::signature::{Ed25519KeyPair, KeyPair as RingKeyPair};
pub use x25519_dalek::{PublicKey, StaticSecret};

// ============ Ring-based Ed25519 Wrapper Types ============

/// Error type for signature operations
#[derive(Debug, Clone)]
pub struct SignatureError(pub String);

impl std::fmt::Display for SignatureError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl std::error::Error for SignatureError {}

/// Ed25519 signing key with cached public key for performance.
#[derive(Clone)]
pub struct SigningKey {
    seed: [u8; 32],
    cached_pub: [u8; 32],
}

impl SigningKey {
    fn new_with_seed(seed: [u8; 32]) -> Self {
        // Create keypair once and cache public key
        let keypair = Ed25519KeyPair::from_seed_unchecked(&seed).expect("valid seed");
        let pub_bytes: [u8; 32] = keypair.public_key().as_ref().try_into().expect("32 bytes");
        Self { seed, cached_pub: pub_bytes }
    }

    pub fn generate(rng: &mut impl RngCore) -> Self {
        let mut seed = [0u8; 32];
        rng.fill_bytes(&mut seed);
        Self::new_with_seed(seed)
    }

    pub fn from_bytes(bytes: &[u8; 32]) -> Self {
        Self::new_with_seed(*bytes)
    }

    pub fn to_bytes(&self) -> [u8; 32] {
        self.seed
    }

    /// Returns cached verifying key - no computation needed.
    pub fn verifying_key(&self) -> VerifyingKey {
        VerifyingKey { bytes: self.cached_pub }
    }

    pub fn sign(&self, message: &[u8]) -> Signature {
        // Recreate keypair from seed for signing
        let keypair = Ed25519KeyPair::from_seed_unchecked(&self.seed).expect("valid seed");
        let sig = keypair.sign(message);
        let sig_bytes: [u8; 64] = sig.as_ref().try_into().expect("64 bytes");
        Signature { bytes: sig_bytes }
    }
}

impl std::fmt::Debug for SigningKey {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "[REDACTED]")
    }
}

/// Ed25519 verifying key (public key)
#[derive(Clone, Copy, PartialEq, Eq)]
pub struct VerifyingKey {
    bytes: [u8; 32],
}

impl VerifyingKey {
    pub fn from_bytes(bytes: &[u8; 32]) -> Result<Self, SignatureError> {
        Ok(Self { bytes: *bytes })
    }

    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.bytes
    }

    pub fn to_bytes(&self) -> [u8; 32] {
        self.bytes
    }

    pub fn verify(&self, message: &[u8], signature: &Signature) -> Result<(), SignatureError> {
        use ring::signature::UnparsedPublicKey;
        let public_key = UnparsedPublicKey::new(&ring::signature::ED25519, &self.bytes);
        public_key.verify(message, &signature.bytes)
            .map_err(|_| SignatureError("Signature verification failed".to_string()))
    }
}

impl std::fmt::Debug for VerifyingKey {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "VerifyingKey({:?})", base64_utils::bytes_to_base64(&self.bytes))
    }
}

/// Ed25519 signature
#[derive(Clone, Copy)]
pub struct Signature {
    bytes: [u8; 64],
}

impl Signature {
    pub fn from_bytes(bytes: &[u8; 64]) -> Self {
        Self { bytes: *bytes }
    }

    pub fn to_bytes(&self) -> [u8; 64] {
        self.bytes
    }
}

impl AsRef<[u8]> for Signature {
    fn as_ref(&self) -> &[u8] {
        &self.bytes
    }
}

// ============ Existing Types ============

#[derive(Clone)]
pub struct SecretWrapper(pub StaticSecret);

impl std::fmt::Debug for SecretWrapper {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "[REDACTED]")
    }
}

impl std::ops::Deref for SecretWrapper {
    type Target = StaticSecret;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

#[derive(Debug, Clone)]
pub struct SigningKeyPair {
    pub private: SigningKey,
    pub public: VerifyingKey,
}

#[derive(Debug, Clone)]
pub struct EncryptionKeyPair {
    pub private: [u8; 32],
    pub public: [u8; 32],
}

pub struct AsymCrypt;

impl AsymCrypt {
    pub fn generate_key_pair_encryption() -> EncryptionKeyPair {
        let private = StaticSecret::random_from_rng(&mut OsRng);
        let public = PublicKey::from(&private);
        EncryptionKeyPair {
            private: private.to_bytes(),
            public: *public.as_bytes(),
        }
    }

    pub fn generate_key_pair_signing() -> SigningKeyPair {
        let signing_key = SigningKey::generate(&mut OsRng);
        let verifying_key = signing_key.verifying_key();
        SigningKeyPair {
            private: signing_key,
            public: verifying_key,
        }
    }

    pub fn sign_message(private_key: &SigningKey, data: &[u8]) -> Signature {
        private_key.sign(data)
    }

    pub fn verify_signature(public_key: &VerifyingKey, signature: &Signature, data: &[u8]) -> Result<(), SignatureError> {
        public_key.verify(data, signature)
    }

    pub fn encryption_key_to_base64(key: &[u8]) -> String {
        base64_utils::bytes_to_base64(key)
    }

    pub fn verifying_key_to_string(key: &VerifyingKey) -> String {
        base64_utils::bytes_to_base64(key.as_bytes())
    }

    pub fn verifying_key_from_string(key_str: &str) -> Result<VerifyingKey, String> {
        let bytes = base64_utils::base64_to_bytes(key_str).map_err(|e| e.to_string())?;
        VerifyingKey::from_bytes(&bytes.try_into().map_err(|_| "Invalid key length")?)
            .map_err(|e| e.to_string())
    }

    pub fn public_key_from_base64(pub_key_str: &str, can_encrypt: bool) -> Result<Vec<u8>, String> {
        let bytes = base64_utils::base64_to_bytes(pub_key_str).map_err(|e| e.to_string())?;
        if can_encrypt && bytes.len() != 32 {
            return Err("Invalid encryption key length".to_string());
        }
        Ok(bytes)
    }

    /// Converts Ed25519 VerifyingKey to X25519 PublicKey. CACHE THE RESULT.
    pub fn ed_pub_to_x25519(ed_pub: &VerifyingKey) -> Result<PublicKey, String> {
        let ed_point = curve25519_dalek::edwards::CompressedEdwardsY::from_slice(ed_pub.as_bytes())
            .map_err(|e| format!("Invalid Ed25519 public key: {}", e))?
            .decompress()
            .ok_or("Failed to decompress Ed25519 point")?;
        Ok(PublicKey::from(ed_point.to_montgomery().to_bytes()))
    }

    /// Converts Ed25519 SigningKey to X25519 StaticSecret. CACHE THE RESULT.
    pub fn ed_priv_to_x25519(ed_priv: &SigningKey) -> StaticSecret {
        use sha2::Digest;
        let hash = sha2::Sha512::digest(ed_priv.to_bytes());
        let mut clamped = [0u8; 32];
        clamped.copy_from_slice(&hash[..32]);
        clamped[0] &= 248;
        clamped[31] &= 127;
        clamped[31] |= 64;
        StaticSecret::from(clamped)
    }

    /// Derives AES-256 key from ECDH. Call ONCE per (ephemeral_priv, recipient) pair, then cache.
    pub fn derive_aes_key(ephemeral_priv: &StaticSecret, recipient_x_pub: &PublicKey) -> [u8; 32] {
        let shared = ephemeral_priv.diffie_hellman(recipient_x_pub);
        // Use shared secret directly as AES key (already 32 bytes from X25519)
        shared.to_bytes()
    }

    /// Derives session key for transport layer. Call ONCE per connection.
    pub fn derive_session_key(my_priv: &StaticSecret, their_pub: &PublicKey) -> [u8; 32] {
        my_priv.diffie_hellman(their_pub).to_bytes()
    }

    /// Derives an X25519 StaticSecret from a seed for deterministic ephemeral keys.
    pub fn derive_ephemeral_key(seed: &[u8]) -> StaticSecret {
        use sha2::Digest;
        let hash = sha2::Sha256::digest(seed);
        let mut clamped = [0u8; 32];
        clamped.copy_from_slice(&hash[..32]);
        clamped[0] &= 248;
        clamped[31] &= 127;
        clamped[31] |= 64;
        StaticSecret::from(clamped)
    }

    /// Encrypts with PRE-DERIVED AES key and PRE-COMPUTED ephemeral public key.
    /// This is the fast path - just AES-GCM.
    pub fn encrypt_with_aes(aes_key: &[u8; 32], ephemeral_pub: &PublicKey, plaintext: &[u8]) -> Result<Vec<u8>, String> {
        use aes_gcm::{aead::Aead, Aes256Gcm, KeyInit};
        let cipher = Aes256Gcm::new_from_slice(aes_key).map_err(|e| format!("AES: {}", e))?;

        let mut nonce_bytes = [0u8; 12];
        OsRng.fill_bytes(&mut nonce_bytes);
        let nonce = GenericArray::from_slice(&nonce_bytes);

        let ct = cipher.encrypt(nonce, plaintext).map_err(|e| format!("Encrypt: {}", e))?;

        // Pack: [Ephemeral Pub (32)] [Nonce (12)] [Ciphertext + Tag]
        let total_len = 32 + 12 + ct.len();
        let mut result = vec![0u8; total_len];
        result[0..32].copy_from_slice(ephemeral_pub.as_bytes());
        result[32..44].copy_from_slice(&nonce_bytes);
        result[44..].copy_from_slice(&ct);
        Ok(result)
    }

    /// Decrypts with PRE-DERIVED AES key. Call AFTER extracting sender's ephemeral pub once.
    pub fn decrypt_with_aes(aes_key: &[u8; 32], payload: &[u8]) -> Result<Vec<u8>, String> {
        if payload.len() < 32 + 12 {
            return Err("Payload too short".to_string());
        }
        // Skip ephemeral pub (32 bytes) - already extracted and cached at session start
        let nonce_bytes = &payload[32..44];
        let ciphertext = &payload[44..];

        use aes_gcm::{aead::Aead, Aes256Gcm, KeyInit};
        let cipher = Aes256Gcm::new_from_slice(aes_key).map_err(|e| format!("AES: {}", e))?;
        let nonce = GenericArray::from_slice(nonce_bytes);
        cipher.decrypt(nonce, ciphertext).map_err(|e| format!("Decrypt: {}", e))
    }

    /// Extracts sender's ephemeral public key from payload. Call ONCE per session, cache result.
    pub fn extract_sender_ephemeral(payload: &[u8]) -> Result<PublicKey, String> {
        if payload.len() < 32 {
            return Err("Payload too short".to_string());
        }
        let bytes: [u8; 32] = payload[0..32].try_into().map_err(|_| "Invalid key")?;
        Ok(PublicKey::from(bytes))
    }

    /// One-off decrypt for messages where sender uses random ephemeral (can't cache).
    /// Slower than decrypt_with_aes - use only when sender ephemeral varies per message.
    pub fn decrypt_e2e(my_ed_sk: &SigningKey, payload: &[u8]) -> Result<Vec<u8>, String> {
        let my_x_priv = Self::ed_priv_to_x25519(my_ed_sk);
        let sender_eph = Self::extract_sender_ephemeral(payload)?;
        let aes_key = Self::derive_aes_key(&my_x_priv, &sender_eph);
        Self::decrypt_with_aes(&aes_key, payload)
    }

    /// One-off encrypt with random ephemeral. Slower than encrypt_with_aes.
    /// Use only for one-off messages, not session-based messaging.
    pub fn encrypt_e2e(recipient_ed_pk: &VerifyingKey, plaintext: &[u8]) -> Result<Vec<u8>, String> {
        let recipient_x_pub = Self::ed_pub_to_x25519(recipient_ed_pk)?;
        let ephemeral_priv = StaticSecret::random_from_rng(&mut OsRng);
        let ephemeral_pub = PublicKey::from(&ephemeral_priv);
        let aes_key = Self::derive_aes_key(&ephemeral_priv, &recipient_x_pub);
        Self::encrypt_with_aes(&aes_key, &ephemeral_pub, plaintext)
    }


    /// Simple Asymmetric Encryption: Encrypts data for a recipient's Public Key.
    /// Returns [EphemeralPubKey 32B] [Nonce 12B] [Ciphertext].
    /// Internally uses Ephemeral ECDH + AES-256-GCM.
    pub fn encrypt_asymmetric(recipient_pk: &VerifyingKey, plaintext: &[u8]) -> Result<Vec<u8>, String> {
        Self::encrypt_e2e(recipient_pk, plaintext)
    }

    /// Explicitly Deterministic Asymmetric Encryption (for Onion Routing).
    /// Uses a seed to derive the ephemeral key.
    pub fn encrypt_asymmetric_deterministic(recipient_pk: &VerifyingKey, plaintext: &[u8], seed: &[u8]) -> Result<Vec<u8>, String> {
        let recipient_x_pub = Self::ed_pub_to_x25519(recipient_pk)?;

        // Deterministic derivation
        let ephemeral_priv = Self::derive_ephemeral_key(seed);
        let ephemeral_pub = PublicKey::from(&ephemeral_priv);
        let aes_key = Self::derive_aes_key(&ephemeral_priv, &recipient_x_pub);

        Self::encrypt_with_aes(&aes_key, &ephemeral_pub, plaintext)
    }

    /// Simple Asymmetric Decryption: Decrypts data using my Private Key.
    /// Expects [EphemeralPubKey 32B] [Nonce 12B] [Ciphertext].
    pub fn decrypt_asymmetric(my_sk: &SigningKey, ciphertext: &[u8]) -> Result<Vec<u8>, String> {
        Self::decrypt_e2e(my_sk, ciphertext)
    }

    /// Asymmetric Decryption with Session Caching.
    /// Checks `cache` for `SenderEphemeralKey`. If hit, uses cached AES key.
    /// If miss, derives key and updates `cache`.
    pub fn decrypt_asymmetric_cached(
        my_sk: &SigningKey,
        ciphertext: &[u8],
        cache: &dashmap::DashMap<[u8; 32], [u8; 32]>,
    ) -> Result<Vec<u8>, String> {
        // 1. Extract Ephemeral Key (first 32 bytes)
        let sender_eph_key = Self::extract_sender_ephemeral(ciphertext)?;
        let eph_bytes = *sender_eph_key.as_bytes();

        // 2. Check Cache
        if let Some(aes_key) = cache.get(&eph_bytes) {
            return Self::decrypt_with_aes(&aes_key, ciphertext);
        }

        // 3. Derive and Cache
        let my_x_priv = Self::ed_priv_to_x25519(my_sk);
        let aes_key = Self::derive_aes_key(&my_x_priv, &sender_eph_key);

        // Verify decryption works before caching?
        // Actually, derive_aes_key is deterministic. Decryption check happens in decrypt_with_aes (GCM tag).
        // But we only want to cache if it's the correct key (though eph collision is impossible).
        // We can cache it.

        let result = Self::decrypt_with_aes(&aes_key, ciphertext);
        if result.is_ok() {
            cache.insert(eph_bytes, aes_key);
        }
        result
    }
}
