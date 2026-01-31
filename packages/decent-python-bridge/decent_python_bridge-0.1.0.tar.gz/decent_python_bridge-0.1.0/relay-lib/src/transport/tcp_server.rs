use tokio::net::{TcpListener, TcpStream};

pub struct TCPServer {
    listener: TcpListener,
}

impl TCPServer {
    pub async fn bind(host: &str, port: u16) -> Result<Self, String> {
        let addr = format!("{}:{}", host, port);
        let listener = TcpListener::bind(&addr).await.map_err(|e| e.to_string())?;
        Ok(TCPServer { listener })
    }

    pub async fn accept(&self) -> Result<TcpStream, String> {
        let (stream, _) = self.listener.accept().await.map_err(|e| e.to_string())?;
        Ok(stream)
    }
}

