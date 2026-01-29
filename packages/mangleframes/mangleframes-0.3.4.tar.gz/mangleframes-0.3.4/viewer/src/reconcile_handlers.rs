//! HTTP handlers for CSV reconciliation endpoints.

use std::io::Cursor;
use std::sync::Arc;
use std::time::Instant;

use arrow::record_batch::RecordBatch;
use arrow_csv::ReaderBuilder;
use axum::body::Body;
use axum::extract::{Multipart, State};
use axum::http::{header, Response, StatusCode};
use axum::response::IntoResponse;
use axum::Json;
use base64::{engine::general_purpose::STANDARD as BASE64, Engine as _};
use serde::{Deserialize, Serialize};
use serde_json::json;
use tracing;

use crate::arrow_reader::batches_to_json;
use crate::dashboard::{self, DashboardMetadata};
use crate::sql_builder;
use crate::web_server::{AppState, CachedFrame};

const CSV_FRAME_PREFIX: &str = "__csv__";

/// Sanitize a name for use as a Spark temp view name.
/// Replaces non-alphanumeric characters (except underscores) with underscores.
fn sanitize_name(name: &str) -> String {
    name.chars()
        .map(|c| if c.is_alphanumeric() || c == '_' { c } else { '_' })
        .collect()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum JoinType {
    Inner,
    Left,
    Right,
    Full,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AggregationType {
    Sum,
    Count,
    Min,
    Max,
    Avg,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregationConfig {
    pub column: String,
    pub aggregations: Vec<AggregationType>,
}

#[derive(Deserialize)]
pub struct UploadCsvJsonRequest {
    pub csv_data: String,
    pub frame_name: String,
}

#[derive(Serialize)]
pub struct UploadCsvResponse {
    pub frame_name: String,
    pub columns: Vec<ColumnInfo>,
    pub row_count: usize,
}

#[derive(Serialize)]
pub struct ColumnInfo {
    pub name: String,
    pub data_type: String,
    pub nullable: bool,
}

#[derive(Deserialize)]
pub struct ReconcileRequest {
    pub source_frame: String,
    pub target_frame: String,
    #[serde(default = "default_source_type")]
    pub source_type: String,
    pub source_group_by: Vec<String>,
    pub target_group_by: Vec<String>,
    pub source_join_keys: Vec<String>,
    pub target_join_keys: Vec<String>,
    pub join_type: JoinType,
    #[serde(default)]
    pub aggregations: Vec<AggregationConfig>,
    pub sample_limit: Option<usize>,
}

fn default_source_type() -> String {
    "csv".to_string()
}

#[derive(Deserialize)]
pub struct ExportReconcileRequest {
    pub source_frame: String,
    pub target_frame: String,
    #[serde(default = "default_source_type")]
    pub source_type: String,
    pub source_group_by: Vec<String>,
    pub target_group_by: Vec<String>,
    pub source_join_keys: Vec<String>,
    pub target_join_keys: Vec<String>,
    pub join_type: JoinType,
    #[serde(default)]
    pub aggregations: Vec<AggregationConfig>,
}

fn parse_csv(data: &[u8]) -> Result<Vec<RecordBatch>, String> {
    let cursor = Cursor::new(data);
    let format = arrow_csv::reader::Format::default().with_header(true);
    let (schema, _) = format
        .infer_schema(cursor, Some(100))
        .map_err(|e| e.to_string())?;

    let cursor = Cursor::new(data);
    let reader = ReaderBuilder::new(Arc::new(schema))
        .with_header(true)
        .build(cursor)
        .map_err(|e| e.to_string())?;

    reader.collect::<Result<Vec<_>, _>>().map_err(|e| e.to_string())
}

pub async fn upload_csv_multipart(
    State(state): State<Arc<AppState>>,
    mut multipart: Multipart,
) -> impl IntoResponse {
    let mut csv_data: Option<Vec<u8>> = None;
    let mut frame_name: Option<String> = None;

    while let Ok(Some(field)) = multipart.next_field().await {
        let name = field.name().unwrap_or("").to_string();
        match name.as_str() {
            "file" => {
                csv_data = match field.bytes().await {
                    Ok(b) => Some(b.to_vec()),
                    Err(e) => return error_response(StatusCode::BAD_REQUEST, &e.to_string()),
                };
            }
            "frame_name" => {
                frame_name = match field.text().await {
                    Ok(t) => Some(t),
                    Err(e) => return error_response(StatusCode::BAD_REQUEST, &e.to_string()),
                };
            }
            _ => {}
        }
    }

    let csv_data = match csv_data {
        Some(d) => d,
        None => return error_response(StatusCode::BAD_REQUEST, "No CSV file provided"),
    };

    let frame_name = frame_name.unwrap_or_else(|| {
        format!("csv_upload_{}", chrono::Utc::now().timestamp_millis())
    });

    process_csv_upload(&state, &csv_data, &frame_name).await
}

pub async fn upload_csv_json(
    State(state): State<Arc<AppState>>,
    Json(req): Json<UploadCsvJsonRequest>,
) -> impl IntoResponse {
    let csv_data = match BASE64.decode(&req.csv_data) {
        Ok(d) => d,
        Err(e) => return error_response(StatusCode::BAD_REQUEST, &format!("Invalid base64: {}", e)),
    };

    process_csv_upload(&state, &csv_data, &req.frame_name).await
}

async fn process_csv_upload(
    state: &AppState,
    csv_data: &[u8],
    frame_name: &str,
) -> axum::response::Response {
    let batches = match parse_csv(csv_data) {
        Ok(b) => b,
        Err(e) => return error_response(StatusCode::BAD_REQUEST, &e),
    };

    if batches.is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "CSV has no data");
    }

    let schema = batches[0].schema();
    let columns: Vec<ColumnInfo> = schema.fields().iter().map(|f| ColumnInfo {
        name: f.name().clone(),
        data_type: format!("{:?}", f.data_type()),
        nullable: f.is_nullable(),
    }).collect();

    let row_count: usize = batches.iter().map(|b| b.num_rows()).sum();

    state.evict_frame_if_needed().await;
    let mut cache = state.cache.write().await;
    cache.insert(
        format!("{}{}", CSV_FRAME_PREFIX, frame_name),
        CachedFrame { batches, stats: None, last_access: Instant::now() },
    );

    Json(UploadCsvResponse { frame_name: frame_name.to_string(), columns, row_count }).into_response()
}

pub async fn list_csv_frames(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let cache = state.cache.read().await;
    let frames: Vec<String> = cache.keys()
        .filter(|k| k.starts_with(CSV_FRAME_PREFIX))
        .map(|k| k.strip_prefix(CSV_FRAME_PREFIX).unwrap_or(k).to_string())
        .collect();
    Json(json!({ "frames": frames }))
}

pub async fn reconcile(
    State(state): State<Arc<AppState>>,
    Json(req): Json<ReconcileRequest>,
) -> impl IntoResponse {
    if let Err(resp) = validate_reconcile_request(&req) {
        return resp;
    }

    let dbx = match &state.databricks_client {
        Some(c) => c,
        None => {
            return error_response(
                StatusCode::SERVICE_UNAVAILABLE,
                "No Databricks connection available",
            )
        }
    };

    // Check if source is a CSV frame and register it as a temp view in Spark
    let source_frame_name = {
        let csv_cache_key = format!("{}{}", CSV_FRAME_PREFIX, req.source_frame);
        let cache = state.cache.read().await;

        if let Some(cached) = cache.get(&csv_cache_key) {
            let view_name = format!("__mf_csv_{}", sanitize_name(&req.source_frame));
            tracing::info!(
                "Registering CSV '{}' as temp view '{}' ({} batches)",
                req.source_frame,
                view_name,
                cached.batches.len()
            );

            // Drop the cache lock before async operation
            let batches = cached.batches.clone();
            drop(cache);

            if let Err(e) = dbx.create_temp_view(&view_name, &batches).await {
                return error_response(
                    StatusCode::INTERNAL_SERVER_ERROR,
                    &format!("Failed to register CSV as temp view: {}", e),
                );
            }
            view_name
        } else {
            drop(cache);
            req.source_frame.clone()
        }
    };

    let config = build_reconcile_config(&req);
    let sample_limit = req.sample_limit.unwrap_or(100);

    tracing::info!("Executing reconciliation: {} vs {}", source_frame_name, req.target_frame);

    // Execute all queries in parallel using tokio::join!
    let (
        stats_result,
        source_only_result,
        target_only_result,
        matched_result,
        mismatched_result,
        totals_result,
    ) = tokio::join!(
        execute_stats_query(dbx, &source_frame_name, &req.target_frame, &config),
        execute_source_only_query(dbx, &source_frame_name, &req.target_frame, &config, sample_limit),
        execute_target_only_query(dbx, &source_frame_name, &req.target_frame, &config, sample_limit),
        execute_matched_query(dbx, &source_frame_name, &req.target_frame, &config, sample_limit),
        execute_mismatched_query(dbx, &source_frame_name, &req.target_frame, &config, sample_limit),
        execute_totals_query(dbx, &source_frame_name, &req.target_frame, &config)
    );

    // Handle results with early return for critical failures
    let stats = match stats_result {
        Ok(s) => s,
        Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e),
    };

    let source_only_rows = match source_only_result {
        Ok(rows) => rows,
        Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e),
    };

    let target_only_rows = match target_only_result {
        Ok(rows) => rows,
        Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e),
    };

    let matched_rows = match matched_result {
        Ok(rows) => rows,
        Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e),
    };

    // Graceful fallback for non-critical queries
    let mismatched_rows = match mismatched_result {
        Ok(rows) => rows,
        Err(e) => {
            tracing::warn!("Failed to get mismatched rows: {}", e);
            json!([])
        }
    };

    let column_totals = match totals_result {
        Ok(totals) => totals,
        Err(e) => {
            tracing::warn!("Failed to get column totals: {}", e);
            json!([])
        }
    };

    // Key match rate: percentage of source groups that have a matching key in target
    let key_match_rate = if stats.source_groups > 0 {
        stats.key_matched_groups as f64 / stats.source_groups as f64
    } else {
        0.0
    };

    // Value match rate: percentage of key-matched groups that also have matching values
    let value_match_rate = if stats.key_matched_groups > 0 {
        stats.value_matched_groups as f64 / stats.key_matched_groups as f64
    } else {
        0.0
    };

    tracing::info!(
        "Reconciliation complete: key_match_rate={:.2}%, value_match_rate={:.2}%, key_matched={}, value_matched={}, value_mismatched={}, source_only={}, target_only={}",
        key_match_rate * 100.0,
        value_match_rate * 100.0,
        stats.key_matched_groups,
        stats.value_matched_groups,
        stats.value_mismatched_groups,
        stats.source_only_groups,
        stats.target_only_groups
    );

    Json(json!({
        "statistics": {
            "key_match_rate": key_match_rate,
            "value_match_rate": value_match_rate,
            "key_matched_groups": stats.key_matched_groups,
            "value_matched_groups": stats.value_matched_groups,
            "value_mismatched_groups": stats.value_mismatched_groups,
            "source_groups": stats.source_groups,
            "source_only_groups": stats.source_only_groups,
            "target_groups": stats.target_groups,
            "target_only_groups": stats.target_only_groups
        },
        "column_totals": column_totals,
        "source_only": {
            "total": stats.source_only_groups,
            "rows": source_only_rows
        },
        "target_only": {
            "total": stats.target_only_groups,
            "rows": target_only_rows
        },
        "matched_rows": {
            "rows": matched_rows
        },
        "mismatched_rows": {
            "total": stats.value_mismatched_groups,
            "rows": mismatched_rows
        },
        "source_frame": req.source_frame,
        "target_frame": req.target_frame
    }))
    .into_response()
}

