use crate::dht::dht::DHT;
use crate::transport::peer_pool::PeerPool;
use std::sync::{Arc, RwLock};
use tokio::time::{interval, Duration, Instant};
use tracing::{info, warn};

pub struct PingTask {
    peer_pool: PeerPool,
    dht: Arc<RwLock<DHT>>,
    interval_sec: u64,
}

impl PingTask {
    pub fn new(peer_pool: PeerPool, dht: Arc<RwLock<DHT>>, interval_sec: u64) -> Self {
        PingTask {
            peer_pool,
            dht,
            interval_sec,
        }
    }

    pub async fn start(&self) {
        let mut interval = interval(Duration::from_secs(self.interval_sec));

        loop {
            interval.tick().await;
            self.ping_peers().await;
        }
    }

    async fn ping_peers(&self) {
        // Collect peers from DHT
        let peers = {
            let dht = self.dht.read().unwrap();
            dht.get_all_nodes() // Need to implement this in DHT
        };

        for node in peers {
            let start = Instant::now();
            let addr = format!("{}:{}", node.ip, node.port);

            match self.peer_pool.get_or_connect(&addr).await {
                Ok(client) => {
                    // Send Ping
                    // We need a Ping message format.
                    // For now, sending dummy bytes or "PING"
                    match client.send_message(b"PING", true).await {
                        Ok(Some(_response)) => {
                            let rtt = start.elapsed().as_millis() as u64;
                            // Estimate BPS? 
                            // Quic provides stats? 
                            // client.endpoint.stats() ?
                            // For now, just update latency.

                            info!("Ping to {} took {}ms", node.id, rtt);

                            let mut dht = self.dht.write().unwrap();
                            // Update Node stats
                            // We need a method in DHT to update metrics
                            dht.update_metrics(&node.id, rtt, 10_000_000); // 10Mbps dummy
                        }
                        Ok(None) => warn!("No pong from {}", node.id),
                        Err(e) => warn!("Ping failed to {}: {}", node.id, e),
                    }
                }
                Err(e) => warn!("Failed to connect to {}: {}", node.id, e),
            }
        }
    }
}
