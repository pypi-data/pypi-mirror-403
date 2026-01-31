use argon2::{Argon2, Params, Version, Algorithm};
use sha2::{Sha256, Digest};
use crate::pow::difficulty::Difficulty;
use crate::util::constants::{DEFAULT_SALT, HASH_LEN};

pub fn argon_hash_func(data: &[u8], diff: &Difficulty) -> Vec<u8> {
    let params = Params::new(
        diff.m_cost,
        diff.t_cost,
        diff.p_cost as u32,
        Some(diff.hash_len_chars as usize),
    ).unwrap();
    let argon2 = Argon2::new(Algorithm::Argon2d, Version::V0x13, params);
    let mut output = vec![0u8; diff.hash_len_chars as usize];
    argon2.hash_password_into(data, DEFAULT_SALT, &mut output).unwrap();
    output
}

pub fn sha256_hash_func(data: &[u8]) -> Vec<u8> {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize()[..HASH_LEN].to_vec()
}


#[cfg(test)]
mod tests {
    use super::*;
    use crate::pow::difficulty::Difficulty;

    #[test]
    fn test_argon2d_python_match() {
        let diff = Difficulty {
            t_cost: 16,
            m_cost: 8,
            p_cost: 1,
            hash_len_chars: 32,
            ..Default::default()
        };
        let data = b"test_input";
        let hash = argon_hash_func(data, &diff);
        let expected_hash = hex::decode("576f4789fe1a10b0b42ef777c516e50a344084515f75c37c565d1be7bbdcf5e7").unwrap();
        assert_eq!(hash, expected_hash, "Hash mismatch! Rust produced: {}", hex::encode(&hash));
    }
}