fn validate_reconcile_request(req: &ReconcileRequest) -> Result<(), axum::response::Response> {
    if req.source_join_keys.len() != req.target_join_keys.len() {
        return Err(error_response(StatusCode::BAD_REQUEST, "Join key count mismatch"));
    }
    if req.source_join_keys.is_empty() {
        return Err(error_response(StatusCode::BAD_REQUEST, "At least one join key required"));
    }
    if req.source_group_by.is_empty() {
        return Err(error_response(
            StatusCode::BAD_REQUEST,
            "At least one source group-by column required",
        ));
    }
    if req.target_group_by.is_empty() {
        return Err(error_response(
            StatusCode::BAD_REQUEST,
            "At least one target group-by column required",
        ));
    }
    if !req.source_join_keys.iter().all(|k| req.source_group_by.contains(k)) {
        return Err(error_response(
            StatusCode::BAD_REQUEST,
            "Source join keys must be subset of group-by",
        ));
    }
    if !req.target_join_keys.iter().all(|k| req.target_group_by.contains(k)) {
        return Err(error_response(
            StatusCode::BAD_REQUEST,
            "Target join keys must be subset of group-by",
        ));
    }
    if req.aggregations.is_empty() {
        return Err(error_response(StatusCode::BAD_REQUEST, "At least one aggregation required"));
    }
    Ok(())
}

