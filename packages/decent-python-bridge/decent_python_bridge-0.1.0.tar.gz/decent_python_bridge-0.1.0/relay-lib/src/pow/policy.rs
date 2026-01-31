use crate::pow::difficulty::Difficulty;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DifficultyRule {
    Fixed(Difficulty),
    Dynamic,
    None,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PowPolicy {
    pub rules: HashMap<u32, DifficultyRule>,
}

impl PowPolicy {
    pub fn new() -> Self {
        Self {
            rules: HashMap::new(),
        }
    }

    pub fn set_rule(&mut self, cmd: u32, rule: DifficultyRule) {
        self.rules.insert(cmd, rule);
    }

    pub fn get_difficulty(&self, cmd: u32, current_dynamic_diff: &Difficulty) -> Option<Difficulty> {
        match self.rules.get(&cmd) {
            Some(DifficultyRule::Fixed(d)) => Some(*d),
            Some(DifficultyRule::Dynamic) => Some(*current_dynamic_diff),
            Some(DifficultyRule::None) => None,
            None => None, // Default to no PoW if not specified for control commands? 
            // Or should it default to Dynamic?
            // Data blocks usually go through Block::from_bytes which has its own check.
        }
    }
}
