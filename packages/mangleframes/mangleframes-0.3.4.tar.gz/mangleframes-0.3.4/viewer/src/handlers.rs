//! HTTP route handlers for the web API.

use std::sync::Arc;
use std::time::Instant;

use arrow::array::Array;
use axum::body::Body;
use axum::extract::{Path, Query, State};
use axum::http::{header, Response, StatusCode};
use axum::response::IntoResponse;
use axum::Json;
use rust_embed::RustEmbed;
use serde::Deserialize;
use serde_json::json;

use crate::arrow_reader::{batches_to_json, batches_to_json_bytes, total_row_count};
use crate::export;
use crate::perf::TimingSample;
use crate::sql_builder;
use crate::stats;
use crate::web_server::{AppState, CachedFrame, JsonCacheEntry, JsonCacheKey};

use tracing::info;

#[derive(RustEmbed)]
#[folder = "static/dist"]
struct Asset;

fn get_content_type(path: &str) -> &'static str {
    if path.ends_with(".html") {
        "text/html"
    } else if path.ends_with(".js") {
        "application/javascript"
    } else if path.ends_with(".css") {
        "text/css"
    } else if path.ends_with(".svg") {
        "image/svg+xml"
    } else if path.ends_with(".json") {
        "application/json"
    } else if path.ends_with(".woff2") {
        "font/woff2"
    } else if path.ends_with(".woff") {
        "font/woff"
    } else {
        "application/octet-stream"
    }
}

pub async fn serve_static(Path(path): Path<String>) -> impl IntoResponse {
    let asset_path = format!("assets/{}", path);

    match Asset::get(&asset_path) {
        Some(content) => {
            let content_type = get_content_type(&asset_path);
            Response::builder()
                .header(header::CONTENT_TYPE, content_type)
                .header(header::CACHE_CONTROL, "public, max-age=31536000")
                .body(Body::from(content.data.into_owned()))
                .unwrap()
        }
        None => Response::builder()
            .status(StatusCode::NOT_FOUND)
            .body(Body::from("Not found"))
            .unwrap(),
    }
}

pub async fn serve_index() -> impl IntoResponse {
    match Asset::get("index.html") {
        Some(content) => Response::builder()
            .header(header::CONTENT_TYPE, "text/html")
            .body(Body::from(content.data.into_owned()))
            .unwrap(),
        None => Response::builder()
            .status(StatusCode::NOT_FOUND)
            .header(header::CONTENT_TYPE, "text/plain")
            .body(Body::from("Frontend not built. Run: cd viewer/frontend && npm install && npm run build"))
            .unwrap(),
    }
}

pub async fn list_frames(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let dbx = match &state.databricks_client {
        Some(c) => c,
        None => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(json!({"error": "No Databricks connection available"})),
            )
                .into_response();
        }
    };

    if !dbx.is_connected().await {
        return (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(json!({"error": "Databricks not connected"})),
        )
            .into_response();
    }

    let sql = sql_builder::list_tables_sql();
    match dbx.execute_sql(&sql, 1000).await {
        Ok(response) => {
            let mut tables = Vec::new();
            for batch in &response.batches {
                let schema = batch.schema();
                // Look for tableName column (SHOW TABLES output)
                let name_idx = schema
                    .index_of("tableName")
                    .or_else(|_| schema.index_of("table_name"))
                    .unwrap_or(1);

                if let Some(col) = batch.columns().get(name_idx) {
                    if let Some(arr) = col.as_any().downcast_ref::<arrow::array::StringArray>() {
                        for i in 0..arr.len() {
                            if !arr.is_null(i) {
                                tables.push(arr.value(i).to_string());
                            }
                        }
                    }
                }
            }
            Json(json!({"frames": tables})).into_response()
        }
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": e.to_string()})),
        )
            .into_response(),
    }
}