fn build_reconcile_config(req: &ReconcileRequest) -> serde_json::Value {
    json!({
        "source_type": req.source_type,
        "source_group_by": req.source_group_by,
        "target_group_by": req.target_group_by,
        "source_join_keys": req.source_join_keys,
        "target_join_keys": req.target_join_keys,
        "join_type": format!("{:?}", req.join_type).to_lowercase(),
        "aggregations": req.aggregations,
        "sample_limit": req.sample_limit.unwrap_or(100)
    })
}

#[derive(Debug)]
struct ReconcileStats {
    source_groups: i64,
    target_groups: i64,
    key_matched_groups: i64,
    value_matched_groups: i64,
    value_mismatched_groups: i64,
    source_only_groups: i64,
    target_only_groups: i64,
}

async fn execute_stats_query(
    dbx: &crate::spark_client::DatabricksClient,
    source: &str,
    target: &str,
    config: &serde_json::Value,
) -> Result<ReconcileStats, String> {
    let sql = sql_builder::reconcile_stats_sql(source, target, config)?;
    tracing::debug!("Stats SQL: {}", sql);

    let response = dbx.execute_sql(&sql, 1).await.map_err(|e| e.to_string())?;
    let rows = batches_to_json(&response.batches, 0, 1);

    let arr = rows.as_array().ok_or("Expected array from stats query")?;
    if arr.is_empty() {
        return Ok(ReconcileStats {
            source_groups: 0,
            target_groups: 0,
            key_matched_groups: 0,
            value_matched_groups: 0,
            value_mismatched_groups: 0,
            source_only_groups: 0,
            target_only_groups: 0,
        });
    }

    let row = &arr[0];
    Ok(ReconcileStats {
        source_groups: extract_i64(row, "source_groups"),
        target_groups: extract_i64(row, "target_groups"),
        key_matched_groups: extract_i64(row, "key_matched_groups"),
        value_matched_groups: extract_i64(row, "value_matched_groups"),
        value_mismatched_groups: extract_i64(row, "value_mismatched_groups"),
        source_only_groups: extract_i64(row, "source_only_groups"),
        target_only_groups: extract_i64(row, "target_only_groups"),
    })
}

