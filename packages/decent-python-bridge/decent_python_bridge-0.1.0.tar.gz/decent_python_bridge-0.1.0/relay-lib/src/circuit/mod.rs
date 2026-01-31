use crate::config::NetworkConfig;
use crate::dht::dht::Node;
use dashmap::DashMap;
use rand::Rng;
// Added DashMap
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, RwLock};
use std::time::Instant;
use tracing::{debug, info, warn};
// Added warn
use uuid::Uuid;

#[derive(Clone, Debug)]
pub struct CircuitId(pub String);

#[derive(Debug, Default, Clone)]
pub struct PerfStats {
    pub lookup_us: u128,
    pub send_us: u128,
    pub route_type: &'static str,
}

impl CircuitId {
    pub fn new() -> Self {
        CircuitId(Uuid::new_v4().to_string())
    }
}

impl std::fmt::Display for CircuitId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

#[derive(Clone, Debug)]
pub struct Circuit {
    pub id: CircuitId,
    pub path: Vec<Node>,
    pub created_at: Instant,
    pub used_blocks: u64,
    pub max_blocks: u64,
    pub verified: bool, // Added verified field
}

use crate::routing::flow_net::FlowNetwork;
// Node already imported at top

#[derive(Clone)]
pub enum VerificationTransport {
    PeerPool(crate::transport::PeerPool),
    SingleConnection(Arc<crate::transport::QuicClient>),
}

#[derive(Debug)]
pub struct CircuitManager {
    circuits: Arc<RwLock<Vec<Circuit>>>,
    config: Arc<NetworkConfig>,
    pub flow_net: Arc<RwLock<FlowNetwork>>, // Shared routing table
    pub pending_verifications: Arc<DashMap<String, tokio::sync::oneshot::Sender<()>>>, // Verification map
    pub min_hops: AtomicUsize,
    pub max_hops: AtomicUsize,
}

impl CircuitManager {
    pub fn new(config: Arc<NetworkConfig>) -> Self {
        CircuitManager {
            circuits: Arc::new(RwLock::new(Vec::new())),
            config,
            flow_net: Arc::new(RwLock::new(FlowNetwork::new())),
            pending_verifications: Arc::new(DashMap::new()),
            min_hops: AtomicUsize::new(1),
            max_hops: AtomicUsize::new(3),
        }
    }

    pub fn set_hop_range(&self, min: usize, max: usize) {
        let actual_min = min.max(1);
        let actual_max = max.max(actual_min);
        self.min_hops.store(actual_min, Ordering::SeqCst);
        self.max_hops.store(actual_max, Ordering::SeqCst);
        info!("CircuitManager: Updated hop range to {} - {}", actual_min, actual_max);
    }

    pub fn get_random_circuit_to(&self, target_id: &str) -> Option<CircuitId> {
        let circuits = self.circuits.read().unwrap();

        // Filter for circuits that specifically terminate at target_id
        let candidates: Vec<&Circuit> = circuits.iter()
            .filter(|c| c.path.last().map(|n| n.id.as_str()) == Some(target_id))
            .collect();

        use rand::seq::SliceRandom;
        let mut rng = rand::thread_rng();

        candidates.choose(&mut rng).map(|c| c.id.clone())
    }

    // Attempt to build a new circuit using routing logic
    pub fn build_circuit_to(&self, source_id: &str, target_id: &str) -> Option<CircuitId> {
        let min_bps = (self.config.routing.min_required_bps) as u64;
        let flow_net = self.flow_net.read().unwrap();

        if let Some(path_ids) = flow_net.calculate_path(source_id, target_id, min_bps) {
            // Look up Nodes from FlowNetwork
            let mut path: Vec<Node> = Vec::new();
            for id in path_ids {
                if let Some(node) = flow_net.nodes.get(&id) {
                    if !flow_net.is_routable(&id) {
                        return None; // Ensure every hop is routable
                    }
                    path.push(node.clone());
                } else {
                    return None; // Missing node info, cannot build valid circuit
                }
            }

            if !path.is_empty() {
                return Some(self.add_circuit(path));
            }
        }
        None
    }

