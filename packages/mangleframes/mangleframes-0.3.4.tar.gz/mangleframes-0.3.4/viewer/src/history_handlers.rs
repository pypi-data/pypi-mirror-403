//! HTTP handlers for history coverage analysis endpoints.

use std::collections::HashMap;
use std::sync::Arc;
use std::time::Instant;

use axum::extract::State;
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::Json;
use futures_util::future::join_all;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::arrow_reader::batches_to_json;
use crate::history_analysis::{
    FrameDataLoss, FrameKeyStats, FrameTemporalStats, HistoryAnalyzer, PairwiseOverlap,
    TemporalRangeStats,
};
use crate::spark_client::DatabricksClient;
use crate::sql_builder;
use crate::web_server::AppState;

#[derive(Deserialize)]
pub struct FrameConfig {
    pub frame: String,
    pub columns: Vec<String>,
}

#[derive(Deserialize)]
pub struct JoinPair {
    pub source_frame: String,
    pub target_frame: String,
    pub source_keys: Vec<String>,
    pub target_keys: Vec<String>,
}

#[derive(Deserialize)]
pub struct HistoryRequest {
    pub frames: Vec<FrameConfig>,
    pub join_pairs: Vec<JoinPair>,
    pub bucket_size: Option<String>,
}

/// Helper to get first row from JSON array
fn get_first_row(value: &Value) -> Option<&Value> {
    value.as_array().and_then(|arr| arr.first())
}

/// Helper to get all rows from JSON array
fn get_rows(value: &Value) -> Vec<&Value> {
    value.as_array().map(|arr| arr.iter().collect()).unwrap_or_default()
}

pub async fn analyze_history(
    State(state): State<Arc<AppState>>,
    Json(req): Json<HistoryRequest>,
) -> impl IntoResponse {
    let start_time = Instant::now();
    tracing::info!(
        "Starting history analysis for {} frames, {} join pairs",
        req.frames.len(),
        req.join_pairs.len()
    );

    if req.frames.is_empty() {
        return error_response(StatusCode::BAD_REQUEST, "At least one frame required");
    }

    if req.frames.len() > 5 {
        return error_response(StatusCode::BAD_REQUEST, "Maximum 5 frames supported");
    }

    for jp in &req.join_pairs {
        if jp.source_keys.len() != jp.target_keys.len() {
            return error_response(
                StatusCode::BAD_REQUEST,
                "Source and target keys must have same length",
            );
        }
        if jp.source_frame == jp.target_frame {
            return error_response(StatusCode::BAD_REQUEST, "Cannot join frame to itself");
        }
    }

    let dbx = match &state.databricks_client {
        Some(c) => c,
        None => {
            return error_response(
                StatusCode::SERVICE_UNAVAILABLE,
                "No Databricks connection available",
            );
        }
    };

    let mut analyzer = HistoryAnalyzer::new();
    let bucket = req.bucket_size.as_deref().unwrap_or("month");

    // Phase 1: Collect key stats for all frames in parallel
    tracing::info!("Collecting key statistics for {} frames...", req.frames.len());
    let key_stats_results = collect_key_stats_parallel(dbx, &req.frames).await;
    for result in key_stats_results {
        match result {
            Ok(stats) => analyzer.add_key_stats(stats),
            Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e),
        }
    }
    tracing::info!("Key statistics collected in {}ms", start_time.elapsed().as_millis());

    // Phase 2: Detect date columns and collect temporal stats in parallel
    tracing::info!("Detecting date columns and collecting temporal statistics...");
    let frame_date_columns = detect_date_columns_parallel(dbx, &req.frames).await;

    let temporal_results = collect_temporal_stats_parallel(
        dbx,
        &req.frames,
        &frame_date_columns,
        bucket,
    ).await;

    for (temporal_stats, range_stats) in temporal_results {
        if let Some(stats) = temporal_stats {
            analyzer.add_temporal_stats(stats);
        }
        if let Some(range) = range_stats {
            analyzer.add_temporal_range(range);
        }
    }
    tracing::info!("Temporal statistics collected in {}ms", start_time.elapsed().as_millis());

    // Phase 3: Compute overlaps for all join pairs in parallel
    if !req.join_pairs.is_empty() {
        tracing::info!("Computing overlaps for {} join pairs...", req.join_pairs.len());
        let overlap_results = compute_overlaps_parallel(dbx, &req.join_pairs).await;
        for result in overlap_results {
            match result {
                Ok(overlap) => analyzer.add_overlap(overlap),
                Err(e) => return error_response(StatusCode::INTERNAL_SERVER_ERROR, &e),
            }
        }
        tracing::info!("Overlaps computed in {}ms", start_time.elapsed().as_millis());
    }

    // Phase 4: Compute data loss based on overlap zone (parallel)
    if !frame_date_columns.is_empty() {
        tracing::info!("Computing temporal data loss...");
        let (overlap_start, overlap_end) =
            compute_overlap_bounds_parallel(dbx, &req.frames, &frame_date_columns).await;

        if let (Some(start), Some(end)) = (overlap_start, overlap_end) {
            if start <= end {
                let loss_results = compute_data_loss_parallel(
                    dbx,
                    &req.frames,
                    &frame_date_columns,
                    &start,
                    &end,
                ).await;
                for loss in loss_results.into_iter().flatten() {
                    analyzer.add_data_loss(loss);
                }
            }
        }
        tracing::info!("Data loss computed in {}ms", start_time.elapsed().as_millis());
    }

    // Compute final coverage result
    let frame_names: Vec<String> = req.frames.iter().map(|f| f.frame.clone()).collect();
    let elapsed = start_time.elapsed().as_millis();
    tracing::info!("History analysis complete in {}ms", elapsed);

    match analyzer.compute_coverage(&frame_names) {
        Ok(result) => Json(result).into_response(),
        Err(e) => error_response(StatusCode::INTERNAL_SERVER_ERROR, &e.to_string()),
    }
}

