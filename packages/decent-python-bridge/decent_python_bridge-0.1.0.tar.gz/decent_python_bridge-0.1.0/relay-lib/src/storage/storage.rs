use sled::Db;

pub struct Storage {
    db: Db,
}

impl Storage {
    pub fn new(path: &str) -> Result<Self, String> {
        let db = sled::open(path).map_err(|e| e.to_string())?;
        Ok(Storage { db })
    }

    pub fn put(&self, key: &[u8], value: &[u8]) -> Result<(), String> {
        self.db.insert(key, value).map_err(|e| e.to_string())?;
        Ok(())
    }

    pub fn get(&self, key: &[u8]) -> Result<Option<Vec<u8>>, String> {
        match self.db.get(key).map_err(|e| e.to_string())? {
            Some(value) => Ok(Some(value.to_vec())),
            None => Ok(None),
        }
    }
}

