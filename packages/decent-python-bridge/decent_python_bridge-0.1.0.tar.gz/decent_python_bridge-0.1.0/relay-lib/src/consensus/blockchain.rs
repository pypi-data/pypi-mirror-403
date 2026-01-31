/*
 *  DecentMesh Consensus: Blockchain
 *  -------------------------------
 *  Core constants defining the structure and constraints of the DecentMesh blockchain
 *  and block processing pipeline.
 */

/// Data endianness used for network serialization
pub const ENDIAN_TYPE: &str = "little";

/// Semantic network version [major, minor, patch]
pub const NETWORK_VERSION: [u8; 3] = [0, 0, 201];

/// Length of the block size prefix in the transport stream (bytes)
pub const BLOCK_PREFIX_LENGTH_BYTES: usize = 3;

/// Size of the block index field (bytes)
pub const INDEX_SIZE: usize = 5;

/// Size of the Proof-of-Work nonce field (bytes)
pub const NONCE_SIZE: usize = 4;

/// Size of the block timestamp field (bytes)
pub const TIMESTAMP_SIZE: usize = 8;

/// Length of standard cryptographic hashes (bytes)
pub const HASH_LEN: usize = 32;

/// Length of block-specific hashes (bytes)
pub const HASH_LEN_BLOCK: usize = 48;

/// Hard limit for a single block size (bytes)
pub const MAXIMUM_BLOCK_SIZE: usize = 4194304;

use crate::consensus::mining::MERGED_DIFFICULTY_BYTE_LEN;

/// Base64 encoded public key length (bytes)
pub const PUB_KEY_SIZE_BYTES: usize = 44;

/// Estimated CBOR serialization overhead (bytes)
pub const CBOR_OVERHEAD_BYTES: usize = 19;

/// Calculated maximum payload data size (bytes)
/// Derived from: MAX_BLOCK_SIZE - headers - overhead
pub const MAXIMUM_DATA_SIZE: usize = MAXIMUM_BLOCK_SIZE - BLOCK_PREFIX_LENGTH_BYTES - INDEX_SIZE - NONCE_SIZE - TIMESTAMP_SIZE - (PUB_KEY_SIZE_BYTES + MERGED_DIFFICULTY_BYTE_LEN + CBOR_OVERHEAD_BYTES) - HASH_LEN - HASH_LEN_BLOCK;

/// Allowed clock drift for block timestamps (seconds)
pub const TIMESTAMP_TOLERANCE: i64 = 9;

/// Enable/Disable transport-level compression
pub const COMPRESSION_ENABLED: bool = false;

/// Depth at which we stop verifying signatures for historical sync (blocks)
pub const SKIP_SIGNATURE_VERIFICATION_DEPTH: usize = 10;
