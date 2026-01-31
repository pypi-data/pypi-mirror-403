use sled::Db;
use std::path::Path;
use tracing::{error, info};

#[derive(Clone)]
pub struct PeerStore {
    db: Db,
}

impl PeerStore {
    /// Opens or creates a PeerStore at the given path.
    pub fn new<P: AsRef<Path>>(path: P) -> Result<Self, sled::Error> {
        let db = sled::open(path)?;
        info!("PeerStore opened successfully.");
        Ok(Self { db })
    }

    /// Adds or updates a peer in the store.
    pub fn add_peer(&self, peer_id: &str, address: &str) -> Result<(), sled::Error> {
        self.db.insert(peer_id.as_bytes(), address.as_bytes())?;
        self.db.flush()?; // Ensure durability immediately for now
        info!("Persisted peer {} at {}", peer_id, address);
        Ok(())
    }

    /// Removes a peer from the store.
    pub fn remove_peer(&self, peer_id: &str) -> Result<(), sled::Error> {
        self.db.remove(peer_id.as_bytes())?;
        self.db.flush()?;
        Ok(())
    }

    /// Retrieves all known peers as (ID, Address) tuples.
    pub fn get_known_peers(&self) -> Vec<(String, String)> {
        let mut peers = Vec::new();
        for item in self.db.iter() {
            match item {
                Ok((k, v)) => {
                    let id = String::from_utf8(k.to_vec()).unwrap_or_default();
                    let addr = String::from_utf8(v.to_vec()).unwrap_or_default();
                    tracing::debug!("PeerStore Found: {} -> {}", id, addr);
                    if !id.is_empty() && !addr.is_empty() {
                        peers.push((id, addr));
                    }
                }
                Err(e) => {
                    error!("Error iterating PeerStore: {}", e);
                }
            }
        }
        peers
    }
}