    pub fn get_circuit(&self, id: &CircuitId) -> Option<Vec<Node>> {
        let circuits = self.circuits.read().unwrap();
        circuits.iter().find(|c| c.id.0 == id.0).map(|c| c.path.clone())
    }

    pub fn add_circuit(&self, path: Vec<Node>) -> CircuitId {
        // Check for duplicate circuits (same path)
        {
            let circuits = self.circuits.read().unwrap();
            for existing in circuits.iter() {
                // Compare paths by node IDs
                if existing.path.len() == path.len() {
                    let same_path = existing.path.iter()
                        .zip(path.iter())
                        .all(|(a, b)| a.id == b.id);

                    if same_path {
                        debug!("Circuit with identical path already exists: {}", existing.id);
                        return existing.id.clone();
                    }
                }
            }
        }

        let id = CircuitId::new();
        let relay_count = path.len().saturating_sub(1);
        info!("Adding new circuit {} with {} relays", id, relay_count);
        let state = Circuit {
            id: id.clone(),
            path,
            created_at: Instant::now(),
            used_blocks: 0,
            max_blocks: 5000, // Configurable
            verified: false,
        };
        self.circuits.write().unwrap().push(state);
        id
    }

    pub fn remove_circuit(&self, id: &CircuitId) {
        let mut circuits = self.circuits.write().unwrap();
        circuits.retain(|c| c.id.0 != id.0);
        info!("Removed circuit {}", id);
    }

    pub fn remove_circuits_with_node(&self, node_id: &str) {
        let mut circuits = self.circuits.write().unwrap();
        let before = circuits.len();
        circuits.retain(|c| !c.path.iter().any(|n| n.id == node_id));
        let removed = before - circuits.len();
        if removed > 0 {
            info!("Removed {} circuits containing dead node {}", removed, node_id);
        }
    }

    pub fn check_verification(&self, data: &[u8]) -> bool {
        // data payload format: "CIRCUIT_VERIFY:<UUID>"
        if let Ok(s) = std::str::from_utf8(data) {
            if s.starts_with("CIRCUIT_VERIFY:") {
                let id = s.trim_start_matches("CIRCUIT_VERIFY:");
                if let Some((_, sender)) = self.pending_verifications.remove(id) {
                    let _ = sender.send(());
                    return true;
                }
            }
        }
        false
    }