pub async fn get_schema(
    State(state): State<Arc<AppState>>,
    Path(name): Path<String>,
) -> impl IntoResponse {
    let dbx = match &state.databricks_client {
        Some(c) => c,
        None => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(json!({"error": "No Databricks connection available"})),
            )
                .into_response();
        }
    };

    let sql = sql_builder::describe_table_sql(&name);
    match dbx.execute_sql(&sql, 1000).await {
        Ok(response) => {
            let mut columns = Vec::new();
            for batch in &response.batches {
                let schema = batch.schema();
                let name_idx = schema.index_of("col_name").unwrap_or(0);
                let type_idx = schema.index_of("data_type").unwrap_or(1);

                let name_col = batch.column(name_idx);
                let type_col = batch.column(type_idx);

                if let (Some(names), Some(types)) = (
                    name_col.as_any().downcast_ref::<arrow::array::StringArray>(),
                    type_col.as_any().downcast_ref::<arrow::array::StringArray>(),
                ) {
                    for i in 0..batch.num_rows() {
                        if names.is_null(i) {
                            continue;
                        }
                        let col_name = names.value(i);
                        // Skip partition/metadata rows
                        if col_name.starts_with('#') || col_name.is_empty() {
                            continue;
                        }
                        columns.push(json!({
                            "name": col_name,
                            "type": types.value(i),
                            "nullable": true
                        }));
                    }
                }
            }
            Json(json!({"columns": columns})).into_response()
        }
        Err(e) => (
            StatusCode::NOT_FOUND,
            Json(json!({"error": e.to_string()})),
        )
            .into_response(),
    }
}

#[derive(Deserialize)]
pub struct DataQuery {
    offset: Option<usize>,
    limit: Option<usize>,
}


pub async fn get_data(
    State(state): State<Arc<AppState>>,
    Path(name): Path<String>,
    Query(query): Query<DataQuery>,
) -> impl IntoResponse {
    let offset = query.offset.unwrap_or(0);
    let limit = query.limit.unwrap_or(100).min(10000);
    let total_start = Instant::now();

    // Check JSON cache first for instant response
    let cache_key = JsonCacheKey {
        frame: name.clone(),
        offset,
        limit,
    };
    {
        let json_cache = state.json_cache.read().await;
        if let Some(entry) = json_cache.get(&cache_key) {
            let total_ms = total_start.elapsed().as_millis() as u64;
            record_sample(&state, &name, limit, 0, 0, 0, 0, 0, 0, total_ms, true).await;
            return Response::builder()
                .header(header::CONTENT_TYPE, "application/json")
                .body(Body::from(entry.data.clone()))
                .unwrap()
                .into_response();
        }
    }

    // Check frame cache
    let cache = state.cache.read().await;
    if let Some(cached) = cache.get(&name) {
        let json_start = Instant::now();
        let (rows_bytes, rows_len) = batches_to_json_bytes(&cached.batches, offset, limit);
        let json_ms = json_start.elapsed().as_millis() as u64;
        let total = total_row_count(&cached.batches);
        let total_ms = total_start.elapsed().as_millis() as u64;

        record_sample(&state, &name, rows_len, 0, 0, 0, 0, 0, json_ms, total_ms, true).await;

        let body = build_response_json(
            &rows_bytes, total, offset, 0, 0, 0, 0, json_ms, total_ms, rows_len, 0, true,
        );

        drop(cache);
        state.evict_json_if_needed().await;
        let mut json_cache = state.json_cache.write().await;
        json_cache.insert(
            cache_key,
            JsonCacheEntry {
                data: body.clone(),
                created: Instant::now(),
            },
        );

        return Response::builder()
            .header(header::CONTENT_TYPE, "application/json")
            .body(Body::from(body))
            .unwrap()
            .into_response();
    }
    drop(cache);

    // Fetch from Databricks via Spark Connect
    let dbx = match &state.databricks_client {
        Some(c) => c,
        None => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(json!({"error": "No Databricks connection available"})),
            )
                .into_response();
        }
    };

    let fetch_limit = (offset + limit).max(10000);
    let sql = sql_builder::select_data_sql(&name, fetch_limit, 0);

    let spark_start = Instant::now();
    match dbx.execute_sql(&sql, fetch_limit).await {
        Ok(response) => {
            let spark_ms = spark_start.elapsed().as_millis() as u64;

            let json_start = Instant::now();
            let (rows_bytes, rows_len) =
                batches_to_json_bytes(&response.batches, offset, limit);
            let json_ms = json_start.elapsed().as_millis() as u64;

            // Get total row count (approximation from fetched data)
            let total = total_row_count(&response.batches);
            let total_ms = total_start.elapsed().as_millis() as u64;

            // Cache the batches
            state.evict_frame_if_needed().await;
            let mut cache = state.cache.write().await;
            cache.insert(
                name.clone(),
                CachedFrame {
                    batches: response.batches,
                    stats: None,
                    last_access: Instant::now(),
                },
            );
            drop(cache);

            record_sample(
                &state, &name, total, 0, spark_ms, 0, 0, 0, json_ms, total_ms, false,
            )
            .await;

            let body = build_response_json(
                &rows_bytes, total, offset, spark_ms, 0, 0, 0, json_ms, total_ms, rows_len, 0,
                false,
            );

            state.evict_json_if_needed().await;
            let mut json_cache = state.json_cache.write().await;
            json_cache.insert(
                cache_key,
                JsonCacheEntry {
                    data: body.clone(),
                    created: Instant::now(),
                },
            );

            Response::builder()
                .header(header::CONTENT_TYPE, "application/json")
                .body(Body::from(body))
                .unwrap()
                .into_response()
        }
        Err(e) => (
            StatusCode::NOT_FOUND,
            Json(json!({"error": e.to_string()})),
        )
            .into_response(),
    }
}

