//! HTTP handlers for join analysis endpoints.

use std::sync::Arc;
use std::time::Instant;

use axum::body::Body;
use axum::extract::{Path, Query, State};
use axum::http::{header, Response, StatusCode};
use axum::response::IntoResponse;
use axum::Json;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::arrow_reader::batches_to_json;
use crate::export;
use crate::spark_client::DatabricksClient;
use crate::sql_builder;
use crate::web_server::AppState;

/// Maximum number of columns to include in unmatched samples (reduces JSON payload size)
const MAX_SAMPLE_COLUMNS: usize = 15;

#[derive(Deserialize)]
pub struct JoinRequest {
    left_table: String,
    right_table: String,
    left_keys: Vec<String>,
    right_keys: Vec<String>,
}

pub async fn analyze_join(
    State(state): State<Arc<AppState>>,
    Json(req): Json<JoinRequest>,
) -> impl IntoResponse {
    let start_time = Instant::now();
    tracing::info!(
        "Starting join analysis: {} <-> {} on keys {:?} <-> {:?}",
        req.left_table, req.right_table, req.left_keys, req.right_keys
    );

    if req.left_keys.len() != req.right_keys.len() {
        return error_response(StatusCode::BAD_REQUEST, "Key count mismatch");
    }
    if req.left_keys.is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "At least one join key required");
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

    // Execute join analysis via SQL
    tracing::info!("Executing join analysis query...");
    let sql = sql_builder::join_analyze_sql(
        &req.left_table,
        &req.right_table,
        &req.left_keys,
        &req.right_keys,
    );

    let stats = match dbx.execute_sql(&sql, 1).await {
        Ok(response) => {
            if response.batches.is_empty() || response.batches[0].num_rows() == 0 {
                return error_response(StatusCode::NOT_FOUND, "No join analysis results");
            }
            parse_join_stats(&response.batches)
        }
        Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e.to_string()),
    };
    tracing::info!("Join statistics computed in {}ms", start_time.elapsed().as_millis());

    // Get limited column lists for both tables (reduces JSON payload size)
    tracing::info!("Fetching table schemas for column limiting...");
    let (left_columns, right_columns) = tokio::join!(
        get_limited_columns(dbx, &req.left_table, &req.left_keys),
        get_limited_columns(dbx, &req.right_table, &req.right_keys)
    );

    // Fetch unmatched rows sample for both sides with limited columns
    tracing::info!("Fetching unmatched row samples...");
    let (left_unmatched, right_unmatched) = fetch_unmatched_samples(
        dbx,
        &req.left_table,
        &req.right_table,
        &req.left_keys,
        &req.right_keys,
        &left_columns,
        &right_columns,
        stats.left_only,
        stats.right_only,
    )
    .await;

    // Compute match rates as decimals (0-1)
    let match_rate_left = compute_match_rate(stats.left_matched, stats.left_total);
    let match_rate_right = compute_match_rate(stats.right_matched, stats.right_total);

    // Determine cardinality
    let cardinality = determine_cardinality(
        stats.left_duplicate_keys,
        stats.right_duplicate_keys,
    );

    let elapsed = start_time.elapsed().as_millis();
    tracing::info!(
        "Join analysis complete in {}ms: left={}/{} matched, right={}/{} matched, cardinality={}",
        elapsed,
        stats.left_matched, stats.left_total,
        stats.right_matched, stats.right_total,
        cardinality
    );

    Json(json!({
        "statistics": {
            "left_total": stats.left_total,
            "right_total": stats.right_total,
            "matched_left": stats.left_matched,
            "matched_right": stats.right_matched,
            "match_rate_left": match_rate_left,
            "match_rate_right": match_rate_right,
            "cardinality": cardinality,
            "left_null_keys": stats.left_null_keys,
            "right_null_keys": stats.right_null_keys,
            "left_duplicate_keys": stats.left_duplicate_keys,
            "right_duplicate_keys": stats.right_duplicate_keys
        },
        "left_unmatched": left_unmatched,
        "right_unmatched": right_unmatched
    }))
    .into_response()
}