    pub async fn verify_circuit_loopback(&self, circuit_id: CircuitId, transport: VerificationTransport, relay_sk: crate::crypto::asymmetric::SigningKey, local_node: Node) {
        let path = {
            let circuits = self.circuits.read().unwrap();
            if let Some(c) = circuits.iter().find(|c| c.id.0 == circuit_id.0) {
                c.path.clone()
            } else {
                return;
            }
        };

        if path.len() < 2 { return; } // Local or 1-hop?

        // Construct loopback path: [Me, R1, ... Rn, Me]
        let mut loopback_path = path.clone();
        loopback_path.push(local_node.clone());

        // Generate ID
        let verify_id = Uuid::new_v4().to_string();
        let payload = format!("CIRCUIT_VERIFY:{}", verify_id);
        
        let (tx, rx) = tokio::sync::oneshot::channel();
        self.pending_verifications.insert(verify_id.clone(), tx);

        // Build Onion
        use crate::api::packager::Packager;
        use crate::block::block::Block;
        use crate::pow::difficulty::Difficulty;
        
        let seed = circuit_id.0.as_bytes(); 

        if let Ok(route_layers) = self.build_onion_route(&loopback_path, Some(seed)) {
            let relay_pk_str = crate::crypto::asymmetric::AsymCrypt::verifying_key_to_string(&relay_sk.verifying_key());
            let block = Block::new(0, vec![0; 32], Difficulty::default(), route_layers, payload.into_bytes(), relay_pk_str);

            // DO NOT remove the first route entry. 
            // The first entry is for the first hop (path[1]), which we are sending to.
            // If we remove it, the first hop cannot decrypt its instruction.


            // Target is path[1]
            let target = &path[1];
            let addr = format!("{}:{}", target.ip, target.port);

            if let Ok(packed) = Packager::pack(&relay_sk, &block, Some(&target.id), Some(crate::util::constants::CMD_PING as u16), false).await {
                debug!("Sending verification loopback for circuit {} to {}", circuit_id, target.id);
                // Send logic based on Transport
                match transport {
                    VerificationTransport::PeerPool(ref pool) => {
                         if let Ok(client) = pool.get_or_connect(&addr).await {
                             if let Err(e) = client.send_message(&packed, false).await {
                                 warn!("Verification send failed (PeerPool): {}", e);
                             }
                         }
                    },
                    VerificationTransport::SingleConnection(ref client) => {
                        // We must assume the SingleConnection is TO the first hop.
                        // If path[1] is NOT the connected relay, this will fail unless we tunnel.
                        // But for client, path[1] IS the home relay usually.
                        if let Err(e) = client.send_message(&packed, false).await {
                            warn!("Verification send failed (SingleConn): {}", e);
                        }
                    }
                }
                
            }
        }

        // Wait for response
        if let Err(_) = tokio::time::timeout(std::time::Duration::from_secs(5), rx).await {
            warn!("Circuit {} verification FAILED (timeout). Destroying.", circuit_id);
            self.remove_circuit(&circuit_id);
            self.pending_verifications.remove(&verify_id);
        } else {
            info!("Circuit {} verification SUCCESS.", circuit_id);
            // Mark verified
            let mut circuits = self.circuits.write().unwrap();
            if let Some(c) = circuits.iter_mut().find(|c| c.id.0 == circuit_id.0) {
                c.verified = true;
            }
        }
    }


    pub async fn maintain_circuits(&self, local_id: &str, transport: VerificationTransport, relay_sk: crate::crypto::asymmetric::SigningKey) {
        // 1. Remove expired
        {
            let mut circuits = self.circuits.write().unwrap();
            circuits.retain(|c| c.used_blocks < c.max_blocks);
        }

        // 2. Check distribution of ACTIVE circuits
        let circuits = self.get_active_circuits();
        let total = circuits.len();
        if total > 0 {
            debug!("maintain_circuits: total active circuits = {}", total);
        } else {
            info!("maintain_circuits: No active circuits, initiating creation.");
        }

        let count_with_relays = |n: usize| circuits.iter().filter(|c| c.path.len().saturating_sub(1) == n).count();

        let relays_1 = count_with_relays(1);
        let relays_2 = count_with_relays(2);

        let mut needed_circuits = Vec::new(); // List of hop_counts to create

        if total < 3 {
             // Aggressive fill
            let mut current_total = total;
            while current_total < 3 {
                let r1 = relays_1 + needed_circuits.iter().filter(|&&h| h == 1).count();
                let r2 = relays_2 + needed_circuits.iter().filter(|&&h| h == 2).count();

                let min = self.min_hops.load(Ordering::SeqCst);
                let max = self.max_hops.load(Ordering::SeqCst);

                if r1 < 1 && min <= 1 { needed_circuits.push(1); } else if r2 < 2 && min <= 2 && max >= 2 { needed_circuits.push(2); } else {
                    needed_circuits.push(rand::thread_rng().gen_range(min..=max));
                }
                current_total += 1;
            }
        } else if total < 10 {
            use rand::Rng;
            let mut rng = rand::thread_rng();
            let min = self.min_hops.load(Ordering::SeqCst);
            let max = self.max_hops.load(Ordering::SeqCst);
            
            let coin = rng.gen_range(0..10);
            if coin < 1 && relays_1 < 1 && min <= 1 { needed_circuits.push(1); } else if coin < 3 && relays_2 < 2 && min <= 2 && max >= 2 { needed_circuits.push(2); } else { needed_circuits.push(rng.gen_range(min..=max)); }
        }

        // Fetch local_node once for verification
        let local_node = {
            let flow = self.flow_net.read().unwrap();
             if let Some(n) = flow.nodes.get(local_id) {
                Some(n.clone())
            } else {
                None
            }
        };

        for hops in needed_circuits {
            if let Some(id) = self.create_circuit(local_id, hops) {
                 if let Some(node) = &local_node {
                     self.verify_circuit_loopback(id, transport.clone(), relay_sk.clone(), node.clone()).await;
                 }
            }
        }
    }

