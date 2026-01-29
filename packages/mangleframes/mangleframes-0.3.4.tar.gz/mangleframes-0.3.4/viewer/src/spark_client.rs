//! Databricks client wrapper for direct Spark Connect access.

use std::sync::Arc;
use std::time::Instant;

use arrow::record_batch::RecordBatch;
use spark_connect::{SparkConnectClient, SparkConnectError};
use tokio::sync::RwLock;
use tracing::{error, info};

/// Response from SQL execution via Spark Connect.
pub struct SqlResponse {
    pub batches: Vec<RecordBatch>,
    pub row_count: u64,
    pub execution_ms: u64,
}

/// Wrapper around SparkConnectClient for Databricks integration.
pub struct DatabricksClient {
    client: Arc<RwLock<Option<SparkConnectClient>>>,
    connected: Arc<RwLock<bool>>,
}

impl DatabricksClient {
    /// Create a new unconnected Databricks client.
    pub fn new() -> Self {
        Self {
            client: Arc::new(RwLock::new(None)),
            connected: Arc::new(RwLock::new(false)),
        }
    }

    /// Connect to Databricks via Spark Connect.
    ///
    /// Pass `cluster_id` as `None` for serverless compute.
    pub async fn connect(
        &self,
        host: &str,
        token: &str,
        cluster_id: Option<&str>,
    ) -> Result<(), SparkConnectError> {
        let mode = if cluster_id.is_some() { "cluster" } else { "serverless" };
        info!("Initializing Databricks {} connection to {}", mode, host);

        let client = SparkConnectClient::connect(host, token, cluster_id).await?;

        *self.client.write().await = Some(client);
        *self.connected.write().await = true;

        info!("Databricks {} connection established", mode);
        Ok(())
    }

    /// Connect via a Spark Connect proxy.
    ///
    /// The proxy handles authentication, so no credentials needed.
    pub async fn connect_via_proxy(
        &self,
        proxy_url: &str,
    ) -> Result<(), SparkConnectError> {
        info!("Connecting to Spark Connect proxy at {}", proxy_url);

        let client = SparkConnectClient::connect_via_proxy(proxy_url).await?;

        *self.client.write().await = Some(client);
        *self.connected.write().await = true;

        info!("Connected to proxy at {}", proxy_url);
        Ok(())
    }

    /// Check if client is connected.
    pub async fn is_connected(&self) -> bool {
        *self.connected.read().await
    }

    /// Execute SQL query and return results with timing.
    pub async fn execute_sql(
        &self,
        query: &str,
        limit: usize,
    ) -> Result<SqlResponse, SparkConnectError> {
        let guard = self.client.read().await;
        let client = guard
            .as_ref()
            .ok_or_else(|| SparkConnectError::Config("Not connected".to_string()))?;

        let start = Instant::now();
        let batches = client.sql_limit(query, limit as u32).await?;
        let execution_ms = start.elapsed().as_millis() as u64;

        let row_count: u64 = batches.iter().map(|b| b.num_rows() as u64).sum();

        info!(
            "SQL executed via Spark Connect in {}ms, {} rows",
            execution_ms, row_count
        );

        Ok(SqlResponse {
            batches,
            row_count,
            execution_ms,
        })
    }

    /// Register Arrow batches as a temporary view in Spark.
    pub async fn create_temp_view(
        &self,
        view_name: &str,
        batches: &[RecordBatch],
    ) -> Result<(), SparkConnectError> {
        let guard = self.client.read().await;
        let client = guard
            .as_ref()
            .ok_or_else(|| SparkConnectError::Config("Not connected".to_string()))?;

        client.create_temp_view(view_name, batches).await
    }
}

impl Default for DatabricksClient {
    fn default() -> Self {
        Self::new()
    }
}

/// Try to create and connect a DatabricksClient from environment variables.
/// Uses serverless if DATABRICKS_CLUSTER_ID is not set.
pub async fn try_connect_from_env() -> Option<Arc<DatabricksClient>> {
    let host = std::env::var("DATABRICKS_HOST").ok()?;
    let token = std::env::var("DATABRICKS_TOKEN").ok()?;
    let cluster_id = std::env::var("DATABRICKS_CLUSTER_ID").ok();

    let client = Arc::new(DatabricksClient::new());

    match client.connect(&host, &token, cluster_id.as_deref()).await {
        Ok(()) => Some(client),
        Err(e) => {
            error!("Failed to connect to Databricks: {}", e);
            None
        }
    }
}