/// Get a limited list of columns for a table (join keys + first N columns).
/// This reduces JSON payload size when fetching unmatched samples.
async fn get_limited_columns(
    dbx: &DatabricksClient,
    table: &str,
    join_keys: &[String],
) -> Vec<String> {
    let schema_sql = sql_builder::describe_table_sql(table);
    match dbx.execute_sql(&schema_sql, 1000).await {
        Ok(response) => {
            let rows_value = batches_to_json(&response.batches, 0, 1000);
            let all_columns = extract_column_names(&rows_value);
            build_limited_column_list(&all_columns, join_keys)
        }
        Err(_) => {
            // If we can't get schema, fall back to join keys only
            join_keys.to_vec()
        }
    }
}

/// Extract column names from DESCRIBE TABLE result.
fn extract_column_names(rows_value: &Value) -> Vec<String> {
    rows_value
        .as_array()
        .map(|arr| {
            arr.iter()
                .filter_map(|row| row.get("col_name").and_then(Value::as_str).map(String::from))
                .collect()
        })
        .unwrap_or_default()
}

/// Build a limited column list: join keys first, then additional columns up to MAX_SAMPLE_COLUMNS.
fn build_limited_column_list(all_columns: &[String], join_keys: &[String]) -> Vec<String> {
    let mut result: Vec<String> = Vec::with_capacity(MAX_SAMPLE_COLUMNS);

    // Add join keys first (always included)
    for key in join_keys {
        if !result.contains(key) {
            result.push(key.clone());
        }
    }

    // Add remaining columns up to the limit
    for col in all_columns {
        if result.len() >= MAX_SAMPLE_COLUMNS {
            break;
        }
        if !result.contains(col) {
            result.push(col.clone());
        }
    }

    result
}

struct JoinStats {
    left_total: i64,
    right_total: i64,
    left_matched: i64,
    right_matched: i64,
    left_only: i64,
    right_only: i64,
    left_null_keys: i64,
    right_null_keys: i64,
    left_duplicate_keys: i64,
    right_duplicate_keys: i64,
}

fn parse_join_stats(batches: &[arrow::array::RecordBatch]) -> JoinStats {
    let rows_value = batches_to_json(batches, 0, 1);
    let rows = rows_value.as_array();
    let row = rows
        .and_then(|r| r.first())
        .cloned()
        .unwrap_or(serde_json::Value::Null);

    JoinStats {
        left_total: row.get("left_total").and_then(|v| v.as_i64()).unwrap_or(0),
        right_total: row.get("right_total").and_then(|v| v.as_i64()).unwrap_or(0),
        left_matched: row.get("left_matched").and_then(|v| v.as_i64()).unwrap_or(0),
        right_matched: row.get("right_matched").and_then(|v| v.as_i64()).unwrap_or(0),
        left_only: row.get("left_only").and_then(|v| v.as_i64()).unwrap_or(0),
        right_only: row.get("right_only").and_then(|v| v.as_i64()).unwrap_or(0),
        left_null_keys: row.get("left_null_keys").and_then(|v| v.as_i64()).unwrap_or(0),
        right_null_keys: row.get("right_null_keys").and_then(|v| v.as_i64()).unwrap_or(0),
        left_duplicate_keys: row.get("left_duplicate_keys").and_then(|v| v.as_i64()).unwrap_or(0),
        right_duplicate_keys: row.get("right_duplicate_keys").and_then(|v| v.as_i64()).unwrap_or(0),
    }
}

fn compute_match_rate(matched: i64, total: i64) -> f64 {
    if total > 0 {
        matched as f64 / total as f64
    } else {
        0.0
    }
}

fn determine_cardinality(left_dupes: i64, right_dupes: i64) -> &'static str {
    match (left_dupes > 0, right_dupes > 0) {
        (false, false) => "1:1",
        (false, true) => "1:N",
        (true, false) => "N:1",
        (true, true) => "N:M",
    }
}