    fn create_circuit(&self, local_id: &str, hops: usize) -> Option<CircuitId> {
        let flow_net = self.flow_net.read().unwrap();
        let all_relays_count = flow_net.get_all_relays().len();

        if all_relays_count == 0 {
            info!("create_circuit: No relays in FlowNetwork, cannot build circuit.");
            return None;
        }
        debug!("create_circuit: building {}-hop path for {}, available relays={}", hops, local_id, all_relays_count);

        let mut chosen = Vec::new();
        // Track visited IDs to avoid loops
        let mut visited_ids = Vec::new();
        visited_ids.push(local_id.to_string());

        // Source Node
        if let Some(local_node) = flow_net.nodes.get(local_id) {
            chosen.push(local_node.clone());
        } else {
            // Fallback if local node not in flow net yet (e.g. startup)
            chosen.push(Node::new(local_id.to_string(), "0.0.0.0".to_string(), 0, 0));
        }

        // Selected Hops
        let mut current_id = local_id.to_string();

        for i in 0..hops {
            let next_node = if i == 0 {
                // First Hop: Use Weighted Neighbor Selection (Optimize Latency/BPS)
                // This is the most critical hop for entry.
                flow_net.get_weighted_neighbor(&current_id)
                    .or_else(|| {
                        // Fallback to global weighted if no direct neighbors
                        debug!("create_circuit: No weighted neighbors for first hop, falling back to global.");
                        flow_net.get_weighted_global_relay(&visited_ids)
                    })
            } else {
                // Subsequent Hops: Use Global Weighted Selection (Optimize BPS)
                // We assume high-BPS nodes are good relays.
                flow_net.get_weighted_global_relay(&visited_ids)
            };

            if let Some(node) = next_node {
                visited_ids.push(node.id.clone());
                current_id = node.id.clone();
                chosen.push(node);
            } else {
                warn!("create_circuit: Failed to find suitable relay for hop {}/{}", i + 1, hops);
                break;
            }
        }

        // Only create circuit if we successfully selected all requested hops (plus source)
        if chosen.len() == hops + 1 {
            Some(self.add_circuit(chosen))
        } else {
            None
        }
    }

