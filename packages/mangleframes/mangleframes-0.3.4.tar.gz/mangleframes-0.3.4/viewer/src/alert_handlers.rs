//! Alert SQL generation and evaluation handlers for Databricks SQL alerts.

use axum::{
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;

use crate::{
    arrow_reader::batches_to_json,
    sql_builder::{
        alert_data_freshness_sql, alert_duplicate_keys_sql, alert_null_rate_sql,
        alert_reconciliation_sql, alert_row_count_sql, alert_threshold_sql,
        generate_databricks_alert_query,
    },
    web_server::AppState,
};

// Helper function for error responses
fn error_response(status: StatusCode, msg: &str) -> Response {
    (status, Json(json!({"error": msg}))).into_response()
}

// ============ Alert Types ============

#[derive(Deserialize, Serialize, Clone, Debug)]
#[serde(rename_all = "snake_case")]
pub enum AlertType {
    Threshold,
    NullRate,
    RowCount,
    DataFreshness,
    DuplicateKeys,
    Reconciliation,
}

#[derive(Deserialize, Serialize, Clone, Debug)]
#[serde(rename_all = "snake_case")]
pub enum AlertSeverity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

// ============ Request/Response Types ============

#[derive(Deserialize, Debug)]
pub struct ThresholdAlertRequest {
    pub name: String,
    pub table: String,
    pub column: String,
    pub operator: String,
    pub threshold: f64,
    pub severity: Option<AlertSeverity>,
}

#[derive(Deserialize, Debug)]
pub struct NullRateAlertRequest {
    pub name: String,
    pub table: String,
    pub column: String,
    pub max_null_pct: f64,
    pub severity: Option<AlertSeverity>,
}

#[derive(Deserialize, Debug)]
pub struct RowCountAlertRequest {
    pub name: String,
    pub table: String,
    pub min_rows: Option<usize>,
    pub max_rows: Option<usize>,
    pub severity: Option<AlertSeverity>,
}

#[derive(Deserialize, Debug)]
pub struct DataFreshnessAlertRequest {
    pub name: String,
    pub table: String,
    pub date_column: String,
    pub max_age_hours: u32,
    pub severity: Option<AlertSeverity>,
}

#[derive(Deserialize, Debug)]
pub struct DuplicateKeysAlertRequest {
    pub name: String,
    pub table: String,
    pub keys: Vec<String>,
    pub max_duplicates: Option<usize>,
    pub severity: Option<AlertSeverity>,
}

#[derive(Deserialize, Debug)]
pub struct ReconciliationAlertRequest {
    pub name: String,
    pub source_table: String,
    pub target_table: String,
    pub join_keys: Vec<String>,
    pub min_match_rate: f64,
    pub severity: Option<AlertSeverity>,
}

#[derive(Serialize)]
pub struct AlertResponse {
    pub name: String,
    pub alert_type: AlertType,
    pub sql: String,
    pub databricks_query: String,
    pub evaluation: Option<AlertEvaluation>,
}

#[derive(Serialize)]
pub struct AlertEvaluation {
    pub status: String,
    pub message: String,
    pub details: Value,
    pub triggered: bool,
}

// ============ Handler Functions ============

/// Generate and optionally evaluate a threshold alert.
pub async fn generate_threshold_alert(
    State(state): State<Arc<AppState>>,
    Json(req): Json<ThresholdAlertRequest>,
) -> impl IntoResponse {
    let sql = match alert_threshold_sql(&req.table, &req.column, &req.operator, req.threshold) {
        Ok(s) => s,
        Err(e) => return error_response(StatusCode::BAD_REQUEST, &e),
    };

    let databricks_query = generate_databricks_alert_query(&sql, "violations", &req.name);

    let evaluation = if let Some(dbx) = &state.databricks_client {
        match dbx.execute_sql(&sql, 1).await {
            Ok(response) => {
                let json_result = batches_to_json(&response.batches, 0, 1);
                if let Some(rows) = json_result.as_array() {
                    if let Some(row) = rows.first() {
                        let violations = row
                            .get("violations")
                            .and_then(|v| v.as_i64())
                            .unwrap_or(0);
                        let total_rows = row
                            .get("total_rows")
                            .and_then(|v| v.as_i64())
                            .unwrap_or(0);
                        let pct = row
                            .get("violation_pct")
                            .and_then(|v| v.as_f64())
                            .unwrap_or(0.0);

                        Some(AlertEvaluation {
                            status: if violations > 0 { "TRIGGERED" } else { "OK" }.to_string(),
                            message: format!(
                                "{}/{} rows ({:.2}%) violate condition: {} {} {}",
                                violations, total_rows, pct, req.column, req.operator, req.threshold
                            ),
                            details: row.clone(),
                            triggered: violations > 0,
                        })
                    } else {
                        None
                    }
                } else {
                    None
                }
            }
            Err(e) => Some(AlertEvaluation {
                status: "ERROR".to_string(),
                message: format!("Failed to evaluate alert: {}", e),
                details: json!({}),
                triggered: false,
            }),
        }
    } else {
        None
    };

    Json(AlertResponse {
        name: req.name,
        alert_type: AlertType::Threshold,
        sql,
        databricks_query,
        evaluation,
    })
    .into_response()
}

/// Generate and optionally evaluate a null rate alert.
pub async fn generate_null_rate_alert(
    State(state): State<Arc<AppState>>,
    Json(req): Json<NullRateAlertRequest>,
) -> impl IntoResponse {
    let sql = alert_null_rate_sql(&req.table, &req.column);
    let databricks_query = generate_databricks_alert_query(&sql, "null_pct", &req.name);

    let evaluation = if let Some(dbx) = &state.databricks_client {
        match dbx.execute_sql(&sql, 1).await {
            Ok(response) => {
                let json_result = batches_to_json(&response.batches, 0, 1);
                if let Some(rows) = json_result.as_array() {
                    if let Some(row) = rows.first() {
                        let null_pct = row.get("null_pct").and_then(|v| v.as_f64()).unwrap_or(0.0);

                        Some(AlertEvaluation {
                            status: if null_pct > req.max_null_pct {
                                "TRIGGERED"
                            } else {
                                "OK"
                            }
                            .to_string(),
                            message: format!(
                                "Null rate: {:.2}% (threshold: {:.2}%)",
                                null_pct, req.max_null_pct
                            ),
                            details: row.clone(),
                            triggered: null_pct > req.max_null_pct,
                        })
                    } else {
                        None
                    }
                } else {
                    None
                }
            }
            Err(e) => Some(AlertEvaluation {
                status: "ERROR".to_string(),
                message: format!("Failed to evaluate alert: {}", e),
                details: json!({}),
                triggered: false,
            }),
        }
    } else {
        None
    };

    Json(AlertResponse {
        name: req.name,
        alert_type: AlertType::NullRate,
        sql,
        databricks_query,
        evaluation,
    })
    .into_response()
}

/// Generate and optionally evaluate a row count alert.
pub async fn generate_row_count_alert(
    State(state): State<Arc<AppState>>,
    Json(req): Json<RowCountAlertRequest>,
) -> impl IntoResponse {
    let sql = match alert_row_count_sql(&req.table, req.min_rows, req.max_rows) {
        Ok(s) => s,
        Err(e) => return error_response(StatusCode::BAD_REQUEST, &e),
    };

    let databricks_query = generate_databricks_alert_query(&sql, "row_count", &req.name);

    let evaluation = if let Some(dbx) = &state.databricks_client {
        match dbx.execute_sql(&sql, 1).await {
            Ok(response) => {
                let json_result = batches_to_json(&response.batches, 0, 1);
                if let Some(rows) = json_result.as_array() {
                    if let Some(row) = rows.first() {
                        let status = row
                            .get("status")
                            .and_then(|v| v.as_str())
                            .unwrap_or("unknown");
                        let row_count = row
                            .get("row_count")
                            .and_then(|v| v.as_i64())
                            .unwrap_or(0);

                        Some(AlertEvaluation {
                            status: if status != "within_range" && status != "above_minimum" {
                                "TRIGGERED"
                            } else {
                                "OK"
                            }
                            .to_string(),
                            message: format!("Row count: {} (status: {})", row_count, status),
                            details: row.clone(),
                            triggered: status != "within_range" && status != "above_minimum",
                        })
                    } else {
                        None
                    }
                } else {
                    None
                }
            }
            Err(e) => Some(AlertEvaluation {
                status: "ERROR".to_string(),
                message: format!("Failed to evaluate alert: {}", e),
                details: json!({}),
                triggered: false,
            }),
        }
    } else {
        None
    };

    Json(AlertResponse {
        name: req.name,
        alert_type: AlertType::RowCount,
        sql,
        databricks_query,
        evaluation,
    })
    .into_response()
}

/// Generate and optionally evaluate a data freshness alert.
pub async fn generate_data_freshness_alert(
    State(state): State<Arc<AppState>>,
    Json(req): Json<DataFreshnessAlertRequest>,
) -> impl IntoResponse {
    let sql = alert_data_freshness_sql(&req.table, &req.date_column, req.max_age_hours);
    let databricks_query =
        generate_databricks_alert_query(&sql, "freshness_status", &req.name);

    let evaluation = if let Some(dbx) = &state.databricks_client {
        match dbx.execute_sql(&sql, 1).await {
            Ok(response) => {
                let json_result = batches_to_json(&response.batches, 0, 1);
                if let Some(rows) = json_result.as_array() {
                    if let Some(row) = rows.first() {
                        let status = row
                            .get("freshness_status")
                            .and_then(|v| v.as_str())
                            .unwrap_or("unknown");
                        let hours = row
                            .get("hours_since_update")
                            .and_then(|v| v.as_i64())
                            .unwrap_or(0);

                        Some(AlertEvaluation {
                            status: if status == "stale" { "TRIGGERED" } else { "OK" }.to_string(),
                            message: format!(
                                "Data is {} hours old (max allowed: {} hours)",
                                hours, req.max_age_hours
                            ),
                            details: row.clone(),
                            triggered: status == "stale",
                        })
                    } else {
                        None
                    }
                } else {
                    None
                }
            }
            Err(e) => Some(AlertEvaluation {
                status: "ERROR".to_string(),
                message: format!("Failed to evaluate alert: {}", e),
                details: json!({}),
                triggered: false,
            }),
        }
    } else {
        None
    };

    Json(AlertResponse {
        name: req.name,
        alert_type: AlertType::DataFreshness,
        sql,
        databricks_query,
        evaluation,
    })
    .into_response()
}

/// Generate and optionally evaluate a duplicate keys alert.
pub async fn generate_duplicate_keys_alert(
    State(state): State<Arc<AppState>>,
    Json(req): Json<DuplicateKeysAlertRequest>,
) -> impl IntoResponse {
    let sql = match alert_duplicate_keys_sql(&req.table, &req.keys, req.max_duplicates) {
        Ok(s) => s,
        Err(e) => return error_response(StatusCode::BAD_REQUEST, &e),
    };

    let databricks_query =
        generate_databricks_alert_query(&sql, "duplicate_key_count", &req.name);

    let evaluation = if let Some(dbx) = &state.databricks_client {
        match dbx.execute_sql(&sql, 1).await {
            Ok(response) => {
                let json_result = batches_to_json(&response.batches, 0, 1);
                if let Some(rows) = json_result.as_array() {
                    if let Some(row) = rows.first() {
                        let dupe_count = row
                            .get("duplicate_key_count")
                            .and_then(|v| v.as_i64())
                            .unwrap_or(0);
                        let max_dupes = row
                            .get("max_duplicates")
                            .and_then(|v| v.as_i64())
                            .unwrap_or(0);

                        let triggered = if let Some(max) = req.max_duplicates {
                            max_dupes > max as i64
                        } else {
                            dupe_count > 0
                        };

                        Some(AlertEvaluation {
                            status: if triggered { "TRIGGERED" } else { "OK" }.to_string(),
                            message: format!(
                                "Found {} duplicate keys with max {} duplicates per key",
                                dupe_count, max_dupes
                            ),
                            details: row.clone(),
                            triggered,
                        })
                    } else {
                        None
                    }
                } else {
                    None
                }
            }
            Err(e) => Some(AlertEvaluation {
                status: "ERROR".to_string(),
                message: format!("Failed to evaluate alert: {}", e),
                details: json!({}),
                triggered: false,
            }),
        }
    } else {
        None
    };

    Json(AlertResponse {
        name: req.name,
        alert_type: AlertType::DuplicateKeys,
        sql,
        databricks_query,
        evaluation,
    })
    .into_response()
}

/// Generate and optionally evaluate a reconciliation alert.
pub async fn generate_reconciliation_alert(
    State(state): State<Arc<AppState>>,
    Json(req): Json<ReconciliationAlertRequest>,
) -> impl IntoResponse {
    let sql = match alert_reconciliation_sql(
        &req.source_table,
        &req.target_table,
        &req.join_keys,
        req.min_match_rate,
    ) {
        Ok(s) => s,
        Err(e) => return error_response(StatusCode::BAD_REQUEST, &e),
    };

    let databricks_query = generate_databricks_alert_query(&sql, "match_rate_pct", &req.name);

    let evaluation = if let Some(dbx) = &state.databricks_client {
        match dbx.execute_sql(&sql, 1).await {
            Ok(response) => {
                let json_result = batches_to_json(&response.batches, 0, 1);
                if let Some(rows) = json_result.as_array() {
                    if let Some(row) = rows.first() {
                        let match_rate = row
                            .get("match_rate_pct")
                            .and_then(|v| v.as_f64())
                            .unwrap_or(0.0);
                        let status = row
                            .get("alert_status")
                            .and_then(|v| v.as_str())
                            .unwrap_or("unknown");

                        Some(AlertEvaluation {
                            status: if status == "below_threshold" {
                                "TRIGGERED"
                            } else {
                                "OK"
                            }
                            .to_string(),
                            message: format!(
                                "Match rate: {:.2}% (minimum: {:.2}%)",
                                match_rate, req.min_match_rate
                            ),
                            details: row.clone(),
                            triggered: status == "below_threshold",
                        })
                    } else {
                        None
                    }
                } else {
                    None
                }
            }
            Err(e) => Some(AlertEvaluation {
                status: "ERROR".to_string(),
                message: format!("Failed to evaluate alert: {}", e),
                details: json!({}),
                triggered: false,
            }),
        }
    } else {
        None
    };

    Json(AlertResponse {
        name: req.name,
        alert_type: AlertType::Reconciliation,
        sql,
        databricks_query,
        evaluation,
    })
    .into_response()
}

/// Get alert templates for common scenarios.
pub async fn get_alert_templates() -> impl IntoResponse {
    Json(json!({
        "templates": [
            {
                "name": "High Order Value Alert",
                "type": "threshold",
                "description": "Alert when order amounts exceed threshold",
                "config": {
                    "table": "orders",
                    "column": "total_amount",
                    "operator": ">",
                    "threshold": 10000,
                    "severity": "high"
                }
            },
            {
                "name": "Email Quality Check",
                "type": "null_rate",
                "description": "Monitor email field completeness",
                "config": {
                    "table": "customers",
                    "column": "email",
                    "max_null_pct": 5,
                    "severity": "medium"
                }
            },
            {
                "name": "Daily Data Volume",
                "type": "row_count",
                "description": "Ensure daily data meets expectations",
                "config": {
                    "table": "events",
                    "min_rows": 1000,
                    "max_rows": 1000000,
                    "severity": "critical"
                }
            },
            {
                "name": "Data Freshness Monitor",
                "type": "data_freshness",
                "description": "Alert on stale data",
                "config": {
                    "table": "metrics",
                    "date_column": "updated_at",
                    "max_age_hours": 24,
                    "severity": "high"
                }
            },
            {
                "name": "Unique Key Validation",
                "type": "duplicate_keys",
                "description": "Ensure key uniqueness",
                "config": {
                    "table": "users",
                    "keys": ["user_id"],
                    "max_duplicates": 0,
                    "severity": "critical"
                }
            },
            {
                "name": "Table Sync Verification",
                "type": "reconciliation",
                "description": "Verify table synchronization",
                "config": {
                    "source_table": "source_data",
                    "target_table": "target_data",
                    "join_keys": ["id"],
                    "min_match_rate": 99,
                    "severity": "high"
                }
            }
        ]
    }))
    .into_response()
}

/// Export alert definition for Databricks API.
pub async fn export_alert_for_databricks(
    State(_state): State<Arc<AppState>>,
    Json(alert): Json<AlertResponse>,
) -> impl IntoResponse {
    // Generate Databricks API payload
    let databricks_config = json!({
        "name": alert.name,
        "query": {
            "query_text": alert.databricks_query,
            "warehouse_id": "{{WAREHOUSE_ID}}"  // Placeholder
        },
        "condition": {
            "op": "GREATER_THAN",
            "operand": {
                "column": {"name": "alert_value"}
            },
            "threshold": {
                "value": {"double_value": 0}
            }
        },
        "custom_subject": format!("Alert: {} - {{{{ALERT_STATUS}}}}", alert.name),
        "custom_body": "The alert '{{ALERT_NAME}}' is {{ALERT_STATUS}}. Value: {{QUERY_RESULT_VALUE}}",
        "empty_result_state": "OK"
    });

    Json(json!({
        "alert_definition": databricks_config,
        "instructions": "To create this alert in Databricks:\n1. Replace {{WAREHOUSE_ID}} with your SQL warehouse ID\n2. POST to https://<workspace>.cloud.databricks.com/api/2.0/sql/alerts\n3. Add notification destinations as needed",
        "curl_command": format!(
            "curl -X POST -H 'Authorization: Bearer <TOKEN>' -H 'Content-Type: application/json' https://<workspace>.cloud.databricks.com/api/2.0/sql/alerts -d '{}'",
            serde_json::to_string(&databricks_config).unwrap_or_default()
        )
    }))
    .into_response()
}