async fn fetch_unmatched_samples(
    dbx: &DatabricksClient,
    left_frame: &str,
    right_frame: &str,
    left_keys: &[String],
    right_keys: &[String],
    left_columns: &[String],
    right_columns: &[String],
    left_only_count: i64,
    right_only_count: i64,
) -> (serde_json::Value, serde_json::Value) {
    const SAMPLE_LIMIT: usize = 100;

    // Use limited columns to reduce JSON payload size
    let left_sql = sql_builder::join_unmatched_sql_limited(
        left_frame, right_frame, left_keys, right_keys, "left", left_columns, 0, SAMPLE_LIMIT,
    );
    let right_sql = sql_builder::join_unmatched_sql_limited(
        left_frame, right_frame, left_keys, right_keys, "right", right_columns, 0, SAMPLE_LIMIT,
    );

    let (left_result, right_result) = tokio::join!(
        dbx.execute_sql(&left_sql, SAMPLE_LIMIT),
        dbx.execute_sql(&right_sql, SAMPLE_LIMIT)
    );

    let left_unmatched = match left_result {
        Ok(resp) => json!({
            "rows": batches_to_json(&resp.batches, 0, SAMPLE_LIMIT),
            "total": left_only_count,
            "columns_limited": left_columns.len() < MAX_SAMPLE_COLUMNS || !left_columns.is_empty()
        }),
        Err(_) => json!({ "rows": [], "total": 0, "columns_limited": false }),
    };

    let right_unmatched = match right_result {
        Ok(resp) => json!({
            "rows": batches_to_json(&resp.batches, 0, SAMPLE_LIMIT),
            "total": right_only_count,
            "columns_limited": right_columns.len() < MAX_SAMPLE_COLUMNS || !right_columns.is_empty()
        }),
        Err(_) => json!({ "rows": [], "total": 0, "columns_limited": false }),
    };

    (left_unmatched, right_unmatched)
}

#[derive(Deserialize)]
pub struct UnmatchedQuery {
    left_table: String,
    right_table: String,
    left_keys: String,
    right_keys: String,
    offset: Option<usize>,
    limit: Option<usize>,
}

pub async fn get_unmatched(
    State(state): State<Arc<AppState>>,
    Path(side): Path<String>,
    Query(query): Query<UnmatchedQuery>,
) -> impl IntoResponse {
    if side != "left" && side != "right" {
        return error_response(StatusCode::BAD_REQUEST, "Side must be 'left' or 'right'");
    }

    let left_keys: Vec<String> = query
        .left_keys
        .split(',')
        .map(|s| s.trim().to_string())
        .collect();
    let right_keys: Vec<String> = query
        .right_keys
        .split(',')
        .map(|s| s.trim().to_string())
        .collect();

    if left_keys.len() != right_keys.len() {
        return error_response(StatusCode::BAD_REQUEST, "Key count mismatch");
    }

    let offset = query.offset.unwrap_or(0);
    let limit = query.limit.unwrap_or(100).min(1000);

    let dbx = match &state.databricks_client {
        Some(c) => c,
        None => {
            return error_response(
                StatusCode::SERVICE_UNAVAILABLE,
                "No Databricks connection available",
            )
        }
    };

    // Execute via SQL
    let sql = sql_builder::join_unmatched_sql(
        &query.left_table,
        &query.right_table,
        &left_keys,
        &right_keys,
        &side,
        offset,
        limit,
    );

    match dbx.execute_sql(&sql, limit).await {
        Ok(response) => {
            let rows = batches_to_json(&response.batches, 0, limit);
            Json(json!({
                "rows": rows,
                "total": response.row_count,
                "offset": offset,
                "limit": limit,
                "side": side
            }))
            .into_response()
        }
        Err(e) => error_response(StatusCode::INTERNAL_SERVER_ERROR, &e.to_string()),
    }
}

#[derive(Deserialize)]
pub struct ExportRequest {
    left_table: String,
    right_table: String,
    left_keys: Vec<String>,
    right_keys: Vec<String>,
    side: String,
    format: String,
}

