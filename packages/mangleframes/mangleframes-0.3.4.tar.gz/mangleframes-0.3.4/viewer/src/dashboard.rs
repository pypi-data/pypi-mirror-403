//! HTML dashboard generation for reconciliation reports.

use chrono::Utc;

/// Metadata for the dashboard report.
pub struct DashboardMetadata {
    pub source_frame: String,
    pub target_frame: String,
    pub source_type: String,
    pub group_by_source: Vec<String>,
    pub group_by_target: Vec<String>,
    pub join_keys_source: Vec<String>,
    pub join_keys_target: Vec<String>,
}

/// Generate a self-contained HTML dashboard report from JSON result.
pub fn generate_reconcile_dashboard(
    result: &serde_json::Value,
    metadata: &DashboardMetadata,
) -> String {
    let timestamp = Utc::now().format("%Y-%m-%d %H:%M:%S UTC").to_string();
    let stats = &result["statistics"];

    let key_match_rate = stats["key_match_rate"].as_f64().unwrap_or(0.0);
    let value_match_rate = stats["value_match_rate"].as_f64().unwrap_or(0.0);
    let source_groups = stats["source_groups"].as_i64().unwrap_or(0);
    let target_groups = stats["target_groups"].as_i64().unwrap_or(0);
    let key_matched_groups = stats["key_matched_groups"].as_i64().unwrap_or(0);
    let value_matched_groups = stats["value_matched_groups"].as_i64().unwrap_or(0);
    let value_mismatched_groups = stats["value_mismatched_groups"].as_i64().unwrap_or(0);
    let source_only_groups = stats["source_only_groups"].as_i64().unwrap_or(0);
    let target_only_groups = stats["target_only_groups"].as_i64().unwrap_or(0);

    // PASS requires both key match rate >= 99% AND value match rate >= 99%
    let status_class = if key_match_rate >= 0.99 && value_match_rate >= 0.99 { "pass" } else { "warn" };
    let status_text = if key_match_rate >= 0.99 && value_match_rate >= 0.99 { "PASS" } else { "REVIEW" };

    let source_only_rows = result["source_only"]["rows"].as_array();
    let target_only_rows = result["target_only"]["rows"].as_array();
    let matched_rows = result["matched_rows"]["rows"].as_array();
    let mismatched_rows = result["mismatched_rows"]["rows"].as_array();
    let column_totals = result["column_totals"].as_array();

    format!(
        r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reconciliation Report - {} vs {}</title>
    <style>{}</style>
</head>
<body>
    <header>
        <h1>Reconciliation Report</h1>
        <div class="status-badge {}">{}</div>
    </header>

    <section class="metadata">
        <h2>Report Details</h2>
        <table class="metadata-table">
            <tr><td>Generated</td><td>{}</td></tr>
            <tr><td>Source Frame</td><td>{} ({})</td></tr>
            <tr><td>Target Frame</td><td>{}</td></tr>
            <tr><td>Source Group By</td><td>{}</td></tr>
            <tr><td>Target Group By</td><td>{}</td></tr>
            <tr><td>Join Keys (Source)</td><td>{}</td></tr>
            <tr><td>Join Keys (Target)</td><td>{}</td></tr>
        </table>
    </section>

    <section class="summary">
        <h2>Executive Summary</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{:.1}%</div>
                <div class="stat-label">Key Match Rate</div>
            </div>
            <div class="stat-card {}">
                <div class="stat-value">{:.1}%</div>
                <div class="stat-label">Value Match Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{}</div>
                <div class="stat-label">Source Groups</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{}</div>
                <div class="stat-label">Target Groups</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{}</div>
                <div class="stat-label">Key Matched</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{}</div>
                <div class="stat-label">Value Matched</div>
            </div>
            <div class="stat-card highlight-error">
                <div class="stat-value">{}</div>
                <div class="stat-label">Value Mismatched</div>
            </div>
            <div class="stat-card highlight-warn">
                <div class="stat-value">{}</div>
                <div class="stat-label">Source Only</div>
            </div>
            <div class="stat-card highlight-warn">
                <div class="stat-value">{}</div>
                <div class="stat-label">Target Only</div>
            </div>
        </div>
    </section>

    <section class="column-totals">
        <h2>Column Totals Comparison</h2>
        {}
    </section>

    <section class="value-mismatches">
        <h2>Value Mismatches ({} groups)</h2>
        <p class="section-description">Rows where keys match but aggregated values differ beyond tolerance (0.01)</p>
        {}
    </section>

    <section class="differences">
        <h2>Key Differences</h2>

        <div class="subsection">
            <h3>Source Only ({} groups)</h3>
            {}
        </div>

        <div class="subsection">
            <h3>Target Only ({} groups)</h3>
            {}
        </div>
    </section>

    <section class="matched-sample">
        <h2>Value Matched Sample ({} of {} groups)</h2>
        {}
    </section>

    <footer>
        <p>Generated by MangleFrames | {}</p>
    </footer>
</body>
</html>"#,
        metadata.source_frame,
        metadata.target_frame,
        get_css(),
        status_class,
        status_text,
        timestamp,
        metadata.source_frame,
        metadata.source_type,
        metadata.target_frame,
        metadata.group_by_source.join(", "),
        metadata.group_by_target.join(", "),
        metadata.join_keys_source.join(", "),
        metadata.join_keys_target.join(", "),
        key_match_rate * 100.0,
        if value_match_rate < 0.99 { "highlight-error" } else { "" },
        value_match_rate * 100.0,
        source_groups,
        target_groups,
        key_matched_groups,
        value_matched_groups,
        value_mismatched_groups,
        source_only_groups,
        target_only_groups,
        render_column_totals_table(column_totals),
        value_mismatched_groups,
        render_json_rows_table(mismatched_rows, 100),
        source_only_groups,
        render_json_rows_table(source_only_rows, 100),
        target_only_groups,
        render_json_rows_table(target_only_rows, 100),
        matched_rows.map(|r| r.len()).unwrap_or(0),
        value_matched_groups,
        render_json_rows_table(matched_rows, 50),
        timestamp
    )
}

