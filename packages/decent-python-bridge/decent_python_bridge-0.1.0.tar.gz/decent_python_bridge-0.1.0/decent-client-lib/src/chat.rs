use chrono::{DateTime, Local, TimeZone};
use relay_lib::crypto::symmetric::{AESCipher, SymmetricCipher};
use std::fs;
use std::path::Path;
use uuid::Uuid;

use serde::{Serialize, Deserialize};

pub mod timestamp_codec {
    use super::*;
    use minicbor::{Encoder, Decoder};

    pub fn encode<C, W>(v: &DateTime<Local>, e: &mut Encoder<W>, _ctx: &mut C) -> Result<(), minicbor::encode::Error<W::Error>>
    where
        W: minicbor::encode::Write,
    {
        e.i64(v.timestamp_millis())?;
        Ok(())
    }

    pub fn decode<'b, C>(d: &mut Decoder<'b>, _ctx: &mut C) -> Result<DateTime<Local>, minicbor::decode::Error> {
        let millis = d.i64()?;
        Ok(Local.timestamp_millis_opt(millis).unwrap())
    }
}

#[derive(Debug, Clone, minicbor::Encode, minicbor::Decode, Serialize, Deserialize)]
pub struct ChatMessage {
    #[n(0)] pub id: String,
    #[n(1)] pub sender: String,      // "You" or contact name
    #[n(2)] pub content: String,
    #[n(3)]
    #[cbor(with = "timestamp_codec")]
    pub timestamp: DateTime<Local>,
    #[n(4)] pub is_outgoing: bool,
    #[n(5)] pub acked: bool,
    #[n(6)] pub ack_latency: Option<i64>,
}

impl ChatMessage {
    pub fn new(sender: String, content: String, is_outgoing: bool) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            sender,
            content,
            timestamp: Local::now(),
            is_outgoing,
            acked: false,
            ack_latency: None,
        }
    }
}

#[derive(Debug, minicbor::Encode, minicbor::Decode)]
pub struct ChatHistory {
    #[n(0)] messages: Vec<ChatMessage>,
    #[n(1)] max_messages: usize,
}

impl ChatHistory {
    pub fn new() -> Self {
        Self {
            messages: Vec::new(),
            max_messages: 1000,
        }
    }

    pub fn add_message(&mut self, msg: ChatMessage) {
        if self.messages.iter().any(|m| m.id == msg.id) {
            return;
        }
        self.messages.push(msg);
        if self.messages.len() > self.max_messages {
            self.messages.remove(0);
        }
    }

    pub fn get_messages(&self) -> &[ChatMessage] {
        &self.messages
    }

    pub fn messages_mut(&mut self) -> &mut Vec<ChatMessage> {
        &mut self.messages
    }

    pub fn save_encrypted(&self, path: &Path, key_seed: &[u8]) -> anyhow::Result<()> {
        let data = minicbor::to_vec(self)?;
        let cipher = AESCipher::new(key_seed, 256, None);
        let encrypted = cipher.encrypt(&data);
        fs::write(path, encrypted)?;
        Ok(())
    }

    pub fn load_encrypted(path: &Path, key_seed: &[u8]) -> anyhow::Result<Self> {
        if !path.exists() {
            return Ok(Self::new());
        }
        let encrypted = fs::read(path)?;
        let cipher = AESCipher::new(key_seed, 256, None);
        let decrypted = cipher.decrypt(&encrypted)
            .map_err(|e| anyhow::anyhow!("Decryption failed: {}", e))?;
        let history = minicbor::decode(&decrypted)?;
        Ok(history)
    }
}
