use crate::util::constants::ENDIAN_TYPE;

pub fn int_to_bytes(num: u64) -> Vec<u8> {
    if num == 0 {
        return vec![0u8];
    }
    let byte_length = (num.bit_length() + 7) / 8;
    match ENDIAN_TYPE {
        "little" => num.to_le_bytes()[..byte_length].to_vec(),
        "big" => num.to_be_bytes()[..byte_length].to_vec(),
        _ => num.to_le_bytes()[..byte_length].to_vec(),
    }
}

pub fn bytes_to_int_bit_length(bytes: &[u8]) -> usize {
    use crate::util::constants::ENDIAN_TYPE;
    
    // Find the most significant non-zero byte based on endianness
    let (most_sig_byte_idx, most_sig_byte) = match ENDIAN_TYPE {
        "little" => {
            // For little-endian, the last byte is most significant
            let mut idx = bytes.len();
            let mut byte = 0u8;
            for (i, &b) in bytes.iter().enumerate().rev() {
                if b != 0 {
                    idx = i;
                    byte = b;
                    break;
                }
            }
            (idx, byte)
        }
        "big" => {
            // For big-endian, the first byte is most significant
            let mut idx = bytes.len();
            let mut byte = 0u8;
            for (i, &b) in bytes.iter().enumerate() {
                if b != 0 {
                    idx = i;
                    byte = b;
                    break;
                }
            }
            (idx, byte)
        }
        _ => {
            // Default to little-endian
            let mut idx = bytes.len();
            let mut byte = 0u8;
            for (i, &b) in bytes.iter().enumerate().rev() {
                if b != 0 {
                    idx = i;
                    byte = b;
                    break;
                }
            }
            (idx, byte)
        }
    };
    
    if most_sig_byte_idx == bytes.len() {
        // All zeros
        return 1;
    }
    
    // Calculate bit length: number of bytes from start to most significant byte + bits in that byte
    let leading_zeros_in_byte = most_sig_byte.leading_zeros() as usize;
    let _bits_in_byte = 8 - leading_zeros_in_byte;
    let total_bits = match ENDIAN_TYPE {
        "little" => (most_sig_byte_idx + 1) * 8 - leading_zeros_in_byte,
        "big" => (bytes.len() - most_sig_byte_idx) * 8 - leading_zeros_in_byte,
        _ => (most_sig_byte_idx + 1) * 8 - leading_zeros_in_byte,
    };
    total_bits.max(1)
}

trait BitLength {
    fn bit_length(&self) -> usize;
}

impl BitLength for u64 {
    fn bit_length(&self) -> usize {
        if *self == 0 {
            return 1;
        }
        (64 - self.leading_zeros()) as usize
    }
}

pub fn add_u64_to_le_bytes_trim(bytes: &[u8], val: u64) -> Vec<u8> {
    if bytes.is_empty() {
        return crate::util::byte_ops::int_to_bytes(val);
    }
    
    // Assume bytes are Little Endian representation of a large integer
    // We add val (u64) to this large integer
    let mut res = bytes.to_vec();
    let mut carry = val;
    
    for i in 0..res.len() {
        if carry == 0 { break; }
        // Perform addition at current byte
        let sum = (res[i] as u64) + (carry & 0xFF);
        res[i] = (sum & 0xFF) as u8;
        // Calculate new carry (remaining part of val + overflow from sum)
        carry = (carry >> 8) + (sum >> 8);
    }
    
    // If we still have carry, append bytes
    while carry > 0 {
        res.push((carry & 0xFF) as u8);
        carry >>= 8;
    }
    
    // Python's int_to_bytes trims trailing zeros (MSB)
    while res.len() > 1 && res.last() == Some(&0) {
        res.pop();
    }
    
    res
}