fn get_css() -> &'static str {
    r#"
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.5;
    color: #1a1a2e;
    background: #fff;
    padding: 40px;
    max-width: 1200px;
    margin: 0 auto;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid #1a1a2e;
    padding-bottom: 20px;
    margin-bottom: 30px;
}

h1 { font-size: 28px; font-weight: 700; }
h2 { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #1a1a2e; }
h3 { font-size: 16px; font-weight: 600; margin-bottom: 12px; color: #444; }

.status-badge {
    padding: 8px 20px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 14px;
    text-transform: uppercase;
}

.status-badge.pass { background: #d4edda; color: #155724; }
.status-badge.warn { background: #fff3cd; color: #856404; }

section { margin-bottom: 40px; }

.metadata-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

.metadata-table td {
    padding: 8px 12px;
    border-bottom: 1px solid #e0e0e0;
}

.metadata-table td:first-child {
    font-weight: 600;
    width: 200px;
    color: #666;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px;
}

.stat-card {
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}

.stat-card.highlight-warn { border-left: 4px solid #ffc107; }
.stat-card.highlight-error { border-left: 4px solid #dc3545; background: #fff5f5; }

.section-description {
    font-size: 13px;
    color: #666;
    margin-bottom: 16px;
    font-style: italic;
}

.stat-value {
    font-size: 28px;
    font-weight: 700;
    color: #1a1a2e;
    font-family: 'SF Mono', Monaco, monospace;
}

.stat-label {
    font-size: 12px;
    color: #666;
    text-transform: uppercase;
    margin-top: 4px;
}

table.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    margin-top: 12px;
}

table.data-table th,
table.data-table td {
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
}

table.data-table th {
    background: #f8f9fa;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    color: #666;
}

table.data-table tr:hover { background: #f8f9fa; }

.diff-positive { color: #28a745; }
.diff-negative { color: #dc3545; }
.diff-zero { color: #666; }

.subsection { margin-bottom: 24px; }

.empty-notice {
    padding: 20px;
    text-align: center;
    color: #666;
    font-style: italic;
    background: #f8f9fa;
    border-radius: 4px;
}

footer {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #e0e0e0;
    text-align: center;
    font-size: 12px;
    color: #666;
}

@media print {
    body { padding: 20px; }
    section { page-break-inside: avoid; }
}
"#
}

fn render_column_totals_table(totals: Option<&Vec<serde_json::Value>>) -> String {
    let totals = match totals {
        Some(t) if !t.is_empty() => t,
        _ => return r#"<div class="empty-notice">No aggregation columns</div>"#.to_string(),
    };

    let mut rows = String::new();
    for total in totals {
        let column = total["column"].as_str().unwrap_or("");
        let aggregation = total["aggregation"].as_str().unwrap_or("");
        let source_total = total["source_total"].as_f64();
        let target_total = total["target_total"].as_f64();
        let difference = total["difference"].as_f64();
        let percent_diff = total["percent_diff"].as_f64();

        let diff_class = match difference {
            Some(d) if d > 0.001 => "diff-positive",
            Some(d) if d < -0.001 => "diff-negative",
            _ => "diff-zero",
        };

        rows.push_str(&format!(
            r#"<tr>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td class="{}">{}</td>
                <td>{}</td>
            </tr>"#,
            column,
            aggregation,
            format_number(source_total),
            format_number(target_total),
            diff_class,
            format_number(difference),
            format_percent(percent_diff)
        ));
    }

    format!(
        r#"<table class="data-table">
            <thead>
                <tr>
                    <th>Column</th>
                    <th>Aggregation</th>
                    <th>Source Total</th>
                    <th>Target Total</th>
                    <th>Difference</th>
                    <th>% Diff</th>
                </tr>
            </thead>
            <tbody>{}</tbody>
        </table>"#,
        rows
    )
}

fn render_json_rows_table(rows: Option<&Vec<serde_json::Value>>, max_rows: usize) -> String {
    let rows = match rows {
        Some(r) if !r.is_empty() => r,
        _ => return r#"<div class="empty-notice">No rows to display</div>"#.to_string(),
    };

    let columns: Vec<String> = if let Some(obj) = rows[0].as_object() {
        obj.keys().cloned().collect()
    } else {
        return r#"<div class="empty-notice">Invalid data format</div>"#.to_string();
    };

    let header: String = columns.iter()
        .map(|c| format!("<th>{}</th>", html_escape(c)))
        .collect();

    let display_rows = rows.iter().take(max_rows);
    let mut body = String::new();
    for row in display_rows {
        if let Some(obj) = row.as_object() {
            let cells: String = columns.iter()
                .map(|col| {
                    let val = obj.get(col)
                        .map(|v| format_json_value(v))
                        .unwrap_or_default();
                    format!("<td>{}</td>", html_escape(&val))
                })
                .collect();
            body.push_str(&format!("<tr>{}</tr>", cells));
        }
    }

    let truncated_notice = if rows.len() > max_rows {
        format!(r#"<div class="empty-notice">Showing {} of {} rows</div>"#, max_rows, rows.len())
    } else {
        String::new()
    };

    format!(
        r#"<table class="data-table">
            <thead><tr>{}</tr></thead>
            <tbody>{}</tbody>
        </table>
        {}"#,
        header, body, truncated_notice
    )
}

fn format_number(val: Option<f64>) -> String {
    match val {
        Some(v) if v.abs() >= 1_000_000.0 => format!("{:.2}M", v / 1_000_000.0),
        Some(v) if v.abs() >= 1_000.0 => format!("{:.2}K", v / 1_000.0),
        Some(v) => format!("{:.2}", v),
        None => "-".to_string(),
    }
}

fn format_percent(val: Option<f64>) -> String {
    match val {
        Some(v) => format!("{:.2}%", v),
        None => "-".to_string(),
    }
}

fn format_json_value(val: &serde_json::Value) -> String {
    match val {
        serde_json::Value::Null => "".to_string(),
        serde_json::Value::Bool(b) => b.to_string(),
        serde_json::Value::Number(n) => {
            if let Some(f) = n.as_f64() {
                if f.abs() >= 1_000_000.0 {
                    format!("{:.2}M", f / 1_000_000.0)
                } else if f.abs() >= 1_000.0 {
                    format!("{:.2}K", f / 1_000.0)
                } else {
                    format!("{:.2}", f)
                }
            } else {
                n.to_string()
            }
        }
        serde_json::Value::String(s) => s.clone(),
        _ => val.to_string(),
    }
}

fn html_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}
