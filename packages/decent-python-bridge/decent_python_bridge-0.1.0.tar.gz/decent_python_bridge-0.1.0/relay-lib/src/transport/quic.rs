use anyhow::Result;
use rustls::pki_types::{CertificateDer, PrivateKeyDer, ServerName};
use rustls::{ClientConfig, ServerConfig};
use std::sync::Arc;
use std::sync::Once;

static INIT: Once = Once::new();

pub fn init_crypto() {
    INIT.call_once(|| {
        rustls::crypto::ring::default_provider().install_default().expect("Failed to install rustls crypto provider");

    });
}

/// Generates a self-signed certificate for the relay.
/// Returns (cert_chain, private_key).
pub fn generate_self_signed_cert(names: Vec<String>) -> Result<(Vec<CertificateDer<'static>>, PrivateKeyDer<'static>)> {
    let certified_key = rcgen::generate_simple_self_signed(names)?;
    // cert.der() returns &CertificateDer. We need 'static.
    let cert_der = certified_key.cert.der().clone().into_owned();

    let priv_key_der = certified_key.key_pair.serialize_der();
    let priv_key: PrivateKeyDer = rustls::pki_types::PrivatePkcs8KeyDer::from(priv_key_der).into();

    let cert_chain = vec![cert_der];
    Ok((cert_chain, priv_key))
}

use quinn::crypto::rustls::{QuicClientConfig, QuicServerConfig};
use quinn::{ClientConfig as QuinnClientConfig, ServerConfig as QuinnServerConfig};

// ... generated cert ...

pub fn make_server_config(cert_chain: Vec<CertificateDer<'static>>, key: PrivateKeyDer<'static>) -> Result<QuinnServerConfig> {
    init_crypto();
    let mut server_crypto = ServerConfig::builder()
        .with_no_client_auth()
        .with_single_cert(cert_chain, key)?;

    server_crypto.alpn_protocols = vec![b"hq-29".to_vec()]; // Important for QUIC? Quinn defaults?
    // Actually quinn examples usually set ALPN. 

    let server_config = QuicServerConfig::try_from(server_crypto)?;
    let mut config = QuinnServerConfig::with_crypto(Arc::new(server_config));

    // Configure Transport parameters
    let mut transport_config = quinn::TransportConfig::default();
    transport_config.max_idle_timeout(Some(quinn::VarInt::from_u32(60000).into())); // 60s
    transport_config.keep_alive_interval(Some(std::time::Duration::from_secs(5)));
    
    // Low Latency Tuning
    transport_config.initial_rtt(std::time::Duration::from_millis(1));
    
    // Configure ACK frequency for 1ms delay (removes 25ms bottleneck)
    let mut ack_freq = quinn::AckFrequencyConfig::default();
    ack_freq.max_ack_delay(Some(std::time::Duration::from_millis(1)));
    transport_config.ack_frequency_config(Some(ack_freq));
    
    // Increase concurrency to prevent blocking
    transport_config.max_concurrent_uni_streams(100_000u32.into());
    transport_config.max_concurrent_bidi_streams(100_000u32.into());

    // Compute buffer sizes from block size constant
    use crate::consensus::blockchain::MAXIMUM_BLOCK_SIZE;
    let stream_window = (MAXIMUM_BLOCK_SIZE as u32) + (MAXIMUM_BLOCK_SIZE as u32 / 10); // +10% headroom
    let connection_window = stream_window + (1024 * 1024);   // +1MB headroom for connection
    let datagram_buffer = (MAXIMUM_BLOCK_SIZE / 64) + (16 * 1024); // ~80KB with headroom

    transport_config.receive_window(connection_window.into());
    transport_config.stream_receive_window(stream_window.into());
    transport_config.datagram_receive_buffer_size(Some(datagram_buffer));

    config.transport_config(Arc::new(transport_config));

    Ok(config)
}