fn extract_i64(row: &serde_json::Value, key: &str) -> i64 {
    row.get(key).and_then(|v| v.as_i64()).unwrap_or(0)
}

async fn execute_source_only_query(
    dbx: &crate::spark_client::DatabricksClient,
    source: &str,
    target: &str,
    config: &serde_json::Value,
    limit: usize,
) -> Result<serde_json::Value, String> {
    let sql = sql_builder::reconcile_source_only_sql(source, target, config, limit)?;
    tracing::debug!("Source-only SQL: {}", sql);

    let response = dbx.execute_sql(&sql, limit).await.map_err(|e| e.to_string())?;
    Ok(batches_to_json(&response.batches, 0, limit))
}

async fn execute_target_only_query(
    dbx: &crate::spark_client::DatabricksClient,
    source: &str,
    target: &str,
    config: &serde_json::Value,
    limit: usize,
) -> Result<serde_json::Value, String> {
    let sql = sql_builder::reconcile_target_only_sql(source, target, config, limit)?;
    tracing::debug!("Target-only SQL: {}", sql);

    let response = dbx.execute_sql(&sql, limit).await.map_err(|e| e.to_string())?;
    Ok(batches_to_json(&response.batches, 0, limit))
}

async fn execute_matched_query(
    dbx: &crate::spark_client::DatabricksClient,
    source: &str,
    target: &str,
    config: &serde_json::Value,
    limit: usize,
) -> Result<serde_json::Value, String> {
    let sql = sql_builder::reconcile_matched_sql(source, target, config, limit)?;
    tracing::debug!("Matched SQL: {}", sql);

    let response = dbx.execute_sql(&sql, limit).await.map_err(|e| e.to_string())?;
    Ok(batches_to_json(&response.batches, 0, limit))
}