pub async fn export_unmatched(
    State(state): State<Arc<AppState>>,
    Json(req): Json<ExportRequest>,
) -> impl IntoResponse {
    if req.side != "left" && req.side != "right" {
        return error_response(StatusCode::BAD_REQUEST, "Side must be 'left' or 'right'");
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

    // Execute via SQL to get all unmatched rows
    let sql = sql_builder::join_unmatched_sql(
        &req.left_table,
        &req.right_table,
        &req.left_keys,
        &req.right_keys,
        &req.side,
        0,
        100000,
    );

    let batches = match dbx.execute_sql(&sql, 100000).await {
        Ok(response) => response.batches,
        Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e.to_string()),
    };

    let (content_type, data, ext) = match req.format.as_str() {
        "csv" => match export::to_csv(&batches) {
            Ok(d) => ("text/csv", d, "csv"),
            Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e.to_string()),
        },
        "json" => match export::to_json(&batches) {
            Ok(d) => ("application/json", d, "json"),
            Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e.to_string()),
        },
        "parquet" => match export::to_parquet(&batches) {
            Ok(d) => ("application/octet-stream", d, "parquet"),
            Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e.to_string()),
        },
        _ => return error_response(StatusCode::BAD_REQUEST, "Invalid format"),
    };

    let filename = format!("{}_unmatched.{}", req.side, ext);
    Response::builder()
        .header(header::CONTENT_TYPE, content_type)
        .header(
            header::CONTENT_DISPOSITION,
            format!("attachment; filename=\"{}\"", filename),
        )
        .body(Body::from(data))
        .unwrap()
        .into_response()
}

