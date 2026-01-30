use reqwest;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum CmfClientError {
    #[error("Api Key cannot be empty.")]
    EmptyApiKey,

    #[error("Path cannot be empty.")]
    EmptyPath,

    #[error("Path must start with '/'")]
    InvalidPath,
    
    #[error("Error connecting to CMF API: {0}")]
    ConnectError(#[from] reqwest::Error),
    
    #[error("Unexpected status {status}: {body}")]
    BadStatus {status: u16, body: String}
}