/// Build response JSON directly as bytes, embedding rows without re-parsing
#[allow(clippy::too_many_arguments)]
fn build_response_json(
    rows_bytes: &[u8], total: usize, offset: usize,
    spark_ms: u64, ipc_ms: u64, socket_ms: u64, parse_ms: u64, json_ms: u64, total_ms: u64,
    rows_fetched: usize, bytes_transferred: usize, cached: bool,
) -> Vec<u8> {
    let timing = format!(
        r#"{{"spark_ms":{},"ipc_ms":{},"socket_ms":{},"parse_ms":{},"json_ms":{},"total_ms":{},"rows_fetched":{},"bytes_transferred":{},"cached":{}}}"#,
        spark_ms, ipc_ms, socket_ms, parse_ms, json_ms, total_ms, rows_fetched, bytes_transferred, cached
    );

    let mut result = Vec::with_capacity(rows_bytes.len() + 200);
    result.extend_from_slice(b"{\"rows\":");
    result.extend_from_slice(rows_bytes);
    result.extend_from_slice(b",\"total\":");
    result.extend_from_slice(total.to_string().as_bytes());
    result.extend_from_slice(b",\"offset\":");
    result.extend_from_slice(offset.to_string().as_bytes());
    result.extend_from_slice(b",\"timing\":");
    result.extend_from_slice(timing.as_bytes());
    result.extend_from_slice(b"}");
    result
}

#[allow(clippy::too_many_arguments)]
async fn record_sample(
    state: &AppState, name: &str, rows: usize, bytes: usize,
    spark_ms: u64, ipc_ms: u64, socket_ms: u64, parse_ms: u64, json_ms: u64,
    total_ms: u64, cached: bool,
) {
    state.perf.record(name, TimingSample {
        timestamp: Instant::now(),
        rows, bytes, spark_ms, ipc_ms, socket_ms, parse_ms, json_ms, total_ms, cached,
    }).await;
}