    pub async fn relay(&self, target_id: &str, data: &[u8], peer_pool: &crate::transport::PeerPool, local_id: Option<&str>) -> anyhow::Result<PerfStats> {
        let start_lookup = Instant::now();
        let mut stats = PerfStats { lookup_us: 0, send_us: 0, route_type: "Unknown" };

        // 1. Try direct connection reuse first (Crucial for NAT)
        if let Some(client) = peer_pool.get_by_id(target_id) {
            stats.lookup_us = start_lookup.elapsed().as_micros();
            stats.route_type = "Direct";
            // debug!("RELAY: Found direct connection to {}, attempting send...", &target_id[..target_id.len().min(16)]);

            let start_send = Instant::now();
            match client.send_message(data, false).await {
                Ok(_) => {
                    stats.send_us = start_send.elapsed().as_micros();
                    // debug!("RELAY: Direct send SUCCESS to {}", &target_id[..target_id.len().min(16)]);
                    return Ok(stats);
                }
                Err(e) => {
                    info!("Direct send to {} failed ({}), retrying with fresh connection...", target_id, e);
                    peer_pool.remove_peer(target_id);
                    // Try to recover address from FlowNet to reconnect
                    let addr_opt = if let Ok(flow) = self.flow_net.read() {
                        flow.nodes.get(target_id).map(|n| format!("{}:{}", n.ip, n.port))
                    } else { None };

                    if let Some(addr) = addr_opt {
                        // CRITICAL: Prevent connecting to 0.0.0.0
                        if addr.starts_with("0.0.0.0") || addr.contains(":0") {
                            return Err(anyhow::anyhow!("Refusing to connect to unroutable target address: {}", addr));
                        }
                        peer_pool.remove_by_addr(&addr);
                        if let Ok(new_client) = peer_pool.get_or_connect(&addr).await {
                            let start_send_retry = Instant::now();
                            new_client.send_message(data, false).await?;
                            stats.send_us = start_send_retry.elapsed().as_micros();
                            stats.route_type = "Direct (Retry)";
                            return Ok(stats);
                        }
                    }
                }
            }
        } else {
            warn!("RELAY: Target {} NOT found in peer_pool, trying circuits...", &target_id[..target_id.len().min(16)]);
        }

        // 2. Fallback to routing logic (Circuits)
        if let Some(circuit_id) = self.get_random_circuit_to(target_id) {
            if let Some(path) = self.get_circuit(&circuit_id) {
                if path.len() > 1 {
                    let next_hop = &path[1];
                    if next_hop.ip == "0.0.0.0" || next_hop.port == 0 {
                        return Err(anyhow::anyhow!("Invalid next hop addr in circuit"));
                    }
                    let addr = format!("{}:{}", next_hop.ip, next_hop.port);

                    stats.lookup_us = start_lookup.elapsed().as_micros();
                    stats.route_type = "Circuit";

                    // Check if specific connection exists or connect
                    match peer_pool.get_or_connect(&addr).await {
                        Ok(client) => {
                            let start_send = Instant::now();
                            match client.send_message(data, false).await {
                                Ok(_) => {
                                    stats.send_us = start_send.elapsed().as_micros();
                                    return Ok(stats);
                                },
                                Err(_) => {
                                    // Retry once
                                    peer_pool.remove_by_addr(&addr);
                                    if let Ok(new_client) = peer_pool.get_or_connect(&addr).await {
                                        let start_send_retry = Instant::now();
                                        new_client.send_message(data, false).await?;
                                        stats.send_us = start_send_retry.elapsed().as_micros();
                                        return Ok(stats);
                                    }
                                }
                            }
                        },
                        Err(_) => {} // Fallthrough
                    }
                }
            }
        }

        // 3. Fallback to FlowNet (Ad-Hoc / Shortest Path)
        if let Some(local) = local_id {
            let next_hop_node = {
                if let Ok(flow) = self.flow_net.read() {
                    let min_bps = (self.config.routing.min_required_bps) as u64;
                    if let Some(path) = flow.calculate_path(local, target_id, min_bps) {
                        if path.len() > 1 {
                            flow.nodes.get(&path[1]).cloned()
                        } else { None }
                    } else { None }
                } else { None }
            };

            if let Some(next_hop) = next_hop_node {
                if next_hop.ip == "0.0.0.0" || next_hop.port == 0 {
                    return Err(anyhow::anyhow!("Ad-hoc next hop has invalid address: {}:{}", next_hop.ip, next_hop.port));
                }

                stats.lookup_us = start_lookup.elapsed().as_micros();
                stats.route_type = "AdHoc";
                
                let addr = format!("{}:{}", next_hop.ip, next_hop.port);
                let client_res = peer_pool.get_or_connect(&addr).await;
                match client_res {
                    Ok(client) => {
                        let start_send = Instant::now();
                         match client.send_message(data, false).await {
                             Ok(_) => {
                                 stats.send_us = start_send.elapsed().as_micros();
                                 return Ok(stats);
                             },
                            Err(_) => {
                                // Retry once
                                peer_pool.remove_by_addr(&addr);
                                if let Ok(new_client) = peer_pool.get_or_connect(&addr).await {
                                    let start_send_retry = Instant::now();
                                    new_client.send_message(data, false).await?;
                                    stats.send_us = start_send_retry.elapsed().as_micros();
                                    return Ok(stats);
                                }
                            }
                        }
                    },
                    Err(_) => {}
                }
            }
        }

        Err(anyhow::anyhow!("No route to target {}", target_id))
    }