pub fn make_client_config() -> QuinnClientConfig {
    init_crypto();
    let mut crypto = ClientConfig::builder()
        .dangerous()
        .with_custom_certificate_verifier(Arc::new(SkipServerVerification))
        .with_no_client_auth();

    crypto.alpn_protocols = vec![b"hq-29".to_vec()];

    let client_crypto = QuicClientConfig::try_from(crypto)
        .expect("Failed to create QuicClientConfig");

    let mut config = QuinnClientConfig::new(Arc::new(client_crypto));
    let mut transport_config = quinn::TransportConfig::default();
    transport_config.max_idle_timeout(Some(quinn::VarInt::from_u32(60000).into())); // 60s
    transport_config.keep_alive_interval(Some(std::time::Duration::from_secs(5)));

    // Low Latency Tuning
    transport_config.initial_rtt(std::time::Duration::from_millis(1));
    
    // Configure ACK frequency for 1ms delay (removes 25ms bottleneck)
    let mut ack_freq = quinn::AckFrequencyConfig::default();
    ack_freq.max_ack_delay(Some(std::time::Duration::from_millis(1)));
    transport_config.ack_frequency_config(Some(ack_freq));
    
    transport_config.max_concurrent_uni_streams(100_000u32.into());
    transport_config.max_concurrent_bidi_streams(100_000u32.into());

    // Compute buffer sizes from block size constant
    use crate::consensus::blockchain::MAXIMUM_BLOCK_SIZE;
    let stream_window = (MAXIMUM_BLOCK_SIZE as u32) + (MAXIMUM_BLOCK_SIZE as u32 / 10); // +10% headroom
    let connection_window = stream_window + (1024 * 1024);   // +1MB headroom for connection
    let datagram_buffer = (MAXIMUM_BLOCK_SIZE / 64) + (16 * 1024); // ~80KB with headroom

    transport_config.receive_window(connection_window.into());
    transport_config.stream_receive_window(stream_window.into());
    transport_config.datagram_receive_buffer_size(Some(datagram_buffer));

    config.transport_config(Arc::new(transport_config));
    
    config
}

#[derive(Debug)]
struct SkipServerVerification;

impl rustls::client::danger::ServerCertVerifier for SkipServerVerification {
    fn verify_server_cert(
        &self,
        _end_entity: &CertificateDer<'_>,
        _intermediates: &[CertificateDer<'_>],
        _server_name: &ServerName<'_>,
        _ocsp_response: &[u8],
        _now: rustls::pki_types::UnixTime,
    ) -> Result<rustls::client::danger::ServerCertVerified, rustls::Error> {
        Ok(rustls::client::danger::ServerCertVerified::assertion())
    }

    fn verify_tls12_signature(
        &self,
        _message: &[u8],
        _cert: &CertificateDer<'_>,
        _dss: &rustls::DigitallySignedStruct,
    ) -> Result<rustls::client::danger::HandshakeSignatureValid, rustls::Error> {
        Ok(rustls::client::danger::HandshakeSignatureValid::assertion())
    }

    fn verify_tls13_signature(
        &self,
        _message: &[u8],
        _cert: &CertificateDer<'_>,
        _dss: &rustls::DigitallySignedStruct,
    ) -> Result<rustls::client::danger::HandshakeSignatureValid, rustls::Error> {
        Ok(rustls::client::danger::HandshakeSignatureValid::assertion())
    }

    fn supported_verify_schemes(&self) -> Vec<rustls::SignatureScheme> {
        vec![
            rustls::SignatureScheme::RSA_PSS_SHA256,
            rustls::SignatureScheme::RSA_PSS_SHA384,
            rustls::SignatureScheme::RSA_PSS_SHA512,
            rustls::SignatureScheme::ED25519,
            rustls::SignatureScheme::ECDSA_NISTP256_SHA256,
            rustls::SignatureScheme::ECDSA_NISTP384_SHA384,
        ]
    }
}
