use crate::transport::quic::{generate_self_signed_cert, make_server_config};
use anyhow::Result;
use quinn::{Endpoint, Incoming};
use std::net::SocketAddr;

pub struct QuicServer {
    endpoint: Endpoint,
}

impl QuicServer {
    pub async fn bind(bind_addr: &str) -> Result<Self> {
        let addr: SocketAddr = bind_addr.parse()?;
        let (certs, key) = generate_self_signed_cert(vec!["localhost".into(), "relay".into()])?;
        let server_config = make_server_config(certs, key)?;

        // Build Endpoint
        let mut endpoint = Endpoint::server(server_config, addr)?;
        endpoint.set_default_client_config(crate::transport::quic::make_client_config());

        Ok(QuicServer { endpoint })
    }

    pub async fn accept(&self) -> Option<Incoming> {
        self.endpoint.accept().await
    }

    pub fn endpoint(&self) -> Endpoint {
        self.endpoint.clone()
    }

    pub fn local_addr(&self) -> Result<SocketAddr> {
        Ok(self.endpoint.local_addr()?)
    }
}
