use crate::api::serializer::{SerializedData, Serializer};
use crate::block::block::Block;
use crate::crypto::asymmetric::{AsymCrypt, Signature, SigningKey};

pub struct Packager;

#[derive(Debug)]
pub struct UnpackedData {
    pub verified: bool,
    pub data: SerializedData,
    pub verified_csig: Option<bool>,
}

impl Packager {
    pub async fn pack(
        owner_key: &SigningKey,
        block: &Block,
        target_pub_key: Option<&str>,
        cmd: Option<u16>,
        skip_sign: bool,
    ) -> Result<Vec<u8>, String> {
        let block_bytes = block.to_bytes().await?;
        let public_key = owner_key.verifying_key();
        
        let signature = if !skip_sign {
            AsymCrypt::sign_message(owner_key, &block_bytes).to_bytes().to_vec()
        } else {
            Vec::new()
        };
        
        Ok(Serializer::serialize_data(
            &public_key,
            &signature,
            &block_bytes,
            target_pub_key,
            cmd,
            None,
            None,
            None,
        ))
    }

    pub fn unpack(
        serialized_data: &[u8],
        skip_key_verify: bool,
    ) -> Result<UnpackedData, String> {
        let data = Serializer::deserialize_data(serialized_data)
            .map_err(|e| format!("Serializer error: {}", e))?;

        // Skip all crypto operations if not verifying
        if skip_key_verify {
            return Ok(UnpackedData {
                verified: true,
                data,
                verified_csig: None,
            });
        }

        let pub_key = match AsymCrypt::verifying_key_from_string(&data.pub_key) {
            Ok(k) => k,
            Err(e) => return Err(format!("Failed to parse public key '{}': {}", &data.pub_key[..data.pub_key.len().min(50)], e)),
        };

        let verified = {
            if data.sig.len() != 64 {
                return Err(format!("Invalid signature length: expected 64, got {}", data.sig.len()));
            }
            let sig_bytes: [u8; 64] = data.sig[..64].try_into().map_err(|_| "Invalid signature length")?;
            let sig = Signature::from_bytes(&sig_bytes);
            AsymCrypt::verify_signature(&pub_key, &sig, &data.data).is_ok()
        };
        
        let verified_csig = if let (Some(cmd), Some(csig_bytes), Some(cpub_str)) = (data.cmd, &data.csig, &data.cpub) {
            let cpub = AsymCrypt::verifying_key_from_string(cpub_str)?;
            let cmd_bytes = cmd.to_le_bytes().to_vec();
            if csig_bytes.len() != 64 {
                return Err("Invalid csig length".to_string());
            }
            let csig_bytes_array: [u8; 64] = csig_bytes[..64].try_into().map_err(|_| "Invalid csig length")?;
            let csig = Signature::from_bytes(&csig_bytes_array);
            Some(AsymCrypt::verify_signature(&cpub, &csig, &cmd_bytes).is_ok())
        } else {
            None
        };
        
        Ok(UnpackedData {
            verified,
            data,
            verified_csig,
        })
    }

    pub fn check_verified(data: &SerializedData, verified: bool) -> Result<(), String> {
        if !verified {
            return Err(format!("Invalid signature, failed to verify data: {:?}", data));
        }
        Ok(())
    }
}


