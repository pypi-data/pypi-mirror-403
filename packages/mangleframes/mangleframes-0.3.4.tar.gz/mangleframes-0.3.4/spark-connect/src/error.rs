//! Error types for Spark Connect client.

use thiserror::Error;

/// Errors that can occur when using the Spark Connect client.
#[derive(Error, Debug)]
pub enum SparkConnectError {
    /// Connection to Spark cluster failed
    #[error("Connection failed: {0}")]
    Connection(#[from] tonic::transport::Error),

    /// gRPC call failed
    #[error("gRPC error: {0}")]
    Grpc(#[from] tonic::Status),

    /// Arrow IPC parsing failed
    #[error("Arrow error: {0}")]
    Arrow(#[from] arrow::error::ArrowError),

    /// No data returned from query
    #[error("No data returned from query")]
    NoData,

    /// Invalid configuration
    #[error("Invalid configuration: {0}")]
    Config(String),
}
