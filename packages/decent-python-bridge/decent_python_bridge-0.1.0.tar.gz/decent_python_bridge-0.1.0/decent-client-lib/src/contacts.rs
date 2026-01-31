use anyhow::Result;

use std::fs;
use std::path::Path;

#[derive(Debug, Clone, minicbor::Encode, minicbor::Decode)]
pub struct Contact {
    #[n(0)] pub name: String,
    #[n(1)] pub public_key: String,
    #[n(2)] pub notes: Option<String>,
    #[n(3)] pub unread_count: u32,
    #[n(4)] pub local_identity_file: Option<String>,
}

#[derive(Debug, minicbor::Encode, minicbor::Decode)]
pub struct ContactBook {
    #[n(0)] pub contacts: Vec<Contact>,
}

impl ContactBook {
    pub fn new() -> Self {
        Self {
            contacts: Vec::new(),
        }
    }

    pub fn load(path: &Path) -> Result<Self> {
        if !path.exists() {
            return Ok(Self::new());
        }
        let data = fs::read(path)?;
        let book: ContactBook = minicbor::decode(&data)?;
        Ok(book)
    }

    pub fn save(&self, path: &Path) -> Result<()> {
        let data = minicbor::to_vec(self)?;
        fs::write(path, data)?;
        Ok(())
    }

    pub fn add_contact(&mut self, contact: Contact) {
        self.contacts.push(contact);
    }

    pub fn remove_contact(&mut self, index: usize) {
        if index < self.contacts.len() {
            self.contacts.remove(index);
        }
    }
}
