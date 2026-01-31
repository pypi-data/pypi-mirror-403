use crate::block::block::BlockHash;
use crate::pow::hashing::{argon_hash_func, sha256_hash_func};


pub fn compute_argon2_pow(n_bits: u8, hash_t: &dyn BlockHash, mut nonce: u64) -> u64 {
    use crate::util::byte_ops::bytes_to_int_bit_length;
    let target_bits = (hash_t.diff().hash_len_chars as usize * 8) - n_bits as usize;
    
    loop {
        // Python: input_data = int_to_bytes(hash_t.value_as_int() + nonce)
        // This is BigInt addition + Trim
        let input_bytes = crate::util::byte_ops::add_u64_to_le_bytes_trim(hash_t.value(), nonce);
        
        let hash_output = argon_hash_func(&input_bytes, hash_t.diff());
        let bit_length = bytes_to_int_bit_length(&hash_output);
        
        if bit_length <= target_bits {
            return nonce;
        }
        nonce += 1;
    }
}

pub fn compute_sha256_pow(n_bits: u8, hash_t: &dyn BlockHash, mut nonce: u64) -> u64 {
    use crate::util::byte_ops::bytes_to_int_bit_length;
    let target_bits = (hash_t.diff().hash_len_chars as usize * 8) - n_bits as usize;
    
    loop {
        // Python: input_data = int_to_bytes(hash_t.value_as_int() + nonce)
        let input_bytes = crate::util::byte_ops::add_u64_to_le_bytes_trim(hash_t.value(), nonce);
        
        let hash_output = sha256_hash_func(&input_bytes);
        let bit_length = bytes_to_int_bit_length(&hash_output);
        
        if bit_length <= target_bits {
            return nonce;
        }
        nonce += 1;
    }
}


