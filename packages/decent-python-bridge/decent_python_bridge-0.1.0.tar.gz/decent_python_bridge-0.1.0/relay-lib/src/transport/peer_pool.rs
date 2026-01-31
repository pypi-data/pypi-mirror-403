use crate::transport::quic_client::QuicClient;
use anyhow::Result;
use dashmap::DashMap;
use std::sync::Arc;
use tracing::info;

use quinn::Endpoint;

#[derive(Clone)]
pub struct PeerPool {
    peers: Arc<DashMap<String, QuicClient>>, // Addr -> Client
    id_to_client: Arc<DashMap<String, QuicClient>>, // ID -> Client
    endpoint: Endpoint,
}

impl PeerPool {
    pub fn new(endpoint: Endpoint) -> Self {
        PeerPool {
            peers: Arc::new(DashMap::new()),
            id_to_client: Arc::new(DashMap::new()),
            endpoint,
        }
    }

    pub fn endpoint(&self) -> Endpoint {
        self.endpoint.clone()
    }

    pub fn register_peer(&self, id: String, client: QuicClient) {
        info!("Registering peer {} to connection", id);
        self.id_to_client.insert(id, client);
    }

    pub fn get_by_id(&self, id: &str) -> Option<QuicClient> {
        self.id_to_client.get(id).map(|c| c.clone())
    }

    pub async fn get_or_connect(&self, addr: &str) -> Result<QuicClient> {
        if let Some(client) = self.peers.get(addr) {
            return Ok(client.clone());
        }

        info!("Connecting to peer: {}", addr);
        // Reuse endpoint
        let mut client = QuicClient::from_endpoint(self.endpoint.clone());
        client.connect(addr).await?;

        self.peers.insert(addr.to_string(), client.clone());
        Ok(client)
    }

    pub fn remove_peer(&self, id: &str) {
        self.id_to_client.remove(id);
    }

    pub fn remove_by_addr(&self, addr: &str) {
        self.peers.remove(addr);
    }
}
