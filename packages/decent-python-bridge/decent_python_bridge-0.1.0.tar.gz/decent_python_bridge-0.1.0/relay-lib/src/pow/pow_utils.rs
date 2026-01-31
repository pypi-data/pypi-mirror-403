use crate::block::block::BlockHash;
use crate::pow::difficulty::Difficulty;
use crate::pow::hashing::{argon_hash_func, sha256_hash_func};
use crate::util::constants::ENDIAN_TYPE;

pub struct PowUtils;


impl PowUtils {
    pub fn get_bit_length(hash: &dyn BlockHash, nonce: u64, diff: &Difficulty) -> usize {
        // Python uses the diff parameter for Argon2, not hash.diff()
        // This matches Python's get_bit_length(i_hash, nonce, diff) signature
        if diff.express == 0 {
            // Python: input_data = int_to_bytes(hash_t.value_as_int() + nonce)
            let input_bytes = crate::util::byte_ops::add_u64_to_le_bytes_trim(hash.value(), nonce);
            
            let hash_output = argon_hash_func(&input_bytes, diff);
            // Python converts entire hash to int and uses bit_length()
            // bit_length() returns number of bits needed to represent the integer
            let hash_len = (diff.hash_len_chars as usize).min(hash_output.len());
            Self::bit_length_full_hash(&hash_output[..hash_len], ENDIAN_TYPE)
        } else {
            // Python: input_data = int_to_bytes(hash_t.value_as_int() + nonce)
            let input_bytes = crate::util::byte_ops::add_u64_to_le_bytes_trim(hash.value(), nonce);
            
            let hash_output = sha256_hash_func(&input_bytes);
            let hash_len = (diff.hash_len_chars as usize).min(hash_output.len());
            Self::bit_length_full_hash(&hash_output[..hash_len], ENDIAN_TYPE)
        }
    }


    pub fn value_as_int(value: &[u8]) -> u64 {
        // Python converts entire hash to int, but we can only handle 8 bytes in u64
        // For bit_length calculation, we need to check the most significant bytes
        // For little-endian: most significant byte is the last one
        // For big-endian: most significant byte is the first one
        match ENDIAN_TYPE {
            "little" => {
                // For little-endian, take up to 8 bytes from the start
                // But for bit_length, we care about the most significant byte (last byte in little-endian)
                let len = value.len().min(8);
                u64::from_le_bytes(value[..len].try_into().unwrap_or([0; 8]))
            },
            "big" => {
                let len = value.len().min(8);
                u64::from_be_bytes(value[..len].try_into().unwrap_or([0; 8]))
            },
            _ => {
                let len = value.len().min(8);
                u64::from_le_bytes(value[..len].try_into().unwrap_or([0; 8]))
            },
        }
    }
    
    // Helper to calculate bit_length for a full hash (up to 32 bytes)
    // Python's int.bit_length() returns the number of bits needed to represent the integer
    // Python converts the entire hash to an integer first: int.from_bytes(hash, ENDIAN_TYPE)
    // Then calls .bit_length() on that integer
    // For n > 0: bit_length = floor(log2(n)) + 1
    // For n = 0: bit_length = 0
    pub fn bit_length_full_hash(hash: &[u8], endian: &str) -> usize {
        if hash.is_empty() {
            return 0;
        }
        
        // Convert bytes to integer and calculate bit_length
        // Python's int.from_bytes() with little-endian: [b0, b1, ..., b31] = b0 + b1*256 + ... + b31*256^31
        // We need to find the most significant non-zero byte and calculate bit_length correctly
        match endian {
            "little" => {
                // Find the most significant non-zero byte (last byte in little-endian)
                let mut msb_idx = hash.len();
                for i in (0..hash.len()).rev() {
                    if hash[i] != 0 {
                        msb_idx = i;
                        break;
                    }
                }
                if msb_idx == hash.len() {
                    return 0; // All zeros
                }
                // Calculate: (byte_index * 8) + bits_needed_for_byte_value
                // For a byte value v: bits_needed = floor(log2(v)) + 1 = 8 - leading_zeros(v)
                // Example: v=1 -> leading_zeros=7 -> bits_needed=1, v=255 -> leading_zeros=0 -> bits_needed=8
                let msb_byte = hash[msb_idx];
                let bits_needed_for_byte = if msb_byte == 0 {
                    0
                } else {
                    // leading_zeros counts from the MSB, so 8 - leading_zeros gives bits needed
                    let leading_zeros = msb_byte.leading_zeros() as usize;
                    8 - leading_zeros
                };
                let result = (msb_idx * 8) + bits_needed_for_byte;
                // Python's bit_length() returns 0 for 0, but we return 0 above
                // For non-zero values, bit_length is always >= 1
                if result == 0 {
                    0
                } else {
                    result
                }
            },
            "big" => {
                // Big-endian: most significant byte is first
                let mut msb_idx = hash.len();
                for i in 0..hash.len() {
                    if hash[i] != 0 {
                        msb_idx = i;
                        break;
                    }
                }
                if msb_idx == hash.len() {
                    return 0; // All zeros
                }
                let msb_byte = hash[msb_idx];
                let leading_zeros_in_byte = msb_byte.leading_zeros() as usize;
                let bits_needed_for_byte = if msb_byte == 0 {
                    0
                } else {
                    8 - leading_zeros_in_byte.min(8)
                };
                let result = ((hash.len() - msb_idx - 1) * 8) + bits_needed_for_byte;
                if result == 0 {
                    0
                } else {
                    result
                }
            },
            _ => {
                // Default to little-endian
                let mut msb_idx = hash.len();
                for i in (0..hash.len()).rev() {
                    if hash[i] != 0 {
                        msb_idx = i;
                        break;
                    }
                }
                if msb_idx == hash.len() {
                    return 0;
                }
                let msb_byte = hash[msb_idx];
                let leading_zeros_in_byte = msb_byte.leading_zeros() as usize;
                let bits_needed_for_byte = if msb_byte == 0 {
                    0
                } else {
                    8 - leading_zeros_in_byte.min(8)
                };
                let result = (msb_idx * 8) + bits_needed_for_byte;
                if result == 0 {
                    0
                } else {
                    result
                }
            },
        }
    }
}

