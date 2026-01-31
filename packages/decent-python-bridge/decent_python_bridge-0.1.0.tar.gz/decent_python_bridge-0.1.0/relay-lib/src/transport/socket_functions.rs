use crate::consensus::blockchain::BLOCK_PREFIX_LENGTH_BYTES;
use crate::consensus::blockchain::ENDIAN_TYPE;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

pub async fn recv_all<R: AsyncReadExt + Unpin>(socket: &mut R) -> Result<(Vec<u8>, usize), String> {
    let mut length_prefix = vec![0u8; BLOCK_PREFIX_LENGTH_BYTES];
    socket.read_exact(&mut length_prefix).await.map_err(|e| e.to_string())?;
    
    let total_bytes = match ENDIAN_TYPE {
        "little" => {
            let mut bytes = [0u8; 4];
            bytes[..BLOCK_PREFIX_LENGTH_BYTES].copy_from_slice(&length_prefix);
            u32::from_le_bytes(bytes) as usize
        },
        "big" => {
            let mut bytes = [0u8; 4];
            bytes[4 - BLOCK_PREFIX_LENGTH_BYTES..].copy_from_slice(&length_prefix);
            u32::from_be_bytes(bytes) as usize
        },
        _ => {
            let mut bytes = [0u8; 4];
            bytes[..BLOCK_PREFIX_LENGTH_BYTES].copy_from_slice(&length_prefix);
            u32::from_le_bytes(bytes) as usize
        },
    };
    
    if total_bytes == 0 {
        return Ok((Vec::new(), 0));
    }
    
    let mut buffer = vec![0u8; total_bytes];
    socket.read_exact(&mut buffer).await.map_err(|e| e.to_string())?;
    
    Ok((buffer, total_bytes))
}

pub async fn send_all<W: AsyncWriteExt + Unpin>(socket: &mut W, data: &[u8]) -> Result<(), String> {
    let length_prefix_full = match ENDIAN_TYPE {
        "little" => (data.len() as u32).to_le_bytes(),
        "big" => (data.len() as u32).to_be_bytes(),
        _ => (data.len() as u32).to_le_bytes(),
    };
    
    let length_prefix = &length_prefix_full[..BLOCK_PREFIX_LENGTH_BYTES];
    socket.write_all(length_prefix).await.map_err(|e| e.to_string())?;
    socket.write_all(data).await.map_err(|e| e.to_string())?;
    socket.flush().await.map_err(|e| e.to_string())?;
    
    Ok(())
}


use crate::crypto::symmetric::{AESCipher, SymmetricCipher};

pub async fn recv_encrypted<R: AsyncReadExt + Unpin>(socket: &mut R, cipher: &AESCipher) -> Result<Vec<u8>, String> {
    let (ciphertext, _) = recv_all(socket).await?;
    cipher.decrypt(&ciphertext).map_err(|e| format!("Decryption failed: {}", e))
}

pub async fn send_encrypted<W: AsyncWriteExt + Unpin>(socket: &mut W, cipher: &AESCipher, data: &[u8]) -> Result<(), String> {
    let ciphertext = cipher.encrypt(data);
    send_all(socket, &ciphertext).await
}