fn error_response(status: StatusCode, msg: &str) -> axum::response::Response {
    (status, Json(json!({"error": msg}))).into_response()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_helpers::*;

    // ============ compute_match_rate tests ============

    #[test]
    fn test_compute_match_rate_full_match() {
        let rate = compute_match_rate(100, 100);
        assert!((rate - 1.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_compute_match_rate_partial() {
        let rate = compute_match_rate(50, 100);
        assert!((rate - 0.5).abs() < f64::EPSILON);
    }

    #[test]
    fn test_compute_match_rate_no_match() {
        let rate = compute_match_rate(0, 100);
        assert!((rate - 0.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_compute_match_rate_empty() {
        let rate = compute_match_rate(0, 0);
        assert!((rate - 0.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_compute_match_rate_high_precision() {
        let rate = compute_match_rate(333, 1000);
        assert!((rate - 0.333).abs() < 0.001);
    }

    // ============ determine_cardinality tests ============

    #[test]
    fn test_determine_cardinality_one_to_one() {
        let card = determine_cardinality(0, 0);
        assert_eq!(card, "1:1");
    }

    #[test]
    fn test_determine_cardinality_one_to_many() {
        let card = determine_cardinality(0, 5);
        assert_eq!(card, "1:N");
    }

    #[test]
    fn test_determine_cardinality_many_to_one() {
        let card = determine_cardinality(5, 0);
        assert_eq!(card, "N:1");
    }

    #[test]
    fn test_determine_cardinality_many_to_many() {
        let card = determine_cardinality(5, 10);
        assert_eq!(card, "N:M");
    }

    #[test]
    fn test_determine_cardinality_large_values() {
        let card = determine_cardinality(1000000, 1000000);
        assert_eq!(card, "N:M");
    }

    // ============ parse_join_stats tests ============

    #[test]
    fn test_parse_join_stats_complete() {
        let batch = build_join_stats_batch(
            100,  // left_total
            90,   // left_distinct
            5,    // left_null_keys
            3,    // left_duplicate_keys
            200,  // right_total
            180,  // right_distinct
            10,   // right_null_keys
            7,    // right_duplicate_keys
            80,   // left_matched
            150,  // right_matched
            200,  // pairs
            20,   // left_only
            50,   // right_only
        );

        let stats = parse_join_stats(&[batch]);
        assert_eq!(stats.left_total, 100);
        assert_eq!(stats.right_total, 200);
        assert_eq!(stats.left_matched, 80);
        assert_eq!(stats.right_matched, 150);
        assert_eq!(stats.left_only, 20);
        assert_eq!(stats.right_only, 50);
        assert_eq!(stats.left_null_keys, 5);
        assert_eq!(stats.right_null_keys, 10);
        assert_eq!(stats.left_duplicate_keys, 3);
        assert_eq!(stats.right_duplicate_keys, 7);
    }

    #[test]
    fn test_parse_join_stats_empty_batch() {
        let batch = build_empty_batch(&[
            ("left_total", arrow::datatypes::DataType::Int64),
        ]);

        let stats = parse_join_stats(&[batch]);
        // Should return defaults (0) for all fields
        assert_eq!(stats.left_total, 0);
        assert_eq!(stats.right_total, 0);
        assert_eq!(stats.left_matched, 0);
    }

    #[test]
    fn test_parse_join_stats_missing_fields() {
        let batch = build_int64_batch(&[
            ("left_total", vec![Some(100)]),
            // Missing other fields
        ]);

        let stats = parse_join_stats(&[batch]);
        assert_eq!(stats.left_total, 100);
        // Missing fields should default to 0
        assert_eq!(stats.right_total, 0);
    }

    // ============ JoinRequest deserialization tests ============

    #[test]
    fn test_join_request_deserialization() {
        let json = r#"{
            "left_table": "orders",
            "right_table": "customers",
            "left_keys": ["customer_id"],
            "right_keys": ["id"]
        }"#;

        let req: JoinRequest = serde_json::from_str(json).unwrap();
        assert_eq!(req.left_table, "orders");
        assert_eq!(req.right_table, "customers");
        assert_eq!(req.left_keys, vec!["customer_id"]);
        assert_eq!(req.right_keys, vec!["id"]);
    }

    #[test]
    fn test_join_request_multiple_keys() {
        let json = r#"{
            "left_table": "table_a",
            "right_table": "table_b",
            "left_keys": ["id", "date", "region"],
            "right_keys": ["key", "dt", "area"]
        }"#;

        let req: JoinRequest = serde_json::from_str(json).unwrap();
        assert_eq!(req.left_keys.len(), 3);
        assert_eq!(req.right_keys.len(), 3);
    }

    #[test]
    fn test_join_request_rejects_wrong_field_names() {
        // Regression test: frontend sends left_table/right_table, not left_frame/right_frame
        let wrong_json = r#"{
            "left_frame": "orders",
            "right_frame": "customers",
            "left_keys": ["id"],
            "right_keys": ["id"]
        }"#;

        let result: Result<JoinRequest, _> = serde_json::from_str(wrong_json);
        assert!(result.is_err(), "Should reject old field names");
    }

    #[test]
    fn test_join_request_frontend_payload_format() {
        // Exact payload format sent by JoinAnalyzer.tsx frontend component
        let frontend_payload = serde_json::json!({
            "left_table": "my_catalog.my_schema.orders",
            "right_table": "my_catalog.my_schema.customers",
            "left_keys": ["customer_id"],
            "right_keys": ["id"]
        });

        let req: JoinRequest = serde_json::from_value(frontend_payload).unwrap();
        assert_eq!(req.left_table, "my_catalog.my_schema.orders");
        assert_eq!(req.right_table, "my_catalog.my_schema.customers");
    }

    // ============ UnmatchedQuery deserialization tests ============

    #[test]
    fn test_unmatched_query_deserialization() {
        // UnmatchedQuery uses query strings which we test via struct creation
        let query = UnmatchedQuery {
            left_table: "left_tbl".to_string(),
            right_table: "right_tbl".to_string(),
            left_keys: "id,date".to_string(),
            right_keys: "key,dt".to_string(),
            offset: Some(100),
            limit: Some(50),
        };

        assert_eq!(query.left_table, "left_tbl");
        assert_eq!(query.offset, Some(100));
        assert_eq!(query.limit, Some(50));
    }

    #[test]
    fn test_unmatched_query_defaults() {
        let query = UnmatchedQuery {
            left_table: "left".to_string(),
            right_table: "right".to_string(),
            left_keys: "id".to_string(),
            right_keys: "id".to_string(),
            offset: None,
            limit: None,
        };

        assert!(query.offset.is_none());
        assert!(query.limit.is_none());
    }

    // ============ ExportRequest tests ============

    #[test]
    fn test_export_request_deserialization() {
        let json = r#"{
            "left_table": "orders",
            "right_table": "customers",
            "left_keys": ["customer_id"],
            "right_keys": ["id"],
            "side": "left",
            "format": "csv"
        }"#;

        let req: ExportRequest = serde_json::from_str(json).unwrap();
        assert_eq!(req.left_table, "orders");
        assert_eq!(req.side, "left");
        assert_eq!(req.format, "csv");
    }

    #[test]
    fn test_export_request_parquet_format() {
        let json = r#"{
            "left_table": "a",
            "right_table": "b",
            "left_keys": ["id"],
            "right_keys": ["id"],
            "side": "right",
            "format": "parquet"
        }"#;

        let req: ExportRequest = serde_json::from_str(json).unwrap();
        assert_eq!(req.format, "parquet");
        assert_eq!(req.side, "right");
    }

    // ============ build_limited_column_list tests ============

    #[test]
    fn test_build_limited_column_list_join_keys_first() {
        let all_columns = vec![
            "a".to_string(), "b".to_string(), "c".to_string(),
            "id".to_string(), "d".to_string(),
        ];
        let join_keys = vec!["id".to_string()];
        let result = super::build_limited_column_list(&all_columns, &join_keys);

        // Join key should be first
        assert_eq!(result[0], "id");
        // Other columns follow
        assert!(result.contains(&"a".to_string()));
        assert!(result.contains(&"b".to_string()));
    }

    #[test]
    fn test_build_limited_column_list_respects_max() {
        let all_columns: Vec<String> = (0..50).map(|i| format!("col{}", i)).collect();
        let join_keys = vec!["key1".to_string(), "key2".to_string()];
        let result = super::build_limited_column_list(&all_columns, &join_keys);

        // Should not exceed MAX_SAMPLE_COLUMNS
        assert!(result.len() <= super::MAX_SAMPLE_COLUMNS);
        // Join keys should be present
        assert!(result.contains(&"key1".to_string()));
        assert!(result.contains(&"key2".to_string()));
    }

    #[test]
    fn test_build_limited_column_list_no_duplicates() {
        let all_columns = vec![
            "id".to_string(), "name".to_string(), "id".to_string(), "value".to_string(),
        ];
        let join_keys = vec!["id".to_string()];
        let result = super::build_limited_column_list(&all_columns, &join_keys);

        // Count occurrences of "id"
        let id_count = result.iter().filter(|c| *c == "id").count();
        assert_eq!(id_count, 1, "Should not have duplicate columns");
    }

    #[test]
    fn test_build_limited_column_list_multiple_join_keys() {
        let all_columns = vec![
            "a".to_string(), "b".to_string(), "c".to_string(),
        ];
        let join_keys = vec!["key1".to_string(), "key2".to_string(), "key3".to_string()];
        let result = super::build_limited_column_list(&all_columns, &join_keys);

        // All join keys should be first
        assert_eq!(result[0], "key1");
        assert_eq!(result[1], "key2");
        assert_eq!(result[2], "key3");
    }

    #[test]
    fn test_build_limited_column_list_empty_all_columns() {
        let all_columns: Vec<String> = vec![];
        let join_keys = vec!["id".to_string()];
        let result = super::build_limited_column_list(&all_columns, &join_keys);

        // Should contain only join keys
        assert_eq!(result.len(), 1);
        assert_eq!(result[0], "id");
    }

    // ============ extract_column_names tests ============

    #[test]
    fn test_extract_column_names_valid() {
        let rows_value = serde_json::json!([
            {"col_name": "id", "data_type": "int"},
            {"col_name": "name", "data_type": "string"},
            {"col_name": "amount", "data_type": "double"}
        ]);
        let result = super::extract_column_names(&rows_value);

        assert_eq!(result.len(), 3);
        assert_eq!(result[0], "id");
        assert_eq!(result[1], "name");
        assert_eq!(result[2], "amount");
    }

    #[test]
    fn test_extract_column_names_empty_array() {
        let rows_value = serde_json::json!([]);
        let result = super::extract_column_names(&rows_value);
        assert!(result.is_empty());
    }

    #[test]
    fn test_extract_column_names_not_array() {
        let rows_value = serde_json::json!({"col_name": "id"});
        let result = super::extract_column_names(&rows_value);
        assert!(result.is_empty());
    }

    #[test]
    fn test_extract_column_names_missing_col_name() {
        let rows_value = serde_json::json!([
            {"data_type": "int"},
            {"col_name": "name", "data_type": "string"}
        ]);
        let result = super::extract_column_names(&rows_value);

        // Should skip rows without col_name
        assert_eq!(result.len(), 1);
        assert_eq!(result[0], "name");
    }
}
