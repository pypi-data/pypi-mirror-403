use sled::Db;

pub struct Mailbox {
    db: Db,
}

impl Mailbox {
    pub fn new(path: &str) -> Result<Self, String> {
        let db = sled::open(path).map_err(|e| e.to_string())?;
        Ok(Mailbox { db })
    }

    pub fn put(&self, target: &str, block: &[u8]) -> Result<(), String> {
        let key = format!("mailbox:{}", target);
        self.db.insert(key, block).map_err(|e| e.to_string())?;
        Ok(())
    }

    pub fn get(&self, target: &str) -> Result<Option<Vec<u8>>, String> {
        let key = format!("mailbox:{}", target);
        match self.db.get(key).map_err(|e| e.to_string())? {
            Some(value) => Ok(Some(value.to_vec())),
            None => Ok(None),
        }
    }
}