    pub fn get_active_circuits(&self) -> Vec<Circuit> {
        self.circuits.read().unwrap().clone()
    }

    pub fn record_usage(&self, id: &CircuitId) {
        let mut circuits = self.circuits.write().unwrap();
        if let Some(c) = circuits.iter_mut().find(|c| c.id.0 == id.0) {
            c.used_blocks += 1;
        }
        // Rotation check logic to be added
    }

    pub fn build_onion_route(&self, path: &[Node], seed: Option<&[u8]>) -> Result<Vec<Vec<u8>>, String> {
        if path.len() < 2 {
            // 1-hop circuit (Direct) -> Empty route vector? 
            // Or if path is [Me, Target], then route is empty because Target is next hop?
            // Requirement says: "Eva -> Adam -> Nick -> Target"
            // "Take Adam_pub (next after Eva). Encrypt using Eva_pub_enc."
            // "Send block to first relay (Eva)."

            // Path: [Source(Me), Rel1, Rel2, Target]
            // Hops: Rel1, Rel2, Target.
            // Relay 1 needs to know about Relay 2.
            // Relay 2 needs to know about Target.
            // Target is final.

            // If path is just [Me, Target], sending to Target directly.
            // Target receives it. No forwarding needed. Route len 0?
            // Protocol: "Relay forwarded blocks only if they belong to an active circuit."
            // If direct, route is empty.
            if path.len() <= 2 {
                return Ok(Vec::new());
            }
        }

        let mut route_entries = Vec::new();

        use crate::crypto::asymmetric::AsymCrypt;


        // Path: [Source, H1, H2, ..., Target]
        // H1 needs H2's ID. Encrypted with H1's Key.
        // H2 needs H3's ID. Encrypted with H2's Key.
        // ...
        // H_last-1 needs Target's ID. Encrypted with H_last-1's Key.

        // Iterate from index 1 (First Hop) to len-2.
        // i = 1 (H1). Next = path[2] (H2).

        let should_be_deterministic = seed.is_some();
        let base_seed = seed.unwrap_or(&[]);

        for i in 1..path.len() - 1 {
            let current_hop = &path[i];
            let next_hop = &path[i + 1];

            // Encrypt next_hop.id (Public Key) using current_hop.id (As Encryption Key)
            // We need current_hop's Encryption Public Key.
            // Assuming Node.id IS the Public Key (Ed25519). 
            // We convert Ed25519 Pub -> X25519 Pub for encryption.

            let current_pk_ed = AsymCrypt::verifying_key_from_string(&current_hop.id)
                .map_err(|e| format!("Invalid ID for {}: {}", current_hop.id, e))?;

            let next_hop_bytes = AsymCrypt::public_key_from_base64(&next_hop.id, false)
                .map_err(|e| format!("Invalid ID for {}: {}", next_hop.id, e))?;

            // Encrypt next_hop_bytes for current_hop using Simple Asymmetric Encryption interface
            let encrypted = if should_be_deterministic {
                let mut hop_seed = base_seed.to_vec();
                hop_seed.extend_from_slice(&(i as u64).to_le_bytes());
                AsymCrypt::encrypt_asymmetric_deterministic(&current_pk_ed, &next_hop_bytes, &hop_seed)?
            } else {
                AsymCrypt::encrypt_asymmetric(&current_pk_ed, &next_hop_bytes)?
            };

            // println!("DEBUG: build_onion_route: Added entry for hop {} -> {}, len={}", current_hop.id, next_hop.id, encrypted.len());
            route_entries.push(encrypted);
        }

        let count = route_entries.len();
        // Do not shuffle. Keep strictly ordered for deterministic debugging.
        // route_entries.shuffle(&mut rng);

        if count != route_entries.len() {
            return Err("Shuffle lost entries?".to_string());
        }
        // println!("DEBUG: build_onion_route: Generated {} entries for path len {}", count, path.len());

        Ok(route_entries)
    }
}


