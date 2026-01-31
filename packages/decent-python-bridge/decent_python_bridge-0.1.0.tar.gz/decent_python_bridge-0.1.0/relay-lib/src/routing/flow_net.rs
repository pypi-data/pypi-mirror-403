use crate::dht::dht::Node;
use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap};

#[derive(Clone, Debug, PartialEq, Eq)]
struct State {
    cost: u64,
    node: String,
}

impl Ord for State {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse for min-heap
        other.cost.cmp(&self.cost)
            .then_with(|| self.node.cmp(&other.node))
    }
}

impl PartialOrd for State {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Debug)]
pub struct FlowNetwork {
    // Adjacency list: Source -> Vec<(Target, Capacity/BPS, Latency)>
    // Actually we can just store Nodes and assume full mesh or use DHT known nodes?
    // For now, let's assume we build the graph from known nodes (e.g. from DHT bucket).
    // We represent the graph explicitly for pathfinding.
    // Adjacency list: Source -> Vec<(Target, Capacity/BPS, Latency)>
    // Adjacency list: Source -> Vec<(Target, Capacity/BPS, Latency)>
    pub adj: HashMap<String, Vec<(String, u64, u64)>>, // Target ID, BPS, Latency
    pub nodes: HashMap<String, Node>, 
}

impl FlowNetwork {
    pub fn new() -> Self {
        FlowNetwork {
            adj: HashMap::new(),
            nodes: HashMap::new(),
        }
    }

    pub fn update_node(&mut self, node: &Node) {
        self.nodes.insert(node.id.clone(), node.clone());
    }

    pub fn is_relay(&self, id: &str) -> bool {
        self.nodes.get(id).map(|n| n.is_relay()).unwrap_or(false)
    }

    pub fn is_routable(&self, id: &str) -> bool {
        if let Some(node) = self.nodes.get(id) {
            !node.ip.is_empty() && node.ip != "0.0.0.0" && node.port != 0
        } else {
            false
        }
    }

    pub fn remove_node(&mut self, id: &str) {
        self.nodes.remove(id);
        self.adj.remove(id);
        // Remove edges where this node is the target
        for neighbors in self.adj.values_mut() {
            neighbors.retain(|(target, _, _)| target != id);
        }
    }

    pub fn add_edge(&mut self, source: &str, target: &str, bps: u64, latency_ms: u64) {
        self.adj.entry(source.to_string())
            .or_default()
            .push((target.to_string(), bps, latency_ms));
    }

    /// Finds the path with the lowest latency that satisfies min_bps.
    pub fn calculate_path(&self, source: &str, target: &str, min_bps: u64) -> Option<Vec<String>> {
        let mut dist: HashMap<String, u64> = HashMap::new();
        let mut heap = BinaryHeap::new();
        let mut prev: HashMap<String, String> = HashMap::new();

        // Initialize
        dist.insert(source.to_string(), 0);
        heap.push(State { cost: 0, node: source.to_string() });

        while let Some(State { cost, node }) = heap.pop() {
            if node == target {
                // Reconstruct path
                let mut path = Vec::new();
                let mut current = target.to_string();
                while let Some(p) = prev.get(&current) {
                    path.push(current.clone());
                    current = p.clone();
                }
                path.push(source.to_string());
                path.reverse();
                return Some(path);
            }

            if cost > *dist.get(&node).unwrap_or(&u64::MAX) {
                continue;
            }

            // Explore neighbors
            if let Some(neighbors) = self.adj.get(&node) {
                for (neighbor, edge_bps, edge_latency) in neighbors {
                    // Check if neighbor is routable (has IP)
                    if !self.is_routable(neighbor) {
                        continue;
                    }
                    if *edge_bps >= min_bps {
                        let next_cost = cost + edge_latency;
                        if next_cost < *dist.get(neighbor).unwrap_or(&u64::MAX) {
                            heap.push(State { cost: next_cost, node: neighbor.clone() });
                            dist.insert(neighbor.clone(), next_cost);
                            prev.insert(neighbor.clone(), node.clone());
                        }
                    }
                }
            }
        }

        None
    }
    pub fn get_all_nodes(&self) -> Vec<String> {
        let mut nodes = std::collections::HashSet::new();
        for (source, targets) in &self.adj {
            nodes.insert(source.clone());
            for (target, _, _) in targets {
                nodes.insert(target.clone());
            }
        }
        nodes.into_iter().collect()
    }

    pub fn get_all_relays(&self) -> Vec<Node> {
        self.nodes.values()
            .filter(|n| n.is_relay())
            .cloned()
            .collect()
    }

    /// Selects a neighbor based on score = BPS / (Latency + 1).
    /// Uses weighted random selection to balance load vs performance.
    pub fn get_weighted_neighbor(&self, node_id: &str) -> Option<Node> {
        use rand::prelude::SliceRandom;
        let mut rng = rand::thread_rng();

        if let Some(neighbors) = self.adj.get(node_id) {
            // Filter routable relays
            let candidates: Vec<(&String, u64, u64)> = neighbors.iter()
                .filter(|(tid, _, _)| self.is_relay(tid) && self.is_routable(tid))
                .map(|(tid, bps, lat)| (tid, *bps, *lat))
                .collect();

            if candidates.is_empty() {
                return None;
            }

            // Calculate scores and choose
            // Score = BPS / (Latency_ms + 1)
            // Add 1 to latency to avoid division by zero and handle 0ms nicely.

            // Weighted choice
            if let Ok(choice) = candidates.choose_weighted(&mut rng, |item| {
                let score = (item.1 as f64) / ((item.2 as f64) + 1.0);
                // Ensure non-zero weight for probability
                if score <= 0.0 { 0.0001 } else { score }
            }) {
                return self.nodes.get(choice.0).cloned();
            }
        }
        None
    }

    /// Selects a relay from all known nodes based on bandwidth (BPS).
    /// Used for hops where we don't know the direct latency (2nd hop onwards).
    pub fn get_weighted_global_relay(&self, exclude: &[String]) -> Option<Node> {
        use rand::prelude::SliceRandom;
        let mut rng = rand::thread_rng();
        use std::collections::HashSet;

        let exclude_set: HashSet<&String> = exclude.iter().collect();

        let candidates: Vec<&Node> = self.nodes.values()
            .filter(|n| n.is_relay() && self.is_routable(&n.id) && !exclude_set.contains(&n.id))
            .collect();

        if candidates.is_empty() {
            return None;
        }

        // Weighted by BPS
        // If BPS is 0 (unknown), assume a small baseline to allow selection
        if let Ok(choice) = candidates.choose_weighted(&mut rng, |n| {
            if n.bps > 0 { n.bps as f64 } else { 1024.0 } // 1KB baseline
        }) {
            Some((*choice).clone())
        } else {
            // Fallback to uniform random if weights fail (e.g. all 0?? shouldn't happen with baseline)
            candidates.choose(&mut rng).map(|n| (*n).clone())
        }
    }
}