async fn execute_mismatched_query(
    dbx: &crate::spark_client::DatabricksClient,
    source: &str,
    target: &str,
    config: &serde_json::Value,
    limit: usize,
) -> Result<serde_json::Value, String> {
    let sql = sql_builder::reconcile_mismatched_sql(source, target, config, limit)?;
    tracing::debug!("Mismatched SQL: {}", sql);

    let response = dbx.execute_sql(&sql, limit).await.map_err(|e| e.to_string())?;
    Ok(batches_to_json(&response.batches, 0, limit))
}

async fn execute_totals_query(
    dbx: &crate::spark_client::DatabricksClient,
    source: &str,
    target: &str,
    config: &serde_json::Value,
) -> Result<serde_json::Value, String> {
    let sql = sql_builder::reconcile_totals_sql(source, target, config)?;
    tracing::debug!("Totals SQL: {}", sql);

    let response = dbx.execute_sql(&sql, 1).await.map_err(|e| e.to_string())?;
    let rows = batches_to_json(&response.batches, 0, 1);

    let arr = rows.as_array().ok_or("Expected array from totals query")?;
    if arr.is_empty() {
        return Ok(json!([]));
    }

    // Convert the single row of totals into column comparison format
    let row = &arr[0];
    let mut totals = Vec::new();

    if let Some(obj) = row.as_object() {
        let mut columns: std::collections::HashMap<String, (Option<f64>, Option<f64>)> =
            std::collections::HashMap::new();

        for (key, value) in obj {
            let num = value.as_f64().or_else(|| value.as_i64().map(|i| i as f64));
            if key.starts_with("source_") {
                let col_name = key.strip_prefix("source_").unwrap();
                columns.entry(col_name.to_string()).or_default().0 = num;
            } else if key.starts_with("target_") {
                let col_name = key.strip_prefix("target_").unwrap();
                columns.entry(col_name.to_string()).or_default().1 = num;
            }
        }

        for (name, (source, target)) in columns {
            let source_val = source.unwrap_or(0.0);
            let target_val = target.unwrap_or(0.0);
            let diff = source_val - target_val;
            let diff_pct = if source_val != 0.0 {
                (diff / source_val) * 100.0
            } else {
                0.0
            };

            // Parse column name and aggregation from alias (e.g., "o_totalprice_sum" -> "o_totalprice", "sum")
            let (column_name, aggregation) = if let Some(pos) = name.rfind('_') {
                let (col, agg) = name.split_at(pos);
                (col.to_string(), agg[1..].to_string())
            } else {
                (name.clone(), "unknown".to_string())
            };

            totals.push(json!({
                "column": column_name,
                "aggregation": aggregation,
                "source_total": source_val,
                "target_total": target_val,
                "difference": diff,
                "percent_diff": diff_pct
            }));
        }
    }

    Ok(json!(totals))
}

