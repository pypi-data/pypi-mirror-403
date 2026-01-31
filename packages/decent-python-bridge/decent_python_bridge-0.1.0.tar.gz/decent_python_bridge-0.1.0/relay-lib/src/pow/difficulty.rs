use serde::{Serialize, Deserialize};
use crate::consensus::mining::*;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Difficulty {
    pub t_cost: u32,
    pub m_cost: u32,
    pub p_cost: u8,
    pub n_bits: u8,
    pub hash_len_chars: u8,
    pub compression_level: u8,
    pub compression_type: u8,
    pub express: u8,
}

impl Difficulty {
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut result = Vec::with_capacity(MERGED_DIFFICULTY_BYTE_LEN);
        result.extend_from_slice(&self.t_cost.to_le_bytes());
        result.extend_from_slice(&self.m_cost.to_le_bytes());
        result.push(self.p_cost);
        result.push(self.n_bits);
        result.push(self.hash_len_chars);
        result.push(self.compression_level);
        result.push(self.compression_type);
        result.push(self.express);
        result
    }

    pub fn from_bytes(data: &[u8]) -> Result<Self, String> {
        if data.len() < MERGED_DIFFICULTY_BYTE_LEN {
            return Err("Insufficient bytes for difficulty".to_string());
        }
        
        let t_cost = u32::from_le_bytes(data[0..4].try_into().unwrap());
        let m_cost = u32::from_le_bytes(data[4..8].try_into().unwrap());
        let p_cost = data[8];
        let n_bits = data[9];
        let hash_len_chars = data[10];
        let compression_level = data[11];
        let compression_type = data[12];
        let express = data[13];
        
        let mut diff = Difficulty {
            t_cost,
            m_cost,
            p_cost,
            n_bits,
            hash_len_chars,
            compression_level,
            compression_type,
            express,
        };
        
        let req_m_cost = 8 * p_cost as u32;
        if req_m_cost > m_cost {
            diff.m_cost = req_m_cost;
        }
        
        Ok(diff)
    }

    pub fn work(&self) -> f64 {
        (self.t_cost as f64) * (self.m_cost as f64) * (2f64.powi(self.n_bits as i32))
    }
}

impl Default for Difficulty {
    fn default() -> Self {
        Difficulty {
            t_cost: 1,
            m_cost: 8,
            p_cost: 1,
            n_bits: 1,
            hash_len_chars: 32,
            compression_level: 9,
            compression_type: 0,
            express: 0,
        }
    }
}

