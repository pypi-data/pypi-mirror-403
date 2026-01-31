/*
 *  DecentMesh Consensus: Distributed Hash Table (DHT)
 *  --------------------------------------------------
 *  Configuration parameters for the Kademlia-based Peer Discovery Network.
 */

/// Alpha parameter: Parallelism degree for DHT lookups (count)
pub const DHT_ALPHA: usize = 3;

/// K parameter: Maximum number of contacts per bucket (count)
pub const DHT_K: usize = 16;

/// Total number of buckets in the routing table (count)
pub const DHT_BUCKET_COUNT: usize = 256;

/// Length of DHT keys/IDs (bits)
pub const DHT_KEY_LENGTH: usize = 256;

/// Time between automatic routing table refreshes (seconds)
pub const DHT_REFRESH_INTERVAL: u64 = 3600; 