pub async fn export_reconciliation(
    State(state): State<Arc<AppState>>,
    Json(req): Json<ExportReconcileRequest>,
) -> impl IntoResponse {
    let dbx = match &state.databricks_client {
        Some(c) => c,
        None => {
            return error_response(
                StatusCode::SERVICE_UNAVAILABLE,
                "No Databricks connection available",
            )
        }
    };

    // Check if source is a CSV frame and register it as a temp view in Spark
    let source_frame_name = {
        let csv_cache_key = format!("{}{}", CSV_FRAME_PREFIX, req.source_frame);
        let cache = state.cache.read().await;

        if let Some(cached) = cache.get(&csv_cache_key) {
            let view_name = format!("__mf_csv_{}", sanitize_name(&req.source_frame));
            tracing::info!(
                "Registering CSV '{}' as temp view '{}' for export",
                req.source_frame,
                view_name
            );

            let batches = cached.batches.clone();
            drop(cache);

            if let Err(e) = dbx.create_temp_view(&view_name, &batches).await {
                return error_response(
                    StatusCode::INTERNAL_SERVER_ERROR,
                    &format!("Failed to register CSV as temp view: {}", e),
                );
            }
            view_name
        } else {
            drop(cache);
            req.source_frame.clone()
        }
    };

    let config = json!({
        "source_type": req.source_type,
        "source_group_by": req.source_group_by,
        "target_group_by": req.target_group_by,
        "source_join_keys": req.source_join_keys,
        "target_join_keys": req.target_join_keys,
        "join_type": format!("{:?}", req.join_type).to_lowercase(),
        "aggregations": req.aggregations,
    });

    let sample_limit = 100;

    tracing::info!(
        "Exporting reconciliation dashboard: {} vs {}",
        source_frame_name,
        req.target_frame
    );

    // Execute all queries in parallel using tokio::join!
    let (
        stats_result,
        source_only_result,
        target_only_result,
        matched_result,
        mismatched_result,
        totals_result,
    ) = tokio::join!(
        execute_stats_query(dbx, &source_frame_name, &req.target_frame, &config),
        execute_source_only_query(dbx, &source_frame_name, &req.target_frame, &config, sample_limit),
        execute_target_only_query(dbx, &source_frame_name, &req.target_frame, &config, sample_limit),
        execute_matched_query(dbx, &source_frame_name, &req.target_frame, &config, sample_limit),
        execute_mismatched_query(dbx, &source_frame_name, &req.target_frame, &config, sample_limit),
        execute_totals_query(dbx, &source_frame_name, &req.target_frame, &config)
    );

    // Handle results with early return for critical failures
    let stats = match stats_result {
        Ok(s) => s,
        Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e),
    };

    let source_only_rows = match source_only_result {
        Ok(rows) => rows,
        Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e),
    };

    let target_only_rows = match target_only_result {
        Ok(rows) => rows,
        Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e),
    };

    let matched_rows = match matched_result {
        Ok(rows) => rows,
        Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e),
    };

    // Graceful fallback for non-critical queries
    let mismatched_rows = match mismatched_result {
        Ok(rows) => rows,
        Err(e) => {
            tracing::warn!("Failed to get mismatched rows: {}", e);
            json!([])
        }
    };

    let column_totals = match totals_result {
        Ok(totals) => totals,
        Err(e) => {
            tracing::warn!("Failed to get column totals: {}", e);
            json!([])
        }
    };

    // Key match rate: percentage of source groups that have a matching key in target
    let key_match_rate = if stats.source_groups > 0 {
        stats.key_matched_groups as f64 / stats.source_groups as f64
    } else {
        0.0
    };

    // Value match rate: percentage of key-matched groups that also have matching values
    let value_match_rate = if stats.key_matched_groups > 0 {
        stats.value_matched_groups as f64 / stats.key_matched_groups as f64
    } else {
        0.0
    };

    tracing::info!(
        "Export reconciliation complete: key_match_rate={:.2}%, value_match_rate={:.2}%, key_matched={}, value_matched={}, value_mismatched={}, source_only={}, target_only={}",
        key_match_rate * 100.0,
        value_match_rate * 100.0,
        stats.key_matched_groups,
        stats.value_matched_groups,
        stats.value_mismatched_groups,
        stats.source_only_groups,
        stats.target_only_groups
    );

    let result = json!({
        "statistics": {
            "key_match_rate": key_match_rate,
            "value_match_rate": value_match_rate,
            "key_matched_groups": stats.key_matched_groups,
            "value_matched_groups": stats.value_matched_groups,
            "value_mismatched_groups": stats.value_mismatched_groups,
            "source_groups": stats.source_groups,
            "source_only_groups": stats.source_only_groups,
            "target_groups": stats.target_groups,
            "target_only_groups": stats.target_only_groups
        },
        "column_totals": column_totals,
        "source_only": {
            "total": stats.source_only_groups,
            "rows": source_only_rows
        },
        "target_only": {
            "total": stats.target_only_groups,
            "rows": target_only_rows
        },
        "matched_rows": {
            "rows": matched_rows
        },
        "mismatched_rows": {
            "total": stats.value_mismatched_groups,
            "rows": mismatched_rows
        },
        "source_frame": req.source_frame,
        "target_frame": req.target_frame
    });

    let metadata = DashboardMetadata {
        source_frame: req.source_frame.clone(),
        target_frame: req.target_frame.clone(),
        source_type: req.source_type.clone(),
        group_by_source: req.source_group_by.clone(),
        group_by_target: req.target_group_by.clone(),
        join_keys_source: req.source_join_keys.clone(),
        join_keys_target: req.target_join_keys.clone(),
    };

    let html = dashboard::generate_reconcile_dashboard(&result, &metadata);
    let filename = format!(
        "reconciliation_{}_{}.html",
        req.source_frame, req.target_frame
    );

    Response::builder()
        .header(header::CONTENT_TYPE, "text/html; charset=utf-8")
        .header(
            header::CONTENT_DISPOSITION,
            format!("attachment; filename=\"{}\"", filename),
        )
        .body(Body::from(html))
        .unwrap()
        .into_response()
}

