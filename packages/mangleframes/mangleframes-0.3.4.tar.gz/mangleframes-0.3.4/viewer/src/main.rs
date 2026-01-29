//! MangleFrames Viewer - Web-based PySpark DataFrame viewer.

mod alert_handlers;
mod arrow_reader;
mod dashboard;
mod export;
mod handlers;
mod history_analysis;
mod history_handlers;
mod join_handlers;
mod perf;
mod reconcile_handlers;
mod spark_client;
mod sql_builder;
mod stats;
#[cfg(test)]
mod test_helpers;
mod web_server;
mod websocket;

use std::sync::Arc;

use clap::Parser;
use tracing::info;
use tracing_subscriber::EnvFilter;

use crate::web_server::AppState;

#[derive(Parser)]
#[command(name = "mangleframes-viewer")]
#[command(about = "Web-based DataFrame viewer via Spark Connect")]
struct Args {
    /// Web server port
    #[arg(short, long, default_value = "8765")]
    port: u16,

    /// Connect via Spark Connect proxy (e.g., sc://localhost:15002)
    #[arg(long)]
    proxy_url: Option<String>,

    /// Databricks workspace host (not needed when using --proxy-url)
    #[arg(long, env = "DATABRICKS_HOST")]
    databricks_host: Option<String>,

    /// Databricks personal access token (not needed when using --proxy-url)
    #[arg(long, env = "DATABRICKS_TOKEN")]
    databricks_token: Option<String>,

    /// Databricks cluster ID (for cluster mode)
    #[arg(long, env = "DATABRICKS_CLUSTER_ID")]
    databricks_cluster_id: Option<String>,

    /// Use Databricks serverless compute (no cluster ID needed)
    #[arg(long)]
    serverless: bool,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .init();

    let args = Args::parse();

    let client = Arc::new(spark_client::DatabricksClient::new());

    // Connect via proxy or directly to Databricks
    if let Some(ref proxy_url) = args.proxy_url {
        info!("Connecting via Spark Connect proxy at {}", proxy_url);
        client
            .connect_via_proxy(proxy_url)
            .await
            .map_err(|e| anyhow::anyhow!("Proxy connection failed: {}", e))?;
    } else {
        // Direct Databricks connection requires host and token
        let host = args
            .databricks_host
            .as_deref()
            .ok_or_else(|| anyhow::anyhow!("DATABRICKS_HOST is required"))?;
        let token = args
            .databricks_token
            .as_deref()
            .ok_or_else(|| anyhow::anyhow!("DATABRICKS_TOKEN is required"))?;

        // Determine cluster_id: None for serverless, Some for cluster mode
        let cluster_id = if args.serverless {
            info!("Initializing Databricks serverless mode");
            None
        } else if let Some(ref id) = args.databricks_cluster_id {
            info!("Initializing Databricks cluster mode (cluster: {})", id);
            Some(id.as_str())
        } else {
            info!("Initializing Databricks serverless mode (default)");
            None
        };

        client
            .connect(host, token, cluster_id)
            .await
            .map_err(|e| anyhow::anyhow!("Databricks connection failed: {}", e))?;
    }

    let state = AppState::new(Some(client));

    info!("Starting web server on http://localhost:{}", args.port);
    info!("Open this URL in your browser to view the UI");
    web_server::run(state, args.port).await
}
