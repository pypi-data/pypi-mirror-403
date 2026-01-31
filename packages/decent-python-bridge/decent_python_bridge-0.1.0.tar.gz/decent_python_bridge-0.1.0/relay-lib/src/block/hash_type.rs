use crate::block::block::BlockHash;
use crate::pow::difficulty::Difficulty;
use crate::pow::hashing::{argon_hash_func, sha256_hash_func};
use crate::consensus::blockchain::ENDIAN_TYPE;

pub struct MemoryHash {
    pub diff: Difficulty,
    pub value: Vec<u8>,
}

impl BlockHash for MemoryHash {
    fn value(&self) -> &[u8] {
        &self.value
    }
    
    fn value_as_int(&self) -> u64 {
        MemoryHash::value_as_int(self)
    }
    
    fn diff(&self) -> &Difficulty {
        &self.diff
    }
}

impl MemoryHash {
    pub fn new(diff: Difficulty, data: &[u8]) -> Self {
        let value = argon_hash_func(data, &diff);
        MemoryHash { diff, value }
    }

    pub fn value_as_int(&self) -> u64 {
        match ENDIAN_TYPE {
            "little" => u64::from_le_bytes(
                self.value[..8.min(self.value.len())].try_into().unwrap_or([0; 8])
            ),
            "big" => u64::from_be_bytes(
                self.value[..8.min(self.value.len())].try_into().unwrap_or([0; 8])
            ),
            _ => u64::from_le_bytes(
                self.value[..8.min(self.value.len())].try_into().unwrap_or([0; 8])
            ),
        }
    }

    pub fn value_as_hex(&self) -> String {
        hex::encode(&self.value)
    }
}

pub struct ShaHash {
    pub diff: Difficulty,
    pub value: Vec<u8>,
}

impl BlockHash for ShaHash {
    fn value(&self) -> &[u8] {
        &self.value
    }
    
    fn value_as_int(&self) -> u64 {
        ShaHash::value_as_int(self)
    }
    
    fn diff(&self) -> &Difficulty {
        &self.diff
    }
}

impl ShaHash {
    pub fn new(diff: Difficulty, data: &[u8]) -> Self {
        let value = sha256_hash_func(data);
        ShaHash { diff, value }
    }

    pub fn value_as_int(&self) -> u64 {
        match ENDIAN_TYPE {
            "little" => u64::from_le_bytes(
                self.value[..8.min(self.value.len())].try_into().unwrap_or([0; 8])
            ),
            "big" => u64::from_be_bytes(
                self.value[..8.min(self.value.len())].try_into().unwrap_or([0; 8])
            ),
            _ => u64::from_le_bytes(
                self.value[..8.min(self.value.len())].try_into().unwrap_or([0; 8])
            ),
        }
    }

    pub fn value_as_hex(&self) -> String {
        hex::encode(&self.value)
    }
}

