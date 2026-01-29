//! Axum web server setup and state management.

use std::collections::HashMap;
use std::sync::Arc;
use std::time::Instant;

use arrow::record_batch::RecordBatch;
use axum::routing::{get, post};
use axum::Router;
use tokio::sync::{broadcast, RwLock};
use tower_http::cors::{Any, CorsLayer};

use crate::alert_handlers;
use crate::handlers;
use crate::history_handlers;
use crate::join_handlers;
use crate::perf::PerfCollector;
use crate::reconcile_handlers;
use crate::spark_client::DatabricksClient;
use crate::websocket;

const MAX_FRAME_CACHE_ENTRIES: usize = 20;
const MAX_JSON_CACHE_ENTRIES: usize = 100;

pub struct CachedFrame {
    pub batches: Vec<RecordBatch>,
    pub stats: Option<serde_json::Value>,
    pub last_access: Instant,
}

/// Cache key for JSON response bytes
#[derive(Hash, Eq, PartialEq, Clone)]
pub struct JsonCacheKey {
    pub frame: String,
    pub offset: usize,
    pub limit: usize,
}

pub struct JsonCacheEntry {
    pub data: Vec<u8>,
    pub created: Instant,
}

pub struct AppState {
    pub databricks_client: Option<Arc<DatabricksClient>>,
    pub cache: RwLock<HashMap<String, CachedFrame>>,
    pub json_cache: RwLock<HashMap<JsonCacheKey, JsonCacheEntry>>,
    pub broadcast_tx: broadcast::Sender<String>,
    pub perf: Arc<PerfCollector>,
}

impl AppState {
    pub fn new(databricks_client: Option<Arc<DatabricksClient>>) -> Arc<Self> {
        let (tx, _) = broadcast::channel(16);
        Arc::new(Self {
            databricks_client,
            cache: RwLock::new(HashMap::new()),
            json_cache: RwLock::new(HashMap::new()),
            broadcast_tx: tx,
            perf: Arc::new(PerfCollector::new()),
        })
    }

    /// Evict oldest frame cache entry if over limit. Call before inserting.
    pub async fn evict_frame_if_needed(&self) {
        let mut cache = self.cache.write().await;
        while cache.len() >= MAX_FRAME_CACHE_ENTRIES {
            let oldest = cache
                .iter()
                .min_by_key(|(_, v)| v.last_access)
                .map(|(k, _)| k.clone());
            if let Some(key) = oldest {
                cache.remove(&key);
            } else {
                break;
            }
        }
    }

    /// Evict oldest JSON cache entries if over limit. Call before inserting.
    pub async fn evict_json_if_needed(&self) {
        let mut cache = self.json_cache.write().await;
        while cache.len() >= MAX_JSON_CACHE_ENTRIES {
            let oldest = cache
                .iter()
                .min_by_key(|(_, v)| v.created)
                .map(|(k, _)| k.clone());
            if let Some(key) = oldest {
                cache.remove(&key);
            } else {
                break;
            }
        }
    }
}

pub async fn run(state: Arc<AppState>, port: u16) -> anyhow::Result<()> {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    let app = Router::new()
        .route("/", get(handlers::serve_index))
        .route("/assets/{*path}", get(handlers::serve_static))
        .route("/api/frames", get(handlers::list_frames))
        .route("/api/frames/{name}/schema", get(handlers::get_schema))
        .route("/api/frames/{name}/data", get(handlers::get_data))
        .route("/api/frames/{name}/stats", get(handlers::get_stats))
        .route("/api/frames/{name}/export", post(handlers::export_frame))
        .route("/api/query", post(handlers::execute_query))
        .route("/api/perf", get(handlers::get_perf_stats))
        .route("/api/perf/benchmark", post(handlers::run_benchmark))
        .route("/api/perf/stream", post(handlers::stream_benchmark))
        .route("/api/join/analyze", post(join_handlers::analyze_join))
        .route("/api/join/unmatched/{side}", get(join_handlers::get_unmatched))
        .route("/api/join/export", post(join_handlers::export_unmatched))
        .route("/api/history/analyze", post(history_handlers::analyze_history))
        .route("/api/reconcile/upload", post(reconcile_handlers::upload_csv_multipart))
        .route("/api/reconcile/upload/json", post(reconcile_handlers::upload_csv_json))
        .route("/api/reconcile/frames", get(reconcile_handlers::list_csv_frames))
        .route("/api/reconcile", post(reconcile_handlers::reconcile))
        .route("/api/reconcile/export", post(reconcile_handlers::export_reconciliation))
        // Alert routes
        .route("/api/alerts/threshold", post(alert_handlers::generate_threshold_alert))
        .route("/api/alerts/null_rate", post(alert_handlers::generate_null_rate_alert))
        .route("/api/alerts/row_count", post(alert_handlers::generate_row_count_alert))
        .route("/api/alerts/data_freshness", post(alert_handlers::generate_data_freshness_alert))
        .route("/api/alerts/duplicate_keys", post(alert_handlers::generate_duplicate_keys_alert))
        .route("/api/alerts/reconciliation", post(alert_handlers::generate_reconciliation_alert))
        .route("/api/alerts/templates", get(alert_handlers::get_alert_templates))
        // TODO: Fix axum version conflict for export handler
        // .route("/api/alerts/export", post(alert_handlers::export_alert_for_databricks))
        .route("/ws", get(websocket::ws_handler))
        .layer(cors)
        .with_state(state);

    let addr = std::net::SocketAddr::from(([0, 0, 0, 0], port));
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