pub async fn get_stats(
    State(state): State<Arc<AppState>>,
    Path(name): Path<String>,
) -> impl IntoResponse {
    info!("Stats requested for frame: {}", name);

    // Step 1: Check cached stats
    {
        let cache = state.cache.read().await;
        if let Some(cached) = cache.get(&name) {
            if let Some(ref stats) = cached.stats {
                info!("Returning cached stats for {}", name);
                return Json(stats.clone()).into_response();
            }
        }
    }

    // Step 2: Databricks direct mode - always use SQL for accurate stats
    if let Some(ref dbx) = state.databricks_client {
        if dbx.is_connected().await {
            info!("Computing stats via Databricks SQL for {}", name);

            // First get schema via DESCRIBE or small query
            let schema_sql = format!("SELECT * FROM {} LIMIT 1", name);
            match dbx.execute_sql(&schema_sql, 1).await {
                Ok(schema_resp) => {
                    if schema_resp.batches.is_empty() {
                        return Json(json!({"row_count": 0, "columns": []})).into_response();
                    }

                    let schema = schema_resp.batches[0].schema();
                    let stats_sql = stats::generate_stats_sql(&name, &schema);

                    match dbx.execute_sql(&stats_sql, 1).await {
                        Ok(stats_resp) => {
                            let result = stats::parse_stats_result(&stats_resp.batches, &schema);
                            return Json(result).into_response();
                        }
                        Err(e) => {
                            return (
                                StatusCode::INTERNAL_SERVER_ERROR,
                                Json(json!({"error": format!("Stats query failed: {}", e)})),
                            )
                                .into_response();
                        }
                    }
                }
                Err(e) => {
                    return (
                        StatusCode::NOT_FOUND,
                        Json(json!({"error": format!("Table not found: {}", e)})),
                    )
                        .into_response();
                }
            }
        }
    }

    // Step 3: Fallback to cached batches (no Databricks connection)
    {
        let cache = state.cache.read().await;
        if let Some(cached) = cache.get(&name) {
            if !cached.batches.is_empty() {
                info!("Computing stats from cached batches for {}", name);
                let computed = stats::compute_stats(&cached.batches);
                drop(cache);

                // Cache the computed stats
                let mut cache = state.cache.write().await;
                if let Some(cached) = cache.get_mut(&name) {
                    cached.stats = Some(computed.clone());
                }
                return Json(computed).into_response();
            }
        }
    }

    // Step 4: No data source available
    (
        StatusCode::NOT_FOUND,
        Json(json!({"error": "No cached data or Databricks connection available"})),
    )
        .into_response()
}

#[derive(Deserialize)]
pub struct ExportRequest {
    format: String,
}

pub async fn export_frame(
    State(state): State<Arc<AppState>>,
    Path(name): Path<String>,
    Json(req): Json<ExportRequest>,
) -> impl IntoResponse {
    let cache = state.cache.read().await;
    let batches = match cache.get(&name) {
        Some(cached) => cached.batches.clone(),
        None => {
            drop(cache);
            // Fetch from Databricks if not cached
            let dbx = match &state.databricks_client {
                Some(c) => c,
                None => {
                    return (StatusCode::SERVICE_UNAVAILABLE, "No Databricks connection")
                        .into_response()
                }
            };

            let sql = sql_builder::select_data_sql(&name, 100000, 0);
            match dbx.execute_sql(&sql, 100000).await {
                Ok(response) => response.batches,
                Err(e) => return (StatusCode::NOT_FOUND, e.to_string()).into_response(),
            }
        }
    };

    let (content_type, data) = match req.format.as_str() {
        "csv" => match export::to_csv(&batches) {
            Ok(d) => ("text/csv", d),
            Err(e) => return (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()).into_response(),
        },
        "json" => match export::to_json(&batches) {
            Ok(d) => ("application/json", d),
            Err(e) => return (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()).into_response(),
        },
        "parquet" => match export::to_parquet(&batches) {
            Ok(d) => ("application/octet-stream", d),
            Err(e) => return (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()).into_response(),
        },
        _ => return (StatusCode::BAD_REQUEST, "Invalid format").into_response(),
    };

    let filename = format!("{}.{}", name, req.format);
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

#[derive(Deserialize)]
pub struct QueryRequest {
    sql: String,
}

pub async fn execute_query(
    State(state): State<Arc<AppState>>,
    Json(req): Json<QueryRequest>,
) -> impl IntoResponse {
    let dbx = match &state.databricks_client {
        Some(c) => c,
        None => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(json!({"error": "No Databricks connection available"})),
            )
                .into_response();
        }
    };

    if !dbx.is_connected().await {
        return (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(json!({"error": "Databricks not connected"})),
        )
            .into_response();
    }

    tracing::info!("Executing SQL via Spark Connect: {}", req.sql);
    match dbx.execute_sql(&req.sql, 1000).await {
        Ok(response) => {
            let rows = batches_to_json(&response.batches, 0, 1000);
            Json(json!({
                "rows": rows,
                "total": response.row_count,
                "timing": { "execution_ms": response.execution_ms }
            }))
            .into_response()
        }
        Err(e) => (
            StatusCode::BAD_REQUEST,
            Json(json!({"error": e.to_string()})),
        )
            .into_response(),
    }
}

