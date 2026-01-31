/*
 *  DecentMesh Consensus: Network Commands
 *  --------------------------------------
 *  Command identifiers for the DecentMesh protocol multiplexer.
 *  These IDs define the packet types shared across the network.
 */

// --- Handshake & Authentication ---
pub const CMD_HANDSHAKE_INIT: u32 = 1;
pub const CMD_HANDSHAKE_RESP: u32 = 2;

// --- DHT & Peer Discovery ---
pub const CMD_DHT_PING: u32 = 10;
pub const CMD_DHT_PONG: u32 = 11;
pub const CMD_DHT_STORE: u32 = 12;
pub const CMD_DHT_FIND_NODE: u32 = 13;
pub const CMD_DHT_FOUND_NODES: u32 = 14;
pub const CMD_DHT_FOUND_VALUE: u32 = 15;

// --- Consensus & Governance ---
pub const CMD_UPDATE_DIFFICULTY: u32 = 20;
pub const CMD_ADVERTISE_BPS: u32 = 21;

// --- Connection Liveliness ---
pub const CMD_PING: u32 = 22;
pub const CMD_PONG: u32 = 23;

// --- Gossip & Events ---
pub const CMD_PEER_JOINED: u32 = 25;
pub const CMD_PEER_LEFT: u32 = 26;

// --- Routing & Transport ---
pub const CMD_ONION_PACKET: u32 = 30;
