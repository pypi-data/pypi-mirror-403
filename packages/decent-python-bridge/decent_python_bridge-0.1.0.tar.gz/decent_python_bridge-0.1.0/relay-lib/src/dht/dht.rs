use crate::consensus::dht::{DHT_BUCKET_COUNT, DHT_K};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Node {
    pub id: String,
    pub ip: String,
    pub port: u16,
    pub last_seen: u64,
    pub bps: u64,
    pub latency_ms: u64,
    pub node_type: u8, // 0 = Client, 1 = Relay
}

impl Node {
    pub fn new(id: String, ip: String, port: u16, node_type: u8) -> Self {
        Node {
            id,
            ip,
            port,
            last_seen: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
            bps: 0,
            latency_ms: 0,
            node_type,
        }
    }

    pub fn is_relay(&self) -> bool {
        self.node_type == 1
    }
}

use crate::routing::flow_net::FlowNetwork;
use std::sync::{Arc, RwLock};

pub struct DHT {
    pub local_node: Node,
    buckets: Vec<Vec<Node>>, // Simple K-buckets implementation
    data_store: HashMap<String, String>, // Key -> Value (Relay Address)
    flow_net: Option<Arc<RwLock<FlowNetwork>>>,
}

impl DHT {
    pub fn new(local_id: String, local_ip: String, local_port: u16, node_type: u8, flow_net: Option<Arc<RwLock<FlowNetwork>>>) -> Self {
        DHT {
            local_node: Node::new(local_id, local_ip, local_port, node_type), // default to type passed
            buckets: vec![Vec::new(); DHT_BUCKET_COUNT], // 256 bits for SHA256 ID space
            data_store: HashMap::new(),
            flow_net,
        }
    }

    pub fn xor_distance(a: &[u8], b: &[u8]) -> Vec<u8> {
        a.iter().zip(b.iter()).map(|(x, y)| x ^ y).collect()
    }

    // Helper to get bucket index based on XOR distance common prefix
    fn get_bucket_index(&self, target_id: &str) -> usize {
        // Assume IDs are Base64 encoded, need to decode or treat as raw bytes?
        // For simplicity, let's treat the ID string bytes directly or assume fixed length.
        // Real Kademlia uses bit-level distance.
        // Let's rely on common prefix length of the ID string for now (simplified)
        // or better, decode base64 to bytes if the IDs are base64.

        // Assuming IDs are URL-Safe Base64 strings from AsymCrypt
        let local_bytes = self.local_node.id.as_bytes();
        let target_bytes = target_id.as_bytes();

        let mut prefix_len = 0;
        let len = local_bytes.len().min(target_bytes.len());

        for i in 0..len {
            let xor = local_bytes[i] ^ target_bytes[i];
            if xor == 0 {
                prefix_len += 8;
            } else {
                prefix_len += xor.leading_zeros() as usize;
                break;
            }
        }

        // Cap at 255
        prefix_len.min(255)
    }

    pub fn add_node(&mut self, node: Node) {
        if node.id == self.local_node.id {
            return;
        }

        let index = self.get_bucket_index(&node.id);
        let bucket = &mut self.buckets[index];

        // Check if exists
        if let Some(pos) = bucket.iter().position(|n| n.id == node.id) {
            // Update last seen (move to tail)
            let mut existing = bucket.remove(pos);
            existing.last_seen = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
            existing.bps = node.bps;
            existing.latency_ms = node.latency_ms;
            bucket.push(existing);
        } else {
            // Add if space
            if bucket.len() < DHT_K {
                bucket.push(node.clone());
            }
            // Update FlowNetwork
            if let Some(flow_net) = &self.flow_net {
                // Add edge from Us -> New Node
                let mut net = flow_net.write().unwrap();
                net.update_node(&node);
                net.add_edge(&self.local_node.id, &node.id, node.bps, node.latency_ms);
                // Assume symmetric link for now? Or wait for gossip.
                // net.add_edge(&node.id, &self.local_node.id, node.bps, node.latency_ms);
            }
        }
    }

    pub fn remove_node(&mut self, id: &str) {
        let index = self.get_bucket_index(id);
        let bucket = &mut self.buckets[index];
        bucket.retain(|n| n.id != id);

        if let Some(flow_net) = &self.flow_net {
            if let Ok(mut net) = flow_net.write() {
                net.remove_node(id);
            }
        }
    }

    pub fn find_closest_nodes(&self, target_key: &str, count: usize) -> Vec<Node> {
        let mut nodes: Vec<(Vec<u8>, Node)> = Vec::new();

        // Flatten buckets
        for bucket in &self.buckets {
            for node in bucket {
                let dist = Self::xor_distance(target_key.as_bytes(), node.id.as_bytes());
                nodes.push((dist, node.clone()));
            }
        }

        // Sort by distance
        nodes.sort_by(|a, b| a.0.cmp(&b.0));

        nodes.into_iter().take(count).map(|(_, n)| n).collect()
    }

    pub fn get_all_nodes(&self) -> Vec<Node> {
        let mut nodes = Vec::new();
        for bucket in &self.buckets {
            for node in bucket {
                nodes.push(node.clone());
            }
        }
        nodes
    }

    pub fn update_metrics(&mut self, node_id: &str, latency_ms: u64, bps: u64) {
        // Find node in buckets
        for bucket in &mut self.buckets {
            if let Some(pos) = bucket.iter().position(|n| n.id == node_id) {
                let node = &mut bucket[pos];
                node.latency_ms = latency_ms;
                node.bps = bps;
                node.last_seen = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();

                // Update FlowNetwork
                if let Some(flow_net) = &self.flow_net {
                    if let Ok(mut net) = flow_net.write() {
                        net.update_node(node);
                        net.add_edge(&self.local_node.id, node_id, bps, latency_ms);
                    }
                }
                return;
            }
        }
    }

    pub fn store(&mut self, key: String, value: String) {
        self.data_store.insert(key, value);
    }

    pub fn get(&self, key: &str) -> Option<String> {
        self.data_store.get(key).cloned()
    }
}