/// Collect key stats for all frames in parallel.
async fn collect_key_stats_parallel(
    dbx: &DatabricksClient,
    frames: &[FrameConfig],
) -> Vec<Result<FrameKeyStats, String>> {
    let futures: Vec<_> = frames
        .iter()
        .map(|fc| async move {
            let sql = sql_builder::join_key_stats_sql(&fc.frame, &fc.columns);
            match dbx.execute_sql(&sql, 1).await {
                Ok(response) => {
                    let rows_value = batches_to_json(&response.batches, 0, 1);
                    if let Some(row) = get_first_row(&rows_value) {
                        Ok(FrameKeyStats {
                            frame: fc.frame.clone(),
                            columns: fc.columns.clone(),
                            cardinality: row
                                .get("cardinality")
                                .and_then(Value::as_u64)
                                .unwrap_or(0) as usize,
                            null_count: row
                                .get("null_count")
                                .and_then(Value::as_u64)
                                .unwrap_or(0) as usize,
                            total_rows: row
                                .get("total_rows")
                                .and_then(Value::as_u64)
                                .unwrap_or(0) as usize,
                        })
                    } else {
                        Err(format!("No key stats returned for {}", fc.frame))
                    }
                }
                Err(e) => Err(format!("Failed to get key stats for {}: {}", fc.frame, e)),
            }
        })
        .collect();

    join_all(futures).await
}

/// Detect date columns for all frames in parallel.
async fn detect_date_columns_parallel(
    dbx: &DatabricksClient,
    frames: &[FrameConfig],
) -> HashMap<String, String> {
    let futures: Vec<_> = frames
        .iter()
        .map(|fc| async move {
            let schema_sql = sql_builder::describe_table_sql(&fc.frame);
            let result: Option<(String, String)> = match dbx.execute_sql(&schema_sql, 1000).await {
                Ok(response) => {
                    let rows_value = batches_to_json(&response.batches, 0, 1000);
                    let rows = get_rows(&rows_value);
                    let date_col = fc.columns.iter().find(|col_name| {
                        rows.iter().any(|row| {
                            let name = row.get("col_name").and_then(Value::as_str).unwrap_or("");
                            let dtype = row
                                .get("data_type")
                                .and_then(Value::as_str)
                                .unwrap_or("")
                                .to_lowercase();
                            name == *col_name
                                && (dtype.contains("date") || dtype.contains("timestamp"))
                        })
                    });
                    date_col.map(|col| (fc.frame.clone(), col.clone()))
                }
                Err(_) => None,
            };
            result
        })
        .collect();

    let results: Vec<Option<(String, String)>> = join_all(futures).await;
    results.into_iter().flatten().collect()
}

