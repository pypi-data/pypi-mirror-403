use crate::crypto::asymmetric::{AsymCrypt, VerifyingKey};

pub struct Serializer;

#[derive(Debug, Clone, minicbor::Encode, minicbor::Decode)]
pub struct SerializedData {
    #[n(0)]
    pub pub_key: String,
    #[n(1)]
    pub sig: Vec<u8>,
    #[n(2)]
    pub data: Vec<u8>,
    #[n(3)]
    pub target: Option<String>,
    #[n(4)]
    pub cmd: Option<u16>,
    #[n(5)]
    pub csig: Option<Vec<u8>>,
    #[n(6)]
    pub cpub: Option<String>,
    #[n(7)]
    pub ttl: Option<i32>,
}

impl Serializer {
    pub fn serialize_data(
        public_key: &VerifyingKey,
        signature: &[u8],
        encrypted_data: &[u8],
        target_pub_key: Option<&str>,
        cmd: Option<u16>,
        command_signature: Option<&[u8]>,
        command_public_key: Option<&VerifyingKey>,
        ttl: Option<i32>,
    ) -> Vec<u8> {
        Self::serialize_data_with_pk_str(
            &AsymCrypt::verifying_key_to_string(public_key),
            signature,
            encrypted_data,
            target_pub_key,
            cmd,
            command_signature,
            command_public_key.map(|k| AsymCrypt::verifying_key_to_string(k)).as_deref(),
            ttl,
        )
    }

    /// Fast path - takes pre-encoded public key string to avoid base64 on hot path.
    pub fn serialize_data_with_pk_str(
        pub_key_str: &str,
        signature: &[u8],
        encrypted_data: &[u8],
        target_pub_key: Option<&str>,
        cmd: Option<u16>,
        command_signature: Option<&[u8]>,
        command_public_key_str: Option<&str>,
        ttl: Option<i32>,
    ) -> Vec<u8> {
        let data = SerializedData {
            pub_key: pub_key_str.to_string(),
            sig: signature.to_vec(),
            data: encrypted_data.to_vec(),
            target: target_pub_key.map(|s| s.to_string()),
            cmd,
            csig: command_signature.map(|s| s.to_vec()),
            cpub: command_public_key_str.map(|s| s.to_string()),
            ttl,
        };

        minicbor::to_vec(&data).expect("Serialization failed")
    }

    pub fn deserialize_data(serialized_data: &[u8]) -> Result<SerializedData, String> {
        minicbor::decode(serialized_data)
            .map_err(|e| format!("CBOR deserialization error: {}", e))
    }
}


