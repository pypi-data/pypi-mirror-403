//! Python bindings for DecentMesh network client.
//!
//! Provides async-compatible interface for connecting to relays
//! and sending/receiving encrypted messages.

use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use std::sync::Arc;
use once_cell::sync::Lazy;
use relay_lib::crypto::asymmetric::{AsymCrypt, SigningKey};
use relay_lib::pow::policy::PowPolicy;
use relay_lib::circuit::CircuitManager;
use relay_lib::config::NetworkConfig;
use decent_client_lib::client::RelayClient;
use decent_client_lib::chat::ChatMessage;
use chrono::Local;

// Global tokio runtime for async operations
static RUNTIME: Lazy<tokio::runtime::Runtime> = Lazy::new(|| {
    tokio::runtime::Runtime::new().expect("Failed to create tokio runtime")
});

/// DecentMesh network client
#[pyclass]
pub struct DecentMeshClient {
    signing_key: Option<SigningKey>,
    connections: Vec<Arc<RelayClient>>,
    my_public_key: String,
    message_callback: Option<PyObject>,
    status_callback: Option<PyObject>,
    ready_callback: Option<PyObject>,
}

#[pymethods]
impl DecentMeshClient {
    #[new]
    fn new() -> Self {
        Self {
            signing_key: None,
            connections: Vec::new(),
            my_public_key: String::new(),
            message_callback: None,
            status_callback: None,
            ready_callback: None,
        }
    }

    /// Generate a new Ed25519 identity keypair
    fn generate_identity(&self) -> PyResult<String> {
        let keypair = AsymCrypt::generate_key_pair_signing();
        Ok(hex::encode(keypair.private.to_bytes()))
    }

    /// Get public key from private key
    fn get_public_key(&self, private_key_hex: &str) -> PyResult<String> {
        let bytes = hex::decode(private_key_hex)
            .map_err(|e| PyRuntimeError::new_err(format!("Invalid hex: {}", e)))?;
        let key_bytes: [u8; 32] = bytes.try_into()
            .map_err(|_| PyRuntimeError::new_err("Key must be 32 bytes"))?;
        let signing_key = SigningKey::from_bytes(&key_bytes);
        let verifying_key = signing_key.verifying_key();
        Ok(hex::encode(verifying_key.to_bytes()))
    }

    /// Set callbacks for events
    fn set_callbacks(
        &mut self,
        on_message: Option<PyObject>,
        on_status: Option<PyObject>,
        on_ready: Option<PyObject>,
    ) {
        self.message_callback = on_message;
        self.status_callback = on_status;
        self.ready_callback = on_ready;
    }

    /// Connect to the DecentMesh network
    fn connect(&mut self, py: Python<'_>, private_key_hex: &str, relay_addresses: Vec<String>, config_path: Option<&str>) -> PyResult<bool> {
        let bytes = hex::decode(private_key_hex)
            .map_err(|e| PyRuntimeError::new_err(format!("Invalid hex: {}", e)))?;
        let key_bytes: [u8; 32] = bytes.try_into()
            .map_err(|_| PyRuntimeError::new_err("Key must be 32 bytes"))?;
        let signing_key = SigningKey::from_bytes(&key_bytes);
        
        self.my_public_key = hex::encode(signing_key.verifying_key().to_bytes());
        self.signing_key = Some(signing_key.clone());

        // Emit status
        if let Some(ref cb) = self.status_callback {
            let _ = cb.call1(py, ("Connecting to relays...",));
        }

        // Connect to relays - load network config from file
        let pow_policy = Arc::new(PowPolicy::new());
        
        // Load network config - try provided path, then default
        let cfg_path = config_path.unwrap_or("network_config.toml");
        let network_config = NetworkConfig::load(std::path::Path::new(cfg_path))
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to load network config from {}: {}", cfg_path, e)))?;
        
        let circuit_manager = Arc::new(CircuitManager::new(Arc::new(network_config)));
        
        let mut connected = false;
        
        for addr in relay_addresses {
            if let Some(ref cb) = self.status_callback {
                let _ = cb.call1(py, (format!("Connecting to {}...", addr),));
            }
            
            let sk = SigningKey::from_bytes(&key_bytes);
            let result = RUNTIME.block_on(async {
                RelayClient::connect(&addr, sk, pow_policy.clone(), circuit_manager.clone()).await
            });
            
            match result {
                Ok((client, _quic, _cipher)) => {
                    // Announce identity
                    let announce_client = client.clone();
                    let _ = RUNTIME.block_on(async {
                        announce_client.announce_identity().await
                    });
                    
                    self.connections.push(Arc::new(client));
                    connected = true;
                    
                    if let Some(ref cb) = self.status_callback {
                        let _ = cb.call1(py, (format!("Connected to {}", addr),));
                    }
                    
                    // One connection is enough
                    break;
                }
                Err(e) => {
                    if let Some(ref cb) = self.status_callback {
                        let _ = cb.call1(py, (format!("Failed to connect to {}: {}", addr, e),));
                    }
                }
            }
        }

        if connected {
            if let Some(ref cb) = self.status_callback {
                let _ = cb.call1(py, ("Network READY",));
            }
            if let Some(ref cb) = self.ready_callback {
                let _ = cb.call0(py);
            }
        }

        Ok(connected)
    }

    /// Send a message to a target public key
    fn send_message(&self, py: Python<'_>, target_pubkey: &str, content: &str, msg_id: &str) -> PyResult<bool> {
        if self.connections.is_empty() {
            return Err(PyRuntimeError::new_err("Not connected to any relays"));
        }

        let msg = ChatMessage {
            id: msg_id.to_string(),
            sender: self.my_public_key.clone(),
            content: content.to_string(),
            timestamp: Local::now(),
            is_outgoing: true,
            acked: false,
            ack_latency: None,
        };

        let client = self.connections.first().unwrap().clone();
        let target = target_pubkey.to_string();
        
        let result = RUNTIME.block_on(async {
            client.send_message(&target, &msg, true).await
        });

        match result {
            Ok(_) => {
                if let Some(ref cb) = self.status_callback {
                    let _ = cb.call1(py, (format!("Message sent to {}", &target[..16.min(target.len())]),));
                }
                Ok(true)
            },
            Err(e) => Err(PyRuntimeError::new_err(format!("Send failed: {}", e))),
        }
    }

    /// Get connected relay count
    fn get_connected_count(&self) -> usize {
        self.connections.len()
    }

    /// Get my public key
    fn get_my_public_key(&self) -> String {
        self.my_public_key.clone()
    }

    /// Check if ready
    fn is_ready(&self) -> bool {
        !self.connections.is_empty()
    }
}

/// Python module definition
#[pymodule]
fn decent_mesh(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<DecentMeshClient>()?;
    Ok(())
}
