/*
 *  DecentMesh Consensus: Network & Routing
 *  ---------------------------------------
 *  Protocols defaults, routing constraints, and cryptographic sizes
 *  for the peer-to-peer transport layer.
 */

/// Maximum hops for broadcast message propagation
pub const BROADCAST_PROPAGATION_TTL: i32 = 5;

/// Default initial capacity for network buffers (packets)
pub const DEFAULT_CAPACITY: i32 = 100;

/// Maximum number of nodes in an onion-routed circuit (hops)
pub const MAX_ROUTE_LENGTH: usize = 6;

/// Identifier size for FlowNet beam packets (bytes)
pub const BEAM_HASH_SIZE: usize = 12;

/// Bit-length of the AES encryption key for Beam packets
pub const BEAM_AES_ENCRYPTION_KEY_SIZE: usize = 256;

/// Standard bit-length for handshake AES encryption keys
pub const DEFAULT_HANDSHAKE_AES_KEY_SIZE: usize = 256;

/// Size of the salt used for key derivation (bytes)
pub const DEFAULT_AES_SALT_SIZE: usize = 4;

/// Standard nonce size for AES-GCM encryption (bytes)
pub const DEFAULT_AES_GCM_NONCE_SIZE: usize = 12;

/// Standard tag (MAC) size for AES-GCM protection (bytes)
pub const DEFAULT_AES_GCM_TAG_SIZE: usize = 16;

/// Hardcoded fallback salt for secondary cryptographic operations
pub const DEFAULT_AES_SALT: &[u8] = b"\x85\x00\x01\x08\x86\x03\x04\x09";

/// Size of the framing header for encrypted chunks (bytes)
pub const AES_FRAME_SIZE: usize = 4;

/// Socket receive buffer capacity (bytes)
pub const RECV_BUFFER_SIZE: i32 = 65536;

/// Socket send buffer capacity (bytes)
pub const SEND_BUFFER_SIZE: i32 = 65536;

/// Preferred symmetric encryption algorithm
pub const USED_ALGORITHM: &str = "AES";
