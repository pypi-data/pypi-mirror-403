use tokio::net::TcpStream;
use crate::transport::socket_functions::{recv_all, send_all};
use crate::util::constants::MAXIMUM_DATA_SIZE;


pub struct TCPClient {
    stream: TcpStream,
}

impl TCPClient {
    pub async fn connect(host: &str, port: u16) -> Result<Self, String> {
        let addr = format!("{}:{}", host, port);
        let stream = TcpStream::connect(&addr).await.map_err(|e| e.to_string())?;
        Ok(TCPClient { stream })
    }

    pub async fn send_message(&mut self, data: &[u8], ack: bool) -> Result<Option<Vec<u8>>, String> {
        if data.len() > MAXIMUM_DATA_SIZE {
            return Err("Too much data for one block".to_string());
        }
        
        send_all(&mut self.stream, data).await?;
        
        if ack {
            let (response, _) = recv_all(&mut self.stream).await?;
            if response.is_empty() {
                return Ok(None);
            }
            Ok(Some(response))
        } else {
            Ok(None)
        }
    }

    pub async fn receive_message(&mut self, decode: bool) -> Result<Vec<u8>, String> {
        let (response, _) = recv_all(&mut self.stream).await?;
        if decode {
            Ok(response)
        } else {
            Ok(response)
        }
    }

    pub fn close(&mut self) {
    }
}

