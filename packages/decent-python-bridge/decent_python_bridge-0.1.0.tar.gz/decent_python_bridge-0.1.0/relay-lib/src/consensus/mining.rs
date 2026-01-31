/*
 *  DecentMesh Consensus: Mining & Difficulty
 *  -----------------------------------------
 *  Constants defining the structure of Proof-of-Work (PoW) difficulty settings
 *  and Argon2i mining parameters for identity verification.
 */

// --- Difficulty Field Byte Sizes ---
pub const T_COST_BYTE_SIZE: usize = 4;
pub const M_COST_BYTE_SIZE: usize = 4;
pub const P_COST_BYTE_SIZE: usize = 1;
pub const N_BITS_BYTE_SIZE: usize = 1;
pub const HASH_LEN_CHARS_BYTE_SIZE: usize = 1;
pub const COMPRESSION_LEVEL_BYTE_SIZE: usize = 1;
pub const COMPRESSION_TYPE_BYTE_SIZE: usize = 1;
pub const EXPRESS_POW_BYTE_SIZE: usize = 1;

/// Total length of the serialized difficulty block (bytes)
pub const MERGED_DIFFICULTY_BYTE_LEN: usize = T_COST_BYTE_SIZE + M_COST_BYTE_SIZE + P_COST_BYTE_SIZE + N_BITS_BYTE_SIZE + HASH_LEN_CHARS_BYTE_SIZE + COMPRESSION_LEVEL_BYTE_SIZE + COMPRESSION_TYPE_BYTE_SIZE + EXPRESS_POW_BYTE_SIZE;

// --- Serialization Slices (Byte offsets) ---
pub const M_COST_CHUNK_SLICE: usize = T_COST_BYTE_SIZE + M_COST_BYTE_SIZE;
pub const P_COST_CHUNK_SLICE: usize = M_COST_CHUNK_SLICE + P_COST_BYTE_SIZE;
pub const N_BITS_CHUNK_SLICE: usize = P_COST_CHUNK_SLICE + N_BITS_BYTE_SIZE;
pub const HASH_LEN_CHARS_CHUNK_SLICE: usize = N_BITS_CHUNK_SLICE + HASH_LEN_CHARS_BYTE_SIZE;
pub const COMPRESSION_LEVEL_CHUNK_SLICE: usize = HASH_LEN_CHARS_CHUNK_SLICE + COMPRESSION_LEVEL_BYTE_SIZE;
pub const COMPRESSION_TYPE_CHUNK_SLICE: usize = COMPRESSION_LEVEL_CHUNK_SLICE + COMPRESSION_TYPE_BYTE_SIZE;
pub const EXPRESS_POW_CHUNK_SLICE: usize = COMPRESSION_TYPE_CHUNK_SLICE + EXPRESS_POW_BYTE_SIZE;

/// Default cryptographic salt used for Identity PoW
pub const DEFAULT_SALT: &[u8] = b"Knz3z0&PavluT0m";