/// Collect temporal stats (buckets and ranges) for all frames in parallel.
async fn collect_temporal_stats_parallel(
    dbx: &DatabricksClient,
    frames: &[FrameConfig],
    frame_date_columns: &HashMap<String, String>,
    bucket: &str,
) -> Vec<(Option<FrameTemporalStats>, Option<TemporalRangeStats>)> {
    let futures: Vec<_> = frames
        .iter()
        .map(|fc| async move {
            let date_col = match frame_date_columns.get(&fc.frame) {
                Some(col) => col,
                None => return (None, None),
            };

            // Run bucket and range queries in parallel for each frame
            let bucket_sql = sql_builder::temporal_buckets_sql(&fc.frame, date_col, bucket);
            let range_sql = sql_builder::temporal_range_sql(&fc.frame, date_col);

            let (bucket_result, range_result) = tokio::join!(
                dbx.execute_sql(&bucket_sql, 1000),
                dbx.execute_sql(&range_sql, 1)
            );

            let temporal_stats = bucket_result.ok().map(|response| {
                let rows_value = batches_to_json(&response.batches, 0, 1000);
                let rows = get_rows(&rows_value);
                let buckets: HashMap<String, usize> = rows
                    .iter()
                    .filter_map(|row| {
                        let bucket_key = row.get("bucket").and_then(Value::as_str)?;
                        let count = row.get("row_count").and_then(Value::as_u64)? as usize;
                        Some((bucket_key.to_string(), count))
                    })
                    .collect();

                let min = rows
                    .first()
                    .and_then(|r| r.get("min_date").and_then(Value::as_str).map(String::from));
                let max = rows
                    .last()
                    .and_then(|r| r.get("max_date").and_then(Value::as_str).map(String::from));

                FrameTemporalStats {
                    frame: fc.frame.clone(),
                    column: date_col.clone(),
                    bucket_size: bucket.to_string(),
                    min,
                    max,
                    buckets,
                }
            });

            let range_stats = range_result.ok().and_then(|response| {
                let rows_value = batches_to_json(&response.batches, 0, 1);
                get_first_row(&rows_value).map(|row| TemporalRangeStats {
                    frame: fc.frame.clone(),
                    column: date_col.clone(),
                    granularity: bucket.to_string(),
                    min_date: row
                        .get("min_date")
                        .and_then(Value::as_str)
                        .map(String::from),
                    max_date: row
                        .get("max_date")
                        .and_then(Value::as_str)
                        .map(String::from),
                    total_rows: row.get("total_rows").and_then(Value::as_u64).unwrap_or(0) as usize,
                    null_dates: row.get("null_dates").and_then(Value::as_u64).unwrap_or(0) as usize,
                    distinct_dates: row
                        .get("distinct_dates")
                        .and_then(Value::as_u64)
                        .unwrap_or(0) as usize,
                    internal_gaps: vec![],
                })
            });

            (temporal_stats, range_stats)
        })
        .collect();

    join_all(futures).await
}

/// Compute overlaps for all join pairs in parallel.
async fn compute_overlaps_parallel(
    dbx: &DatabricksClient,
    join_pairs: &[JoinPair],
) -> Vec<Result<PairwiseOverlap, String>> {
    let futures: Vec<_> = join_pairs
        .iter()
        .map(|jp| async move {
            let sql = sql_builder::join_overlap_sql(
                &jp.source_frame,
                &jp.target_frame,
                &jp.source_keys,
                &jp.target_keys,
            );

            match dbx.execute_sql(&sql, 1).await {
                Ok(response) => {
                    let rows_value = batches_to_json(&response.batches, 0, 1);
                    if let Some(row) = get_first_row(&rows_value) {
                        Ok(PairwiseOverlap {
                            frame1: jp.source_frame.clone(),
                            frame2: jp.target_frame.clone(),
                            left_total: row
                                .get("left_total")
                                .and_then(Value::as_u64)
                                .unwrap_or(0) as usize,
                            right_total: row
                                .get("right_total")
                                .and_then(Value::as_u64)
                                .unwrap_or(0) as usize,
                            left_only: row
                                .get("left_only")
                                .and_then(Value::as_u64)
                                .unwrap_or(0) as usize,
                            right_only: row
                                .get("right_only")
                                .and_then(Value::as_u64)
                                .unwrap_or(0) as usize,
                            both: row.get("both_count").and_then(Value::as_u64).unwrap_or(0)
                                as usize,
                            overlap_pct: row
                                .get("overlap_pct")
                                .and_then(Value::as_f64)
                                .unwrap_or(0.0),
                        })
                    } else {
                        Err(format!(
                            "No overlap results for {} <-> {}",
                            jp.source_frame, jp.target_frame
                        ))
                    }
                }
                Err(e) => Err(format!(
                    "Failed to compute overlap between {} and {}: {}",
                    jp.source_frame, jp.target_frame, e
                )),
            }
        })
        .collect();

    join_all(futures).await
}