pub async fn get_perf_stats(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let frames = state.perf.get_all_metrics().await;
    let global = state.perf.get_global_metrics().await;
    Json(json!({ "frames": frames, "global": global }))
}

#[derive(Deserialize)]
pub struct BenchmarkRequest {
    frame: String,
    sample_sizes: Vec<usize>,
    iterations: Option<usize>,
}

pub async fn run_benchmark(
    State(state): State<Arc<AppState>>,
    Json(req): Json<BenchmarkRequest>,
) -> impl IntoResponse {
    let dbx = match &state.databricks_client {
        Some(c) => c,
        None => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(json!({"error": "No Databricks connection available"})),
            )
                .into_response();
        }
    };

    let iterations = req.iterations.unwrap_or(3);
    let mut results = Vec::with_capacity(req.sample_sizes.len());

    for sample_size in &req.sample_sizes {
        let mut timings = Vec::with_capacity(iterations);

        for _ in 0..iterations {
            // Clear cache to force fresh fetch
            state.cache.write().await.remove(&req.frame);

            let start = Instant::now();
            let sql = sql_builder::select_data_sql(&req.frame, *sample_size, 0);
            match dbx.execute_sql(&sql, *sample_size).await {
                Ok(_) => {
                    let elapsed_ms = start.elapsed().as_millis() as u64;
                    timings.push(elapsed_ms);
                }
                Err(e) => {
                    return (
                        StatusCode::NOT_FOUND,
                        Json(json!({"error": e.to_string()})),
                    )
                        .into_response();
                }
            }
        }

        let avg_ms = timings.iter().sum::<u64>() as f64 / timings.len() as f64;
        let rows_per_sec = *sample_size as f64 / (avg_ms / 1000.0);

        results.push(json!({
            "sample_size": sample_size,
            "iterations": iterations,
            "avg_total_ms": avg_ms,
            "avg_rows_per_sec": rows_per_sec,
            "min_ms": timings.iter().min().unwrap_or(&0),
            "max_ms": timings.iter().max().unwrap_or(&0)
        }));
    }

    Json(json!({ "results": results })).into_response()
}

#[derive(Deserialize)]
pub struct StreamRequest {
    frame: String,
    chunk_size: usize,
    max_chunks: usize,
}

pub async fn stream_benchmark(
    State(state): State<Arc<AppState>>,
    Json(req): Json<StreamRequest>,
) -> impl IntoResponse {
    let dbx = match &state.databricks_client {
        Some(c) => c,
        None => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(json!({"error": "No Databricks connection available"})),
            )
                .into_response();
        }
    };

    let start = Instant::now();
    let mut chunks_processed = 0;
    let mut total_rows = 0;
    let mut chunk_timings = Vec::with_capacity(req.max_chunks);

    for chunk_idx in 0..req.max_chunks {
        let chunk_start = Instant::now();
        let offset = chunk_idx * req.chunk_size;
        let sql = sql_builder::select_data_sql(&req.frame, req.chunk_size, offset);

        match dbx.execute_sql(&sql, req.chunk_size).await {
            Ok(response) => {
                let rows = response.row_count as usize;
                let chunk_ms = chunk_start.elapsed().as_millis() as u64;

                chunks_processed += 1;
                total_rows += rows;
                chunk_timings.push(json!({
                    "chunk": chunk_idx,
                    "rows": rows,
                    "ms": chunk_ms
                }));

                // Stop if we got fewer rows than requested (end of data)
                if rows < req.chunk_size {
                    break;
                }
            }
            Err(e) => {
                return (
                    StatusCode::NOT_FOUND,
                    Json(json!({"error": e.to_string()})),
                )
                    .into_response();
            }
        }
    }

    let elapsed_secs = start.elapsed().as_secs_f64();
    Json(json!({
        "chunks_processed": chunks_processed,
        "total_rows": total_rows,
        "elapsed_seconds": elapsed_secs,
        "rows_per_sec": total_rows as f64 / elapsed_secs,
        "chunk_timings": chunk_timings
    }))
    .into_response()
}
