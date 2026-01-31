use crate::transport::quic::make_client_config;
use anyhow::Result;
use quinn::{Connection, Endpoint, RecvStream, SendStream};
use std::net::SocketAddr;
use tracing::debug;
use crate::metrics::METRICS;

#[derive(Clone, Debug)]
pub struct QuicClient {
    endpoint: Endpoint,
    connection: Option<Connection>,
    _guard: Option<std::sync::Arc<crate::metrics::ConnectionGuard>>,
}

impl QuicClient {
    pub fn new() -> Result<Self> {
        // Try to bind IPv6 (dual-stack) first, then fallback to IPv4
        let bind_addr_v6: SocketAddr = "[::]:0".parse().unwrap();
        let bind_addr_v4: SocketAddr = "0.0.0.0:0".parse().unwrap();

        let endpoint = match Endpoint::client(bind_addr_v6) {
            Ok(mut ep) => {
                ep.set_default_client_config(make_client_config());
                ep
            },
            Err(_) => {
                debug!("IPv6 bind failed, falling back to IPv4");
                let mut ep = Endpoint::client(bind_addr_v4)?;
                ep.set_default_client_config(make_client_config());
                ep
            }
        };
        
        Ok(QuicClient { endpoint, connection: None, _guard: None })
    }

    pub fn set_connection(&mut self, conn: Connection) {
        self.connection = Some(conn);
        self._guard = Some(std::sync::Arc::new(crate::metrics::ConnectionGuard::new()));
    }

    pub fn connection(&self) -> Option<Connection> {
        self.connection.clone()
    }

    pub fn from_endpoint(endpoint: Endpoint) -> Self {
        // Assume endpoint already has client config or we set it?
        // Ideally we should ensure client config is set. 
        // But if sharing server endpoint, server endpoint might not have client config set default?
        // We can set it if missing, but better to assume caller handled it or we set it safely.
        // For now, simple construction.
        QuicClient { endpoint, connection: None, _guard: None }
    }

    pub async fn connect(&mut self, addr: &str) -> Result<()> {
        let addrs = tokio::net::lookup_host(addr).await?;
        let mut last_err = None;

        for socket_addr in addrs {
            debug!("QuicClient connecting to resolved IP: {}...", socket_addr);
            match self.endpoint.connect(socket_addr, "relay") {
                Ok(connecting) => {
                    match connecting.await {
                        Ok(conn) => {
                            debug!("QuicClient connection established with {}", socket_addr);
                            self.connection = Some(conn);
                            self._guard = Some(std::sync::Arc::new(crate::metrics::ConnectionGuard::new()));
                            return Ok(());
                        }
                        Err(e) => {
                            debug!("Failed to handshake with {}: {}", socket_addr, e);
                            last_err = Some(e.into());
                        }
                    }
                }
                Err(e) => {
                    debug!("Failed to connect endpoint to {}: {}", socket_addr, e);
                    last_err = Some(e.into());
                }
            }
        }

        Err(last_err.unwrap_or_else(|| anyhow::anyhow!("Could not connect to any address for {}", addr)))
    }

    pub async fn accept_uni(&self) -> Result<RecvStream> {
        if let Some(conn) = &self.connection {
            let recv = conn.accept_uni().await?;
            Ok(recv)
        } else {
            use anyhow::anyhow;
            Err(anyhow!("Not connected"))
        }
    }

    pub async fn accept_bi(&self) -> Result<(SendStream, RecvStream)> {
        if let Some(conn) = &self.connection {
            let (send, recv) = conn.accept_bi().await?;
            Ok((send, recv))
        } else {
            use anyhow::anyhow;
            Err(anyhow!("Not connected"))
        }
    }

    pub async fn open_bi(&self) -> Result<(SendStream, RecvStream)> {
        if let Some(conn) = &self.connection {
            let (send, recv) = conn.open_bi().await?;
            Ok((send, recv))
        } else {
            use anyhow::anyhow;
            Err(anyhow!("Not connected"))
        }
    }

    pub async fn open_uni(&self) -> Result<SendStream> {
        if let Some(conn) = &self.connection {
            let send = conn.open_uni().await?;
            Ok(send)
        } else {
            use anyhow::anyhow;
            Err(anyhow!("Not connected"))
        }
    }

    pub async fn send_message(&self, data: &[u8], wait_for_response: bool) -> Result<Option<Vec<u8>>> {
        if wait_for_response {
            let (mut send, mut recv) = self.open_bi().await?;
            send.write_all(data).await?;
            METRICS.record_bytes_sent(data.len()); // Instrument sent
            send.finish()?;

            let buf = recv.read_to_end(10 * 1024 * 1024).await?;
            METRICS.record_bytes_received(buf.len()); // Instrument recv
            if buf.is_empty() {
                Ok(None)
            } else {
                Ok(Some(buf))
            }
        } else {
            let mut send = self.open_uni().await?;
            send.write_all(data).await?;
            METRICS.record_bytes_sent(data.len()); // Instrument sent
            send.finish()?;
            Ok(None)
        }
    }

    pub fn close(&self) {
        if let Some(conn) = &self.connection {
            conn.close(0u32.into(), b"closed");
        }
    }

    pub fn close_reason(&self) -> Option<quinn::ConnectionError> {
        self.connection.as_ref().and_then(|c| c.close_reason())
    }
}