/// Compute overlap bounds for all frames in parallel.
async fn compute_overlap_bounds_parallel(
    dbx: &DatabricksClient,
    frames: &[FrameConfig],
    frame_date_columns: &HashMap<String, String>,
) -> (Option<String>, Option<String>) {
    // Collect frames with date columns and build their futures
    let frame_configs: Vec<_> = frames
        .iter()
        .filter_map(|fc| {
            frame_date_columns.get(&fc.frame).map(|date_col| {
                (fc.frame.clone(), date_col.clone())
            })
        })
        .collect();

    let futures: Vec<_> = frame_configs
        .iter()
        .map(|(frame, date_col)| async move {
            let sql = sql_builder::temporal_range_sql(frame, date_col);
            let result: Option<(Option<String>, Option<String>)> = match dbx.execute_sql(&sql, 1).await {
                Ok(response) => {
                    let rows_value = batches_to_json(&response.batches, 0, 1);
                    get_first_row(&rows_value).map(|row| {
                        let min = row.get("min_date").and_then(Value::as_str).map(String::from);
                        let max = row.get("max_date").and_then(Value::as_str).map(String::from);
                        (min, max)
                    })
                }
                Err(_) => None,
            };
            result
        })
        .collect();

    let results: Vec<Option<(Option<String>, Option<String>)>> = join_all(futures).await;

    let mut min_dates: Vec<String> = Vec::new();
    let mut max_dates: Vec<String> = Vec::new();

    for result in results.into_iter().flatten() {
        if let Some(min) = result.0 {
            min_dates.push(min);
        }
        if let Some(max) = result.1 {
            max_dates.push(max);
        }
    }

    let overlap_start = min_dates.iter().max().cloned();
    let overlap_end = max_dates.iter().min().cloned();

    (overlap_start, overlap_end)
}

/// Compute data loss for all frames in parallel.
async fn compute_data_loss_parallel(
    dbx: &DatabricksClient,
    frames: &[FrameConfig],
    frame_date_columns: &HashMap<String, String>,
    overlap_start: &str,
    overlap_end: &str,
) -> Vec<Option<FrameDataLoss>> {
    let futures: Vec<_> = frames
        .iter()
        .filter_map(|fc| {
            frame_date_columns.get(&fc.frame).map(|date_col| {
                let frame = fc.frame.clone();
                let date_col = date_col.clone();
                let start = overlap_start.to_string();
                let end = overlap_end.to_string();
                async move {
                    let sql = sql_builder::temporal_loss_sql(&frame, &date_col, &start, &end);
                    match dbx.execute_sql(&sql, 1).await {
                        Ok(response) => {
                            let rows_value = batches_to_json(&response.batches, 0, 1);
                            get_first_row(&rows_value).map(|row| FrameDataLoss {
                                frame: frame.clone(),
                                rows_before_overlap: row
                                    .get("rows_before")
                                    .and_then(Value::as_u64)
                                    .unwrap_or(0) as usize,
                                rows_after_overlap: row
                                    .get("rows_after")
                                    .and_then(Value::as_u64)
                                    .unwrap_or(0) as usize,
                                total_lost: row
                                    .get("total_lost")
                                    .and_then(Value::as_u64)
                                    .unwrap_or(0) as usize,
                                pct_lost: row
                                    .get("pct_lost")
                                    .and_then(Value::as_f64)
                                    .unwrap_or(0.0),
                                range_lost_before: None,
                                range_lost_after: None,
                            })
                        }
                        Err(_) => None,
                    }
                }
            })
        })
        .collect();

    join_all(futures).await
}

fn error_response(status: StatusCode, msg: &str) -> axum::response::Response {
    (status, Json(json!({"error": msg}))).into_response()
}
