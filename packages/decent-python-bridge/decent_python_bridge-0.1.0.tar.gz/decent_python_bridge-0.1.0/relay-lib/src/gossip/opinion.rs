use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Opinion {
    pub issuer: String,
    pub subject: String,
    pub weight: i32,
    pub reason: String,
    pub hlc: u64,
    pub signature: Vec<u8>,
}

impl Opinion {
    pub fn new(issuer: String, subject: String, weight: i32, reason: String) -> Self {
        Opinion {
            issuer,
            subject,
            weight,
            reason,
            hlc: 0,
            signature: Vec::new(),
        }
    }
}