fn error_response(status: StatusCode, msg: &str) -> axum::response::Response {
    (status, Json(json!({"error": msg}))).into_response()
}

#[cfg(test)]
mod tests {
    use super::*;

    // ============ parse_csv tests ============

    #[test]
    fn test_parse_csv_valid() {
        let csv_data = b"name,age\nAlice,30\nBob,25";
        let result = parse_csv(csv_data);
        assert!(result.is_ok());
        let batches = result.unwrap();
        assert!(!batches.is_empty());
        let total_rows: usize = batches.iter().map(|b| b.num_rows()).sum();
        assert_eq!(total_rows, 2);
    }

    #[test]
    fn test_parse_csv_empty() {
        let csv_data = b"name,age\n";
        let result = parse_csv(csv_data);
        assert!(result.is_ok());
        let batches = result.unwrap();
        let total_rows: usize = batches.iter().map(|b| b.num_rows()).sum();
        assert_eq!(total_rows, 0);
    }

    #[test]
    fn test_parse_csv_special_chars() {
        let csv_data = b"name,description\nAlice,\"Hello, World\"\nBob,\"Line1\nLine2\"";
        let result = parse_csv(csv_data);
        assert!(result.is_ok());
    }

    #[test]
    fn test_parse_csv_numeric_columns() {
        let csv_data = b"id,amount,rate\n1,100,1.5\n2,200,2.5";
        let result = parse_csv(csv_data);
        assert!(result.is_ok());
        let batches = result.unwrap();
        assert_eq!(batches[0].num_columns(), 3);
    }

    // ============ JoinType/AggregationType serde tests ============

    #[test]
    fn test_join_type_serde() {
        let inner: JoinType = serde_json::from_str("\"inner\"").unwrap();
        assert!(matches!(inner, JoinType::Inner));

        let left: JoinType = serde_json::from_str("\"left\"").unwrap();
        assert!(matches!(left, JoinType::Left));

        let right: JoinType = serde_json::from_str("\"right\"").unwrap();
        assert!(matches!(right, JoinType::Right));

        let full: JoinType = serde_json::from_str("\"full\"").unwrap();
        assert!(matches!(full, JoinType::Full));
    }

    #[test]
    fn test_aggregation_type_serde() {
        let sum: AggregationType = serde_json::from_str("\"sum\"").unwrap();
        assert!(matches!(sum, AggregationType::Sum));

        let count: AggregationType = serde_json::from_str("\"count\"").unwrap();
        assert!(matches!(count, AggregationType::Count));

        let min: AggregationType = serde_json::from_str("\"min\"").unwrap();
        assert!(matches!(min, AggregationType::Min));

        let max: AggregationType = serde_json::from_str("\"max\"").unwrap();
        assert!(matches!(max, AggregationType::Max));

        let avg: AggregationType = serde_json::from_str("\"avg\"").unwrap();
        assert!(matches!(avg, AggregationType::Avg));
    }

    // ============ build_reconcile_config tests ============

    #[test]
    fn test_build_reconcile_config() {
        let req = ReconcileRequest {
            source_frame: "source_table".to_string(),
            target_frame: "target_table".to_string(),
            source_type: "csv".to_string(),
            source_group_by: vec!["id".to_string(), "date".to_string()],
            target_group_by: vec!["customer_id".to_string(), "order_date".to_string()],
            source_join_keys: vec!["id".to_string()],
            target_join_keys: vec!["customer_id".to_string()],
            join_type: JoinType::Inner,
            aggregations: vec![
                AggregationConfig {
                    column: "amount".to_string(),
                    aggregations: vec![AggregationType::Sum, AggregationType::Count],
                },
            ],
            sample_limit: Some(50),
        };

        let config = build_reconcile_config(&req);

        assert_eq!(config["source_type"], "csv");
        assert_eq!(config["source_group_by"].as_array().unwrap().len(), 2);
        assert_eq!(config["target_group_by"].as_array().unwrap().len(), 2);
        assert_eq!(config["source_join_keys"].as_array().unwrap().len(), 1);
        assert_eq!(config["target_join_keys"].as_array().unwrap().len(), 1);
        assert_eq!(config["join_type"], "inner");
        assert_eq!(config["sample_limit"], 50);
    }

