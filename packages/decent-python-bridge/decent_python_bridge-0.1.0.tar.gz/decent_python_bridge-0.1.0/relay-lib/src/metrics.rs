use dashmap::DashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerStats {
    pub bytes_sent: u64,
    pub bytes_received: u64,
    pub messages_forwarded: u64,
}

/// Zero-overhead metrics collection using atomic counters
pub struct RelayMetrics {
    // Bandwidth tracking
    bytes_sent: AtomicU64,
    bytes_received: AtomicU64,
    total_data_transferred: AtomicU64, // Cumulative total (never resets)

    // Connection tracking
    active_connections: AtomicU64,
    total_connections: AtomicU64,

    // Message tracking
    messages_forwarded: AtomicU64,

    // Block size tracking (running sum for average calculation)
    total_block_bytes: AtomicU64,
    total_blocks: AtomicU64,

    // Per-peer tracking
    peer_stats: DashMap<String, PeerStats>,

    // Timestamp of last reset (for rate calculations)
    last_reset: AtomicU64,
}

impl RelayMetrics {
    pub fn new() -> Self {
        Self {
            bytes_sent: AtomicU64::new(0),
            bytes_received: AtomicU64::new(0),
            total_data_transferred: AtomicU64::new(0),
            active_connections: AtomicU64::new(0),
            total_connections: AtomicU64::new(0),
            messages_forwarded: AtomicU64::new(0),
            total_block_bytes: AtomicU64::new(0),
            total_blocks: AtomicU64::new(0),
            peer_stats: DashMap::new(),
            last_reset: AtomicU64::new(Self::current_timestamp()),
        }
    }

    fn current_timestamp() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs()
    }

    // Bandwidth tracking
    pub fn record_bytes_sent(&self, bytes: usize) {
        self.bytes_sent.fetch_add(bytes as u64, Ordering::Relaxed);
        self.total_data_transferred.fetch_add(bytes as u64, Ordering::Relaxed);
    }

    pub fn record_bytes_received(&self, bytes: usize) {
        self.bytes_received.fetch_add(bytes as u64, Ordering::Relaxed);
        self.total_data_transferred.fetch_add(bytes as u64, Ordering::Relaxed);
    }

    // Per-peer tracking
    pub fn record_peer_sent(&self, peer_id: &str, bytes: usize) {
        self.peer_stats.entry(peer_id.to_string())
            .and_modify(|stats| stats.bytes_sent += bytes as u64)
            .or_insert(PeerStats { bytes_sent: bytes as u64, bytes_received: 0, messages_forwarded: 0 });
    }

    pub fn record_peer_received(&self, peer_id: &str, bytes: usize) {
        self.peer_stats.entry(peer_id.to_string())
            .and_modify(|stats| stats.bytes_received += bytes as u64)
            .or_insert(PeerStats { bytes_sent: 0, bytes_received: bytes as u64, messages_forwarded: 0 });
    }

    pub fn record_peer_message(&self, peer_id: &str) {
        self.peer_stats.entry(peer_id.to_string())
            .and_modify(|stats| stats.messages_forwarded += 1)
            .or_insert(PeerStats { bytes_sent: 0, bytes_received: 0, messages_forwarded: 1 });
    }

    // Connection tracking
    pub fn increment_connections(&self) {
        self.active_connections.fetch_add(1, Ordering::Relaxed);
        self.total_connections.fetch_add(1, Ordering::Relaxed);
    }

    pub fn decrement_connections(&self) {
        self.active_connections.fetch_sub(1, Ordering::Relaxed);
    }

    // Message tracking
    pub fn record_message_forwarded(&self, block_size: usize) {
        self.messages_forwarded.fetch_add(1, Ordering::Relaxed);
        self.total_block_bytes.fetch_add(block_size as u64, Ordering::Relaxed);
        self.total_blocks.fetch_add(1, Ordering::Relaxed);
    }

    // Snapshot for stats API
    pub fn snapshot(&self) -> MetricsSnapshot {
        let now = Self::current_timestamp();
        let last_reset = self.last_reset.load(Ordering::Relaxed);
        let elapsed = (now - last_reset).max(1); // Avoid division by zero

        let bytes_sent = self.bytes_sent.load(Ordering::Relaxed);
        let bytes_received = self.bytes_received.load(Ordering::Relaxed);
        let total_blocks = self.total_blocks.load(Ordering::Relaxed);
        let total_block_bytes = self.total_block_bytes.load(Ordering::Relaxed);
        let total_data = self.total_data_transferred.load(Ordering::Relaxed);

        // Get top 10 peers by total data
        let mut peers_vec: Vec<(String, PeerStats)> = self.peer_stats.iter()
            .map(|entry| (entry.key().clone(), entry.value().clone()))
            .collect();
        peers_vec.sort_by(|a, b| {
            let a_total = a.1.bytes_sent + a.1.bytes_received;
            let b_total = b.1.bytes_sent + b.1.bytes_received;
            b_total.cmp(&a_total)
        });
        let top_peers = peers_vec.into_iter().take(10).collect();

        MetricsSnapshot {
            timestamp: now,
            bytes_sent,
            bytes_received,
            sent_bps: (bytes_sent as f64) / elapsed as f64,
            recv_bps: (bytes_received as f64) / elapsed as f64,
            active_connections: self.active_connections.load(Ordering::Relaxed),
            total_connections: self.total_connections.load(Ordering::Relaxed),
            messages_forwarded: self.messages_forwarded.load(Ordering::Relaxed),
            avg_block_size: if total_blocks > 0 {
                total_block_bytes / total_blocks
            } else {
                0
            },
            total_data_transferred: total_data,
            top_peers,
        }
    }

    // Reset counters for rate calculation (called periodically)
    pub fn reset_rates(&self) {
        self.bytes_sent.store(0, Ordering::Relaxed);
        self.bytes_received.store(0, Ordering::Relaxed);
        self.last_reset.store(Self::current_timestamp(), Ordering::Relaxed);
    }
}

impl Default for RelayMetrics {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricsSnapshot {
    pub timestamp: u64,
    pub bytes_sent: u64,
    pub bytes_received: u64,
    pub sent_bps: f64,
    pub recv_bps: f64,
    pub active_connections: u64,
    pub total_connections: u64,
    pub messages_forwarded: u64,
    pub avg_block_size: u64,
    pub total_data_transferred: u64,
    pub top_peers: Vec<(String, PeerStats)>,
}

// Global metrics instance
use std::sync::LazyLock;
pub static METRICS: LazyLock<RelayMetrics> = LazyLock::new(RelayMetrics::new);

/// RAII Guard for connection tracking
/// Increments active_connections on creation, decrements on drop.
#[derive(Debug)]
pub struct ConnectionGuard;

impl ConnectionGuard {
    pub fn new() -> Self {
        METRICS.increment_connections();
        Self
    }
}

impl Drop for ConnectionGuard {
    fn drop(&mut self) {
        METRICS.decrement_connections();
    }
}

// End of file
