use crate::pow::difficulty::Difficulty;
use crate::pow::policy::DifficultyRule;
use serde::Deserialize;
use std::collections::HashMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize, Clone)]
pub struct SeedRelay {
    pub address: String,
    pub name: Option<String>,
    pub region: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct SeedRelayConfig {
    pub relay: Vec<SeedRelay>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct DifficultyConfig {
    pub t_cost: u32,
    pub m_cost: u32,
    pub p_cost: u8,
    pub n_bits: u8,
    pub hash_len_chars: u8,
    pub compression_level: u8,
    pub compression_type: u8,
    pub express: u8,
}

impl DifficultyConfig {
    pub fn to_difficulty(&self) -> Difficulty {
        Difficulty {
            t_cost: self.t_cost,
            m_cost: self.m_cost,
            p_cost: self.p_cost,
            n_bits: self.n_bits,
            hash_len_chars: self.hash_len_chars,
            compression_level: self.compression_level,
            compression_type: self.compression_type,
            express: self.express,
        }
    }
}

#[derive(Debug, Deserialize, Clone)]
pub struct DHTConfig {
    pub k: usize,
    pub alpha: usize,
    pub bucket_count: usize,
    pub refresh_interval: u64,
}

#[derive(Debug, Deserialize, Clone)]
pub struct DifficultyPresets {
    pub relay_handshake: DifficultyConfig,
    pub client_handshake: DifficultyConfig,
    pub cmd_difficulty: Option<HashMap<String, DifficultyRule>>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct ScalingConfig {
    pub target_bps: f64,
    pub update_interval_seconds: f64,
}

#[derive(Debug, Deserialize, Clone)]
pub struct QuicConfig {
    pub bind_addr: String,
    pub bind_addr_v6: Option<String>,
    pub idle_timeout_ms: u64,
    pub keep_alive_interval_ms: u64,
    #[serde(default)]
    pub hole_punching: bool,
    #[serde(default = "default_ipv6_true")]
    pub ipv6: bool,
}

fn default_ipv6_true() -> bool {
    true
}

#[derive(Debug, Deserialize, Clone)]
pub struct RoutingConfig {
    pub relay_ping_interval_seconds: u64,
    pub capacity_weight: f64,
    pub latency_weight: f64,
    pub min_required_bps: f64,
}

#[derive(Debug, Deserialize, Clone)]
pub struct StatsConfig {
    pub enabled: bool,
    pub host: String,
    #[serde(default = "default_stats_port")]
    pub port: u16,
    #[serde(default)]
    pub json_metrics_only: bool,
    #[serde(default)]
    pub autostart: bool,
}

fn default_stats_port() -> u16 {
    8008
}

#[derive(Debug, Deserialize, Clone)]
pub struct NetworkConfig {
    pub difficulty: DifficultyPresets,
    pub dht: DHTConfig,
    pub scaling: ScalingConfig,
    pub quic: QuicConfig,
    pub routing: RoutingConfig,
    pub monitoring: StatsConfig,
}

impl NetworkConfig {
    pub fn load(path: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        let contents = fs::read_to_string(path)?;
        let config: NetworkConfig = toml::from_str(&contents)?;
        Ok(config)
    }
}

impl SeedRelayConfig {
    pub fn load(path: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        let contents = fs::read_to_string(path)?;
        let config: SeedRelayConfig = toml::from_str(&contents)?;
        Ok(config)
    }

    pub fn get_addresses(&self) -> Vec<String> {
        self.relay.iter().map(|r| r.address.clone()).collect()
    }
}