    // ============ ColumnInfo tests ============

    #[test]
    fn test_column_info_serialization() {
        let col_info = ColumnInfo {
            name: "test_column".to_string(),
            data_type: "Int64".to_string(),
            nullable: true,
        };

        let json = serde_json::to_value(&col_info).unwrap();
        assert_eq!(json["name"], "test_column");
        assert_eq!(json["data_type"], "Int64");
        assert_eq!(json["nullable"], true);
    }

    // ============ UploadCsvResponse tests ============

    #[test]
    fn test_upload_csv_response_serialization() {
        let response = UploadCsvResponse {
            frame_name: "my_frame".to_string(),
            columns: vec![
                ColumnInfo {
                    name: "id".to_string(),
                    data_type: "Int64".to_string(),
                    nullable: false,
                },
                ColumnInfo {
                    name: "name".to_string(),
                    data_type: "Utf8".to_string(),
                    nullable: true,
                },
            ],
            row_count: 100,
        };

        let json = serde_json::to_value(&response).unwrap();
        assert_eq!(json["frame_name"], "my_frame");
        assert_eq!(json["row_count"], 100);
        assert_eq!(json["columns"].as_array().unwrap().len(), 2);
    }

    // ============ ReconcileRequest deserialization tests ============

    #[test]
    fn test_reconcile_request_deserialization() {
        let json = r#"{
            "source_frame": "source",
            "target_frame": "target",
            "source_group_by": ["id"],
            "target_group_by": ["id"],
            "source_join_keys": ["id"],
            "target_join_keys": ["id"],
            "join_type": "inner",
            "aggregations": [
                {"column": "amount", "aggregations": ["sum"]}
            ],
            "sample_limit": 100
        }"#;

        let req: ReconcileRequest = serde_json::from_str(json).unwrap();
        assert_eq!(req.source_frame, "source");
        assert_eq!(req.target_frame, "target");
        assert!(matches!(req.join_type, JoinType::Inner));
        assert_eq!(req.sample_limit, Some(100));
    }

    #[test]
    fn test_reconcile_request_default_source_type() {
        let json = r#"{
            "source_frame": "source",
            "target_frame": "target",
            "source_group_by": ["id"],
            "target_group_by": ["id"],
            "source_join_keys": ["id"],
            "target_join_keys": ["id"],
            "join_type": "inner",
            "aggregations": []
        }"#;

        let req: ReconcileRequest = serde_json::from_str(json).unwrap();
        assert_eq!(req.source_type, "csv");
    }

    // ============ extract_i64 tests ============

    #[test]
    fn test_extract_i64_present() {
        let row = json!({"count": 42, "total": 100});
        assert_eq!(extract_i64(&row, "count"), 42);
        assert_eq!(extract_i64(&row, "total"), 100);
    }

    #[test]
    fn test_extract_i64_missing() {
        let row = json!({"count": 42});
        assert_eq!(extract_i64(&row, "missing"), 0);
    }

    #[test]
    fn test_extract_i64_null() {
        let row = json!({"count": null});
        assert_eq!(extract_i64(&row, "count"), 0);
    }

    #[test]
    fn test_extract_i64_non_numeric() {
        let row = json!({"count": "not a number"});
        assert_eq!(extract_i64(&row, "count"), 0);
    }

    // ============ sanitize_name tests ============

    #[test]
    fn test_sanitize_name_spaces_and_parens() {
        assert_eq!(sanitize_name("orders (1)"), "orders__1_");
    }

    #[test]
    fn test_sanitize_name_dots_and_hyphens() {
        assert_eq!(sanitize_name("my-table.csv"), "my_table_csv");
    }

    #[test]
    fn test_sanitize_name_already_valid() {
        assert_eq!(sanitize_name("normal_name"), "normal_name");
    }

    #[test]
    fn test_sanitize_name_alphanumeric() {
        assert_eq!(sanitize_name("table123"), "table123");
    }

    #[test]
    fn test_sanitize_name_special_chars() {
        assert_eq!(sanitize_name("data@2024#test!"), "data_2024_test_");
    }
}
