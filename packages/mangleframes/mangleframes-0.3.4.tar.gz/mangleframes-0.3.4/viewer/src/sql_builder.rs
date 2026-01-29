//! SQL query generation for Spark Connect operations.

use serde_json::Value;

/// Quote an identifier to prevent SQL injection.
pub fn quote_identifier(name: &str) -> String {
    format!("`{}`", name.replace('`', "``"))
}

/// Quote multiple identifiers and join with commas.
pub fn quote_identifiers(names: &[String]) -> String {
    names.iter().map(|n| quote_identifier(n)).collect::<Vec<_>>().join(", ")
}

/// Generate SQL to list all tables/views.
pub fn list_tables_sql() -> String {
    "SHOW TABLES".to_string()
}

/// Generate SQL to describe a table's schema.
pub fn describe_table_sql(table: &str) -> String {
    format!("DESCRIBE TABLE {}", quote_identifier(table))
}

/// Generate SQL to select data with pagination.
pub fn select_data_sql(table: &str, limit: usize, offset: usize) -> String {
    let quoted = quote_identifier(table);
    if offset == 0 {
        format!("SELECT * FROM {} LIMIT {}", quoted, limit)
    } else {
        // Use ROW_NUMBER() for offset support
        format!(
            "SELECT * FROM (SELECT *, ROW_NUMBER() OVER () as __row_num FROM {}) \
             WHERE __row_num > {} AND __row_num <= {} \
             ORDER BY __row_num",
            quoted, offset, offset + limit
        )
    }
}

/// Generate SQL to count total rows in a table.
pub fn count_rows_sql(table: &str) -> String {
    format!("SELECT COUNT(*) as total FROM {}", quote_identifier(table))
}

/// Generate SQL for column statistics.
pub fn stats_sql(table: &str, columns: &[(String, String)]) -> String {
    let quoted_table = quote_identifier(table);
    let mut select_parts = vec!["COUNT(*) AS row_count".to_string()];

    for (col_name, col_type) in columns {
        let quoted = quote_identifier(col_name);
        select_parts.push(format!("COUNT({}) AS {}_non_null", quoted, quote_identifier(&format!("{}_non_null", col_name))));
        select_parts.push(format!(
            "COUNT(*) - COUNT({}) AS {}",
            quoted, quote_identifier(&format!("{}_null", col_name))
        ));

        if is_numeric_type(col_type) {
            select_parts.push(format!("MIN({}) AS {}", quoted, quote_identifier(&format!("{}_min", col_name))));
            select_parts.push(format!("MAX({}) AS {}", quoted, quote_identifier(&format!("{}_max", col_name))));
        }
    }

    format!("SELECT {} FROM {}", select_parts.join(", "), quoted_table)
}

/// Generate SQL for join key analysis.
pub fn join_keys_sql(table: &str, keys: &[String]) -> String {
    let quoted_table = quote_identifier(table);
    let mut select_parts = vec!["COUNT(*) AS total_rows".to_string()];

    for key in keys {
        let quoted = quote_identifier(key);
        select_parts.push(format!("COUNT(DISTINCT {}) AS {}", quoted, quote_identifier(&format!("{}_distinct", key))));
        select_parts.push(format!(
            "COUNT(*) - COUNT({}) AS {}",
            quoted, quote_identifier(&format!("{}_nulls", key))
        ));
    }

    format!("SELECT {} FROM {}", select_parts.join(", "), quoted_table)
}

/// Generate SQL for join analysis between two tables.
/// Returns comprehensive statistics including null/duplicate key counts.
pub fn join_analyze_sql(
    left_table: &str,
    right_table: &str,
    left_keys: &[String],
    right_keys: &[String],
) -> String {
    let left_quoted = quote_identifier(left_table);
    let right_quoted = quote_identifier(right_table);
    let join_cond = build_join_condition("l", "r", left_keys, right_keys);

    // Build null check expressions for composite keys
    let left_null_check = build_null_check("l", left_keys);
    let right_null_check = build_null_check("r", right_keys);

    // Build key expressions for distinct counting
    let left_key_expr = build_key_expr("l", left_keys);
    let right_key_expr = build_key_expr("r", right_keys);

    format!(
        "WITH
  left_stats AS (
    SELECT
      COUNT(*) as total,
      COUNT(DISTINCT {left_key}) as distinct_keys,
      SUM(CASE WHEN {left_null} THEN 1 ELSE 0 END) as null_keys
    FROM {left_table} l
  ),
  right_stats AS (
    SELECT
      COUNT(*) as total,
      COUNT(DISTINCT {right_key}) as distinct_keys,
      SUM(CASE WHEN {right_null} THEN 1 ELSE 0 END) as null_keys
    FROM {right_table} r
  ),
  left_dupes AS (
    SELECT COUNT(*) as cnt FROM (
      SELECT {left_key} FROM {left_table} l
      WHERE NOT ({left_null})
      GROUP BY {left_key} HAVING COUNT(*) > 1
    )
  ),
  right_dupes AS (
    SELECT COUNT(*) as cnt FROM (
      SELECT {right_key} FROM {right_table} r
      WHERE NOT ({right_null})
      GROUP BY {right_key} HAVING COUNT(*) > 1
    )
  ),
  matched AS (
    SELECT
      COUNT(DISTINCT {left_key}) as left_matched,
      COUNT(DISTINCT {right_key}) as right_matched,
      COUNT(*) as pairs
    FROM {left_table} l INNER JOIN {right_table} r ON {join_cond}
  ),
  left_only AS (
    SELECT COUNT(*) as cnt FROM {left_table} l
    LEFT JOIN {right_table} r ON {join_cond}
    WHERE r.{right_first_key} IS NULL
  ),
  right_only AS (
    SELECT COUNT(*) as cnt FROM {right_table} r
    LEFT JOIN {left_table} l ON {join_cond}
    WHERE l.{left_first_key} IS NULL
  )
SELECT
  left_stats.total as left_total,
  left_stats.distinct_keys as left_distinct,
  left_stats.null_keys as left_null_keys,
  left_dupes.cnt as left_duplicate_keys,
  right_stats.total as right_total,
  right_stats.distinct_keys as right_distinct,
  right_stats.null_keys as right_null_keys,
  right_dupes.cnt as right_duplicate_keys,
  matched.left_matched,
  matched.right_matched,
  matched.pairs,
  left_only.cnt as left_only,
  right_only.cnt as right_only
FROM left_stats, right_stats, left_dupes, right_dupes, matched, left_only, right_only",
        left_key = left_key_expr,
        right_key = right_key_expr,
        left_null = left_null_check,
        right_null = right_null_check,
        left_table = left_quoted,
        right_table = right_quoted,
        join_cond = join_cond,
        left_first_key = quote_identifier(&left_keys[0]),
        right_first_key = quote_identifier(&right_keys[0])
    )
}

/// Build null check expression for join keys.
fn build_null_check(alias: &str, keys: &[String]) -> String {
    keys.iter()
        .map(|k| format!("{}.{} IS NULL", alias, quote_identifier(k)))
        .collect::<Vec<_>>()
        .join(" OR ")
}

/// Build key expression for distinct counting with composite keys.
fn build_key_expr(alias: &str, keys: &[String]) -> String {
    if keys.len() == 1 {
        format!("{}.{}", alias, quote_identifier(&keys[0]))
    } else {
        format!(
            "CONCAT_WS('|', {})",
            keys.iter()
                .map(|k| format!("COALESCE(CAST({}.{} AS STRING), '')", alias, quote_identifier(k)))
                .collect::<Vec<_>>()
                .join(", ")
        )
    }
}

/// Generate SQL to get unmatched rows from one side of a join.
pub fn join_unmatched_sql(
    left_table: &str,
    right_table: &str,
    left_keys: &[String],
    right_keys: &[String],
    side: &str,
    offset: usize,
    limit: usize,
) -> String {
    let left_quoted = quote_identifier(left_table);
    let right_quoted = quote_identifier(right_table);
    let join_cond = build_join_condition("l", "r", left_keys, right_keys);

    if side == "left" {
        format!(
            "SELECT l.* FROM {} l \
             WHERE NOT EXISTS (SELECT 1 FROM {} r WHERE {}) \
             LIMIT {} OFFSET {}",
            left_quoted, right_quoted, join_cond, limit, offset
        )
    } else {
        format!(
            "SELECT r.* FROM {} r \
             WHERE NOT EXISTS (SELECT 1 FROM {} l WHERE {}) \
             LIMIT {} OFFSET {}",
            right_quoted, left_quoted, join_cond, limit, offset
        )
    }
}

/// Generate SQL to get unmatched rows with limited columns.
/// Returns only the specified columns plus join keys to reduce JSON payload size.
pub fn join_unmatched_sql_limited(
    left_table: &str,
    right_table: &str,
    left_keys: &[String],
    right_keys: &[String],
    side: &str,
    columns: &[String],
    offset: usize,
    limit: usize,
) -> String {
    let left_quoted = quote_identifier(left_table);
    let right_quoted = quote_identifier(right_table);
    let join_cond = build_join_condition("l", "r", left_keys, right_keys);

    let alias = if side == "left" { "l" } else { "r" };
    let select_cols = if columns.is_empty() {
        format!("{}.*", alias)
    } else {
        columns
            .iter()
            .map(|c| format!("{}.{}", alias, quote_identifier(c)))
            .collect::<Vec<_>>()
            .join(", ")
    };

    if side == "left" {
        format!(
            "SELECT {} FROM {} l \
             WHERE NOT EXISTS (SELECT 1 FROM {} r WHERE {}) \
             LIMIT {} OFFSET {}",
            select_cols, left_quoted, right_quoted, join_cond, limit, offset
        )
    } else {
        format!(
            "SELECT {} FROM {} r \
             WHERE NOT EXISTS (SELECT 1 FROM {} l WHERE {}) \
             LIMIT {} OFFSET {}",
            select_cols, right_quoted, left_quoted, join_cond, limit, offset
        )
    }
}

/// Generate SQL for aggregated reconciliation.
pub fn reconcile_agg_sql(
    source_table: &str,
    target_table: &str,
    config: &Value,
) -> Result<String, String> {
    let source_group_by = config["source_group_by"]
        .as_array()
        .ok_or("Missing source_group_by")?
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect::<Vec<_>>();

    let target_group_by = config["target_group_by"]
        .as_array()
        .ok_or("Missing target_group_by")?
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect::<Vec<_>>();

    let source_join_keys = config["source_join_keys"]
        .as_array()
        .ok_or("Missing source_join_keys")?
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect::<Vec<_>>();

    let target_join_keys = config["target_join_keys"]
        .as_array()
        .ok_or("Missing target_join_keys")?
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect::<Vec<_>>();

    let aggregations = config["aggregations"]
        .as_array()
        .ok_or("Missing aggregations")?;

    let join_type = config["join_type"]
        .as_str()
        .unwrap_or("inner")
        .to_uppercase();

    let sample_limit = config["sample_limit"].as_u64().unwrap_or(100) as usize;

    // Build aggregation expressions
    let agg_exprs = build_agg_expressions(aggregations)?;

    let source_quoted = quote_identifier(source_table);
    let target_quoted = quote_identifier(target_table);
    let source_group = quote_identifiers(&source_group_by);
    let target_group = quote_identifiers(&target_group_by);

    // Build join condition for aggregated results
    let join_cond = build_join_condition("s", "t", &source_join_keys, &target_join_keys);

    format!(
        "WITH
  source_agg AS (
    SELECT {}, {} FROM {} GROUP BY {}
  ),
  target_agg AS (
    SELECT {}, {} FROM {} GROUP BY {}
  ),
  reconciled AS (
    SELECT s.*, {} as __match_status
    FROM source_agg s
    {} JOIN target_agg t ON {}
  )
SELECT * FROM reconciled LIMIT {}",
        source_group, agg_exprs.source, source_quoted, source_group,
        target_group, agg_exprs.target, target_quoted, target_group,
        build_match_status_expr(&agg_exprs),
        join_type, join_cond,
        sample_limit
    );

    // Actually build a simpler reconciliation query
    Ok(build_reconcile_query(
        source_table,
        target_table,
        &source_group_by,
        &target_group_by,
        &source_join_keys,
        &target_join_keys,
        aggregations,
        &join_type,
        sample_limit,
    )?)
}

struct AggExpressions {
    source: String,
    target: String,
    comparisons: Vec<String>,
}

fn build_agg_expressions(aggregations: &[Value]) -> Result<AggExpressions, String> {
    let mut source_parts = Vec::new();
    let mut target_parts = Vec::new();
    let mut comparisons = Vec::new();

    for agg in aggregations {
        let column = agg["column"]
            .as_str()
            .ok_or("Missing column in aggregation")?;
        let agg_types = agg["aggregations"]
            .as_array()
            .ok_or("Missing aggregations array")?;

        for agg_type in agg_types {
            let agg_name = agg_type.as_str().unwrap_or("sum");
            let func = agg_name.to_uppercase();
            let alias = format!("{}_{}", column, agg_name);

            source_parts.push(format!(
                "{}({}) AS {}",
                func, quote_identifier(column), quote_identifier(&alias)
            ));
            target_parts.push(format!(
                "{}({}) AS {}",
                func, quote_identifier(column), quote_identifier(&alias)
            ));
            comparisons.push(alias);
        }
    }

    Ok(AggExpressions {
        source: source_parts.join(", "),
        target: target_parts.join(", "),
        comparisons,
    })
}

fn build_match_status_expr(agg_exprs: &AggExpressions) -> String {
    if agg_exprs.comparisons.is_empty() {
        return "'matched'".to_string();
    }

    let conditions: Vec<String> = agg_exprs.comparisons.iter()
        .map(|c| format!("s.{} = t.{}", quote_identifier(c), quote_identifier(c)))
        .collect();

    format!("CASE WHEN {} THEN 'matched' ELSE 'mismatched' END", conditions.join(" AND "))
}

fn build_reconcile_query(
    source_table: &str,
    target_table: &str,
    source_group_by: &[String],
    target_group_by: &[String],
    source_join_keys: &[String],
    target_join_keys: &[String],
    aggregations: &[Value],
    join_type: &str,
    sample_limit: usize,
) -> Result<String, String> {
    let source_quoted = quote_identifier(source_table);
    let target_quoted = quote_identifier(target_table);
    let source_group = quote_identifiers(source_group_by);
    let target_group = quote_identifiers(target_group_by);

    let agg_exprs = build_agg_expressions(aggregations)?;
    let join_cond = build_join_condition("s", "t", source_join_keys, target_join_keys);

    Ok(format!(
        "WITH
  source_agg AS (
    SELECT {}, {} FROM {} GROUP BY {}
  ),
  target_agg AS (
    SELECT {}, {} FROM {} GROUP BY {}
  ),
  joined AS (
    SELECT
      s.*,
      {}
    FROM source_agg s
    {} JOIN target_agg t ON {}
  )
SELECT * FROM joined LIMIT {}",
        source_group, agg_exprs.source, source_quoted, source_group,
        target_group, agg_exprs.target, target_quoted, target_group,
        build_target_columns(&agg_exprs.comparisons),
        join_type, join_cond,
        sample_limit
    ))
}

fn build_target_columns(comparisons: &[String]) -> String {
    comparisons.iter()
        .map(|c| format!("t.{} AS target_{}", quote_identifier(c), c))
        .collect::<Vec<_>>()
        .join(", ")
}

/// Build value comparison expression for determining if aggregated values match.
/// Uses tolerance-based comparison for floating point values.
fn build_value_match_condition(alias_s: &str, alias_t: &str, comparisons: &[String]) -> String {
    if comparisons.is_empty() {
        return "TRUE".to_string();
    }

    comparisons.iter()
        .map(|c| {
            let s_col = format!("{}.{}", alias_s, quote_identifier(c));
            let t_col = format!("{}.{}", alias_t, quote_identifier(c));
            // Use tolerance-based comparison: values match if both NULL or difference <= 0.01
            format!(
                "(({s} IS NULL AND {t} IS NULL) OR (ABS(COALESCE({s}, 0) - COALESCE({t}, 0)) <= 0.01))",
                s = s_col,
                t = t_col
            )
        })
        .collect::<Vec<_>>()
        .join(" AND ")
}

/// Generate SQL for reconciliation statistics counts.
/// Uses JOINs instead of EXISTS/NOT EXISTS to avoid SPARK-47070 bug
/// with correlated subqueries on same-named columns from CTEs.
/// Returns both key match counts and value match counts.
pub fn reconcile_stats_sql(
    source_table: &str,
    target_table: &str,
    config: &Value,
) -> Result<String, String> {
    let (source_group_by, target_group_by, source_join_keys, target_join_keys, agg_exprs) =
        parse_reconcile_config(config)?;

    let source_quoted = quote_identifier(source_table);
    let target_quoted = quote_identifier(target_table);
    let source_group = quote_identifiers(&source_group_by);
    let target_group = quote_identifiers(&target_group_by);
    let join_cond = build_join_condition("s", "t", &source_join_keys, &target_join_keys);
    let value_match_cond = build_value_match_condition("s", "t", &agg_exprs.comparisons);

    // Use first target key for NULL check in source_only (after LEFT JOIN)
    let target_null_check = quote_identifier(&target_join_keys[0]);
    // Use first source key for NULL check in target_only (after LEFT JOIN)
    let source_null_check = quote_identifier(&source_join_keys[0]);

    Ok(format!(
        "WITH
  source_agg AS (SELECT {}, {} FROM {} GROUP BY {}),
  target_agg AS (SELECT {}, {} FROM {} GROUP BY {}),
  source_count AS (SELECT COUNT(*) as cnt FROM source_agg),
  target_count AS (SELECT COUNT(*) as cnt FROM target_agg),
  key_matched AS (
    SELECT COUNT(*) as cnt
    FROM source_agg s
    INNER JOIN target_agg t ON {}
  ),
  value_matched AS (
    SELECT COUNT(*) as cnt
    FROM source_agg s
    INNER JOIN target_agg t ON {}
    WHERE {}
  ),
  value_mismatched AS (
    SELECT COUNT(*) as cnt
    FROM source_agg s
    INNER JOIN target_agg t ON {}
    WHERE NOT ({})
  ),
  source_only AS (
    SELECT COUNT(*) as cnt
    FROM source_agg s
    LEFT JOIN target_agg t ON {}
    WHERE t.{} IS NULL
  ),
  target_only AS (
    SELECT COUNT(*) as cnt
    FROM target_agg t
    LEFT JOIN source_agg s ON {}
    WHERE s.{} IS NULL
  )
SELECT
  source_count.cnt as source_groups,
  target_count.cnt as target_groups,
  key_matched.cnt as key_matched_groups,
  value_matched.cnt as value_matched_groups,
  value_mismatched.cnt as value_mismatched_groups,
  source_only.cnt as source_only_groups,
  target_only.cnt as target_only_groups
FROM source_count, target_count, key_matched, value_matched, value_mismatched, source_only, target_only",
        source_group, agg_exprs.source, source_quoted, source_group,
        target_group, agg_exprs.target, target_quoted, target_group,
        join_cond,
        join_cond, value_match_cond,
        join_cond, value_match_cond,
        join_cond, target_null_check,
        join_cond, source_null_check
    ))
}

/// Generate SQL for source-only rows (unmatched in target).
/// Uses LEFT JOIN instead of NOT EXISTS to avoid SPARK-47070 bug.
pub fn reconcile_source_only_sql(
    source_table: &str,
    target_table: &str,
    config: &Value,
    limit: usize,
) -> Result<String, String> {
    let (source_group_by, target_group_by, source_join_keys, target_join_keys, agg_exprs) =
        parse_reconcile_config(config)?;

    let source_quoted = quote_identifier(source_table);
    let target_quoted = quote_identifier(target_table);
    let source_group = quote_identifiers(&source_group_by);
    let target_group = quote_identifiers(&target_group_by);
    let join_cond = build_join_condition("s", "t", &source_join_keys, &target_join_keys);
    let target_null_check = quote_identifier(&target_join_keys[0]);

    Ok(format!(
        "WITH
  source_agg AS (SELECT {}, {} FROM {} GROUP BY {}),
  target_agg AS (SELECT {}, {} FROM {} GROUP BY {})
SELECT s.* FROM source_agg s
LEFT JOIN target_agg t ON {}
WHERE t.{} IS NULL
LIMIT {}",
        source_group, agg_exprs.source, source_quoted, source_group,
        target_group, agg_exprs.target, target_quoted, target_group,
        join_cond, target_null_check, limit
    ))
}

/// Generate SQL for target-only rows (unmatched in source).
/// Uses LEFT JOIN instead of NOT EXISTS to avoid SPARK-47070 bug.
pub fn reconcile_target_only_sql(
    source_table: &str,
    target_table: &str,
    config: &Value,
    limit: usize,
) -> Result<String, String> {
    let (source_group_by, target_group_by, source_join_keys, target_join_keys, agg_exprs) =
        parse_reconcile_config(config)?;

    let source_quoted = quote_identifier(source_table);
    let target_quoted = quote_identifier(target_table);
    let source_group = quote_identifiers(&source_group_by);
    let target_group = quote_identifiers(&target_group_by);
    let join_cond = build_join_condition("s", "t", &source_join_keys, &target_join_keys);
    let source_null_check = quote_identifier(&source_join_keys[0]);

    Ok(format!(
        "WITH
  source_agg AS (SELECT {}, {} FROM {} GROUP BY {}),
  target_agg AS (SELECT {}, {} FROM {} GROUP BY {})
SELECT t.* FROM target_agg t
LEFT JOIN source_agg s ON {}
WHERE s.{} IS NULL
LIMIT {}",
        source_group, agg_exprs.source, source_quoted, source_group,
        target_group, agg_exprs.target, target_quoted, target_group,
        join_cond, source_null_check, limit
    ))
}

/// Generate SQL for matched rows with comparison data.
pub fn reconcile_matched_sql(
    source_table: &str,
    target_table: &str,
    config: &Value,
    limit: usize,
) -> Result<String, String> {
    let (source_group_by, target_group_by, source_join_keys, target_join_keys, agg_exprs) =
        parse_reconcile_config(config)?;

    let source_quoted = quote_identifier(source_table);
    let target_quoted = quote_identifier(target_table);
    let source_group = quote_identifiers(&source_group_by);
    let target_group = quote_identifiers(&target_group_by);
    let join_cond = build_join_condition("s", "t", &source_join_keys, &target_join_keys);

    Ok(format!(
        "WITH
  source_agg AS (SELECT {}, {} FROM {} GROUP BY {}),
  target_agg AS (SELECT {}, {} FROM {} GROUP BY {})
SELECT s.*, {}
FROM source_agg s
INNER JOIN target_agg t ON {}
LIMIT {}",
        source_group, agg_exprs.source, source_quoted, source_group,
        target_group, agg_exprs.target, target_quoted, target_group,
        build_target_columns(&agg_exprs.comparisons),
        join_cond, limit
    ))
}

/// Generate SQL for mismatched rows (keys match but values differ).
/// Returns rows where keys match but aggregated values don't match within tolerance.
pub fn reconcile_mismatched_sql(
    source_table: &str,
    target_table: &str,
    config: &Value,
    limit: usize,
) -> Result<String, String> {
    let (source_group_by, target_group_by, source_join_keys, target_join_keys, agg_exprs) =
        parse_reconcile_config(config)?;

    let source_quoted = quote_identifier(source_table);
    let target_quoted = quote_identifier(target_table);
    let source_group = quote_identifiers(&source_group_by);
    let target_group = quote_identifiers(&target_group_by);
    let join_cond = build_join_condition("s", "t", &source_join_keys, &target_join_keys);
    let value_match_cond = build_value_match_condition("s", "t", &agg_exprs.comparisons);

    Ok(format!(
        "WITH
  source_agg AS (SELECT {}, {} FROM {} GROUP BY {}),
  target_agg AS (SELECT {}, {} FROM {} GROUP BY {})
SELECT s.*, {}
FROM source_agg s
INNER JOIN target_agg t ON {}
WHERE NOT ({})
LIMIT {}",
        source_group, agg_exprs.source, source_quoted, source_group,
        target_group, agg_exprs.target, target_quoted, target_group,
        build_target_columns(&agg_exprs.comparisons),
        join_cond, value_match_cond, limit
    ))
}

/// Generate SQL for column totals comparison.
pub fn reconcile_totals_sql(
    source_table: &str,
    target_table: &str,
    config: &Value,
) -> Result<String, String> {
    let aggregations = config["aggregations"]
        .as_array()
        .ok_or("Missing aggregations")?;

    let source_quoted = quote_identifier(source_table);
    let target_quoted = quote_identifier(target_table);

    let mut source_aggs = Vec::new();
    let mut target_aggs = Vec::new();

    for agg in aggregations {
        let column = agg["column"].as_str().ok_or("Missing column")?;
        let agg_types = agg["aggregations"].as_array().ok_or("Missing aggregations")?;

        for agg_type in agg_types {
            let func = agg_type.as_str().unwrap_or("sum").to_uppercase();
            let alias = format!("{}_{}", column, func.to_lowercase());
            source_aggs.push(format!(
                "{}({}) AS source_{}",
                func, quote_identifier(column), alias
            ));
            target_aggs.push(format!(
                "{}({}) AS target_{}",
                func, quote_identifier(column), alias
            ));
        }
    }

    Ok(format!(
        "SELECT s.*, t.* FROM (SELECT {} FROM {}) s, (SELECT {} FROM {}) t",
        source_aggs.join(", "), source_quoted,
        target_aggs.join(", "), target_quoted
    ))
}

fn parse_reconcile_config(config: &Value) -> Result<(Vec<String>, Vec<String>, Vec<String>, Vec<String>, AggExpressions), String> {
    let source_group_by = config["source_group_by"]
        .as_array()
        .ok_or("Missing source_group_by")?
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect::<Vec<_>>();

    let target_group_by = config["target_group_by"]
        .as_array()
        .ok_or("Missing target_group_by")?
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect::<Vec<_>>();

    let source_join_keys = config["source_join_keys"]
        .as_array()
        .ok_or("Missing source_join_keys")?
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect::<Vec<_>>();

    let target_join_keys = config["target_join_keys"]
        .as_array()
        .ok_or("Missing target_join_keys")?
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect::<Vec<_>>();

    let aggregations = config["aggregations"]
        .as_array()
        .ok_or("Missing aggregations")?;

    let agg_exprs = build_agg_expressions(aggregations)?;

    Ok((source_group_by, target_group_by, source_join_keys, target_join_keys, agg_exprs))
}

fn build_join_condition(
    left_alias: &str,
    right_alias: &str,
    left_keys: &[String],
    right_keys: &[String],
) -> String {
    left_keys
        .iter()
        .zip(right_keys.iter())
        .map(|(lk, rk)| {
            // Use NULL-safe equality (<=>). Standard = returns NULL when comparing NULLs,
            // causing rows with NULL keys to never match even in identical tables.
            format!(
                "{}.{} <=> {}.{}",
                left_alias, quote_identifier(lk),
                right_alias, quote_identifier(rk)
            )
        })
        .collect::<Vec<_>>()
        .join(" AND ")
}

fn is_numeric_type(type_str: &str) -> bool {
    let t = type_str.to_lowercase();
    t.contains("int") || t.contains("float") || t.contains("double")
        || t.contains("decimal") || t.contains("numeric")
}

/// Generate SQL for join key statistics.
pub fn join_key_stats_sql(table: &str, columns: &[String]) -> String {
    let quoted_table = quote_identifier(table);
    let key_expr = if columns.len() == 1 {
        quote_identifier(&columns[0])
    } else {
        format!(
            "CONCAT_WS('|', {})",
            columns
                .iter()
                .map(|c| format!("COALESCE(CAST({} AS STRING), '')", quote_identifier(c)))
                .collect::<Vec<_>>()
                .join(", ")
        )
    };

    format!(
        "SELECT
            COUNT(*) as total_rows,
            COUNT(DISTINCT {}) as cardinality,
            COUNT(*) - COUNT({}) as null_count
         FROM {}",
        key_expr, key_expr, quoted_table
    )
}

/// Generate SQL for temporal bucket analysis.
pub fn temporal_buckets_sql(table: &str, date_column: &str, bucket: &str) -> String {
    let quoted_table = quote_identifier(table);
    let quoted_col = quote_identifier(date_column);

    let trunc_expr = match bucket {
        "day" => format!("DATE_TRUNC('DAY', {})", quoted_col),
        "week" => format!("DATE_TRUNC('WEEK', {})", quoted_col),
        "month" => format!("DATE_TRUNC('MONTH', {})", quoted_col),
        "year" => format!("DATE_TRUNC('YEAR', {})", quoted_col),
        _ => format!("DATE_TRUNC('MONTH', {})", quoted_col),
    };

    format!(
        "SELECT
            {} as bucket,
            MIN({}) as min_date,
            MAX({}) as max_date,
            COUNT(*) as row_count
         FROM {}
         WHERE {} IS NOT NULL
         GROUP BY 1
         ORDER BY 1",
        trunc_expr, quoted_col, quoted_col, quoted_table, quoted_col
    )
}

/// Generate SQL for temporal range stats.
pub fn temporal_range_sql(table: &str, date_column: &str) -> String {
    let quoted_table = quote_identifier(table);
    let quoted_col = quote_identifier(date_column);

    format!(
        "SELECT
            MIN({}) as min_date,
            MAX({}) as max_date,
            COUNT(*) as total_rows,
            COUNT(*) - COUNT({}) as null_dates,
            COUNT(DISTINCT {}) as distinct_dates
         FROM {}",
        quoted_col, quoted_col, quoted_col, quoted_col, quoted_table
    )
}

/// Generate SQL for computing join overlap between two tables.
/// Uses indexed aliases (key_0, key_1, etc.) to avoid column name collisions.
/// Uses JOINs instead of EXISTS/NOT EXISTS to avoid SPARK-47070 bug
/// with correlated subqueries on same-named columns from CTEs.
pub fn join_overlap_sql(
    left_table: &str,
    right_table: &str,
    left_keys: &[String],
    right_keys: &[String],
) -> String {
    let left_quoted = quote_identifier(left_table);
    let right_quoted = quote_identifier(right_table);

    let left_cols = left_keys
        .iter()
        .enumerate()
        .map(|(i, k)| format!("{} AS key_{}", quote_identifier(k), i))
        .collect::<Vec<_>>()
        .join(", ");
    let right_cols = right_keys
        .iter()
        .enumerate()
        .map(|(i, k)| format!("{} AS key_{}", quote_identifier(k), i))
        .collect::<Vec<_>>()
        .join(", ");
    let join_cond = build_overlap_condition("lk", "rk", left_keys.len());

    format!(
        "WITH
  left_keys AS (SELECT DISTINCT {} FROM {} l),
  right_keys AS (SELECT DISTINCT {} FROM {} r),
  left_count AS (SELECT COUNT(*) as cnt FROM left_keys),
  right_count AS (SELECT COUNT(*) as cnt FROM right_keys),
  left_only AS (
    SELECT COUNT(*) as cnt
    FROM left_keys lk
    LEFT JOIN right_keys rk ON {}
    WHERE rk.key_0 IS NULL
  ),
  right_only AS (
    SELECT COUNT(*) as cnt
    FROM right_keys rk
    LEFT JOIN left_keys lk ON {}
    WHERE lk.key_0 IS NULL
  ),
  both_matched AS (
    SELECT COUNT(*) as cnt
    FROM left_keys lk
    INNER JOIN right_keys rk ON {}
  )
SELECT
  left_count.cnt as left_total,
  right_count.cnt as right_total,
  left_only.cnt as left_only,
  right_only.cnt as right_only,
  both_matched.cnt as both_count,
  CASE WHEN left_count.cnt + right_count.cnt - both_matched.cnt > 0
    THEN both_matched.cnt * 100.0 / (left_count.cnt + right_count.cnt - both_matched.cnt)
    ELSE 0
  END as overlap_pct
FROM left_count, right_count, left_only, right_only, both_matched",
        left_cols, left_quoted, right_cols, right_quoted,
        join_cond, join_cond, join_cond
    )
}

fn build_overlap_condition(left_alias: &str, right_alias: &str, key_count: usize) -> String {
    (0..key_count)
        .map(|i| format!("{}.key_{} <=> {}.key_{}", left_alias, i, right_alias, i))
        .collect::<Vec<_>>()
        .join(" AND ")
}

/// Generate SQL for temporal data loss calculation.
pub fn temporal_loss_sql(
    table: &str,
    date_column: &str,
    overlap_start: &str,
    overlap_end: &str,
) -> String {
    let quoted_table = quote_identifier(table);
    let quoted_col = quote_identifier(date_column);

    format!(
        "SELECT
            SUM(CASE WHEN {} < '{}' THEN 1 ELSE 0 END) as rows_before,
            SUM(CASE WHEN {} > '{}' THEN 1 ELSE 0 END) as rows_after,
            SUM(CASE WHEN {} < '{}' OR {} > '{}' THEN 1 ELSE 0 END) as total_lost,
            COUNT(*) as total_rows,
            CASE WHEN COUNT(*) > 0 THEN
                SUM(CASE WHEN {} < '{}' OR {} > '{}' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
            ELSE 0 END as pct_lost
         FROM {}
         WHERE {} IS NOT NULL",
        quoted_col, overlap_start,
        quoted_col, overlap_end,
        quoted_col, overlap_start, quoted_col, overlap_end,
        quoted_col, overlap_start, quoted_col, overlap_end,
        quoted_table, quoted_col
    )
}

// ============ Alert SQL Generation Functions ============

/// Generate SQL to check if a column value exceeds a threshold.
/// Returns count of rows meeting the condition and statistics.
pub fn alert_threshold_sql(
    table: &str,
    column: &str,
    operator: &str,
    threshold: f64,
) -> Result<String, String> {
    let quoted_table = quote_identifier(table);
    let quoted_col = quote_identifier(column);

    // Validate operator
    let op = match operator {
        ">" | "<" | ">=" | "<=" | "=" | "==" | "!=" => {
            if operator == "==" { "=" } else { operator }
        }
        _ => return Err(format!("Invalid operator: {}", operator)),
    };

    Ok(format!(
        "SELECT
            COUNT(*) as total_rows,
            SUM(CASE WHEN {} {} {} THEN 1 ELSE 0 END) as violations,
            CASE WHEN COUNT(*) > 0 THEN
                SUM(CASE WHEN {} {} {} THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
            ELSE 0 END as violation_pct,
            MAX({}) as max_value,
            MIN({}) as min_value,
            AVG({}) as avg_value
         FROM {}",
        quoted_col, op, threshold,
        quoted_col, op, threshold,
        quoted_col, quoted_col, quoted_col,
        quoted_table
    ))
}

/// Generate SQL to check null rate in a column.
pub fn alert_null_rate_sql(
    table: &str,
    column: &str,
) -> String {
    let quoted_table = quote_identifier(table);
    let quoted_col = quote_identifier(column);

    format!(
        "SELECT
            COUNT(*) as total_rows,
            COUNT({}) as non_null,
            COUNT(*) - COUNT({}) as null_count,
            CASE WHEN COUNT(*) > 0
                THEN ((COUNT(*) - COUNT({})) * 100.0 / COUNT(*))
                ELSE 0
            END as null_pct
         FROM {}",
        quoted_col, quoted_col, quoted_col, quoted_table
    )
}

/// Generate SQL to check row count against thresholds.
pub fn alert_row_count_sql(
    table: &str,
    min_rows: Option<usize>,
    max_rows: Option<usize>,
) -> Result<String, String> {
    if min_rows.is_none() && max_rows.is_none() {
        return Err("At least one of min_rows or max_rows must be specified".to_string());
    }

    let quoted_table = quote_identifier(table);
    let conditions = match (min_rows, max_rows) {
        (Some(min), Some(max)) => format!(
            "CASE
                WHEN COUNT(*) < {} THEN 'below_minimum'
                WHEN COUNT(*) > {} THEN 'above_maximum'
                ELSE 'within_range'
            END as status,
            {} as min_threshold,
            {} as max_threshold",
            min, max, min, max
        ),
        (Some(min), None) => format!(
            "CASE
                WHEN COUNT(*) < {} THEN 'below_minimum'
                ELSE 'above_minimum'
            END as status,
            {} as min_threshold,
            NULL as max_threshold",
            min, min
        ),
        (None, Some(max)) => format!(
            "CASE
                WHEN COUNT(*) > {} THEN 'above_maximum'
                ELSE 'below_maximum'
            END as status,
            NULL as min_threshold,
            {} as max_threshold",
            max, max
        ),
        _ => unreachable!(),
    };

    Ok(format!(
        "SELECT
            COUNT(*) as row_count,
            {},
            CURRENT_TIMESTAMP() as evaluated_at
         FROM {}",
        conditions, quoted_table
    ))
}

/// Generate SQL to check data freshness based on a date column.
pub fn alert_data_freshness_sql(
    table: &str,
    date_column: &str,
    max_age_hours: u32,
) -> String {
    let quoted_table = quote_identifier(table);
    let quoted_col = quote_identifier(date_column);

    format!(
        "SELECT
            MAX({}) as latest_date,
            CURRENT_TIMESTAMP() as current_time,
            TIMESTAMPDIFF(HOUR, MAX({}), CURRENT_TIMESTAMP()) as hours_since_update,
            {} as max_age_hours,
            CASE
                WHEN TIMESTAMPDIFF(HOUR, MAX({}), CURRENT_TIMESTAMP()) > {} THEN 'stale'
                ELSE 'fresh'
            END as freshness_status,
            COUNT(*) as total_rows
         FROM {}
         WHERE {} IS NOT NULL",
        quoted_col, quoted_col,
        max_age_hours,
        quoted_col, max_age_hours,
        quoted_table, quoted_col
    )
}

/// Generate SQL to check for duplicate keys.
pub fn alert_duplicate_keys_sql(
    table: &str,
    keys: &[String],
    max_duplicates: Option<usize>,
) -> Result<String, String> {
    if keys.is_empty() {
        return Err("At least one key column must be specified".to_string());
    }

    let quoted_table = quote_identifier(table);
    let key_expr = if keys.len() == 1 {
        quote_identifier(&keys[0])
    } else {
        format!(
            "CONCAT_WS('|', {})",
            keys.iter()
                .map(|k| format!("COALESCE(CAST({} AS STRING), '')", quote_identifier(k)))
                .collect::<Vec<_>>()
                .join(", ")
        )
    };

    let threshold_check = if let Some(max) = max_duplicates {
        format!(
            "SUM(CASE WHEN dupe_count > {} THEN 1 ELSE 0 END) as keys_above_threshold,
            {} as max_allowed_duplicates,",
            max, max
        )
    } else {
        String::new()
    };

    Ok(format!(
        "WITH key_counts AS (
            SELECT
                {} as key_value,
                COUNT(*) as dupe_count
            FROM {}
            GROUP BY {}
            HAVING COUNT(*) > 1
        )
        SELECT
            COUNT(*) as duplicate_key_count,
            SUM(dupe_count) as total_duplicate_rows,
            MAX(dupe_count) as max_duplicates,
            {}
            (SELECT COUNT(*) FROM {}) as total_rows
        FROM key_counts",
        key_expr, quoted_table, key_expr,
        threshold_check,
        quoted_table
    ))
}

/// Generate SQL for reconciliation-based alerts.
/// Checks if match rate between tables meets minimum threshold.
pub fn alert_reconciliation_sql(
    source_table: &str,
    target_table: &str,
    join_keys: &[String],
    min_match_rate: f64,
) -> Result<String, String> {
    if join_keys.is_empty() {
        return Err("At least one join key must be specified".to_string());
    }

    if min_match_rate < 0.0 || min_match_rate > 100.0 {
        return Err("min_match_rate must be between 0 and 100".to_string());
    }

    let source_quoted = quote_identifier(source_table);
    let target_quoted = quote_identifier(target_table);
    let join_cond = build_join_condition("s", "t", join_keys, join_keys);

    Ok(format!(
        "WITH
          source_count AS (SELECT COUNT(*) as cnt FROM {} s),
          target_count AS (SELECT COUNT(*) as cnt FROM {} t),
          matched AS (
            SELECT COUNT(*) as cnt
            FROM {} s
            INNER JOIN {} t ON {}
          )
        SELECT
            source_count.cnt as source_rows,
            target_count.cnt as target_rows,
            matched.cnt as matched_rows,
            CASE
                WHEN source_count.cnt + target_count.cnt - matched.cnt > 0 THEN
                    matched.cnt * 100.0 / (source_count.cnt + target_count.cnt - matched.cnt)
                ELSE 100.0
            END as match_rate_pct,
            {} as min_match_rate_pct,
            CASE
                WHEN source_count.cnt + target_count.cnt - matched.cnt > 0 AND
                     matched.cnt * 100.0 / (source_count.cnt + target_count.cnt - matched.cnt) < {}
                THEN 'below_threshold'
                ELSE 'acceptable'
            END as alert_status
        FROM source_count, target_count, matched",
        source_quoted, target_quoted,
        source_quoted, target_quoted, join_cond,
        min_match_rate, min_match_rate
    ))
}

/// Generate a Databricks-compatible alert query wrapper.
/// Wraps the provided SQL to return a single value for alert evaluation.
pub fn generate_databricks_alert_query(
    inner_sql: &str,
    value_column: &str,
    alert_name: &str,
) -> String {
    format!(
        "-- MangleFrames Generated Alert Query
-- Name: {}
-- Evaluates: {}
WITH alert_data AS (
{}
)
SELECT {} as alert_value FROM alert_data",
        alert_name, value_column, inner_sql, quote_identifier(value_column)
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    // ============ quote_identifier tests ============

    #[test]
    fn test_quote_identifier_simple() {
        assert_eq!(quote_identifier("column"), "`column`");
    }

    #[test]
    fn test_quote_identifier_with_backtick() {
        assert_eq!(quote_identifier("my`col"), "`my``col`");
    }

    #[test]
    fn test_quote_identifier_unicode() {
        assert_eq!(quote_identifier("列名"), "`列名`");
        assert_eq!(quote_identifier("tëst_cöl"), "`tëst_cöl`");
    }

    #[test]
    fn test_quote_identifier_spaces() {
        assert_eq!(quote_identifier("my column"), "`my column`");
        assert_eq!(quote_identifier("  spaces  "), "`  spaces  `");
    }

    #[test]
    fn test_quote_identifier_special_chars() {
        assert_eq!(quote_identifier("col-name"), "`col-name`");
        assert_eq!(quote_identifier("col.name"), "`col.name`");
    }

    // ============ quote_identifiers tests ============

    #[test]
    fn test_quote_identifiers_empty() {
        let result = quote_identifiers(&[]);
        assert_eq!(result, "");
    }

    #[test]
    fn test_quote_identifiers_single() {
        let result = quote_identifiers(&["col1".to_string()]);
        assert_eq!(result, "`col1`");
    }

    #[test]
    fn test_quote_identifiers_multiple() {
        let result = quote_identifiers(&["col1".to_string(), "col2".to_string(), "col3".to_string()]);
        assert_eq!(result, "`col1`, `col2`, `col3`");
    }

    // ============ list_tables_sql tests ============

    #[test]
    fn test_list_tables_sql() {
        assert_eq!(list_tables_sql(), "SHOW TABLES");
    }

    // ============ describe_table_sql tests ============

    #[test]
    fn test_describe_table_sql_simple() {
        let sql = describe_table_sql("my_table");
        assert_eq!(sql, "DESCRIBE TABLE `my_table`");
    }

    #[test]
    fn test_describe_table_sql_special_chars() {
        let sql = describe_table_sql("my`special`table");
        assert_eq!(sql, "DESCRIBE TABLE `my``special``table`");
    }

    #[test]
    fn test_describe_table_sql_qualified_name() {
        let sql = describe_table_sql("catalog.schema.table");
        assert_eq!(sql, "DESCRIBE TABLE `catalog.schema.table`");
    }

    // ============ select_data_sql tests ============

    #[test]
    fn test_select_data_sql_no_offset() {
        let sql = select_data_sql("my_table", 100, 0);
        assert_eq!(sql, "SELECT * FROM `my_table` LIMIT 100");
    }

    #[test]
    fn test_select_data_sql_with_offset() {
        let sql = select_data_sql("my_table", 100, 50);
        assert!(sql.contains("ROW_NUMBER()"));
        assert!(sql.contains("> 50"));
        assert!(sql.contains("<= 150"));
    }

    #[test]
    fn test_select_data_sql_limit_zero() {
        let sql = select_data_sql("my_table", 0, 0);
        assert_eq!(sql, "SELECT * FROM `my_table` LIMIT 0");
    }

    #[test]
    fn test_select_data_sql_large_offset() {
        let sql = select_data_sql("my_table", 10, 1_000_000);
        assert!(sql.contains("> 1000000"));
        assert!(sql.contains("<= 1000010"));
    }

    // ============ count_rows_sql tests ============

    #[test]
    fn test_count_rows_sql() {
        let sql = count_rows_sql("test_table");
        assert_eq!(sql, "SELECT COUNT(*) as total FROM `test_table`");
    }

    // ============ stats_sql tests ============

    #[test]
    fn test_stats_sql_numeric_column() {
        let sql = stats_sql("table", &[("amount".to_string(), "int".to_string())]);
        assert!(sql.contains("COUNT(*) AS row_count"));
        assert!(sql.contains("COUNT(`amount`) AS `amount_non_null`"));
        assert!(sql.contains("MIN(`amount`)"));
        assert!(sql.contains("MAX(`amount`)"));
    }

    #[test]
    fn test_stats_sql_string_column() {
        let sql = stats_sql("table", &[("name".to_string(), "string".to_string())]);
        assert!(sql.contains("COUNT(`name`) AS `name_non_null`"));
        assert!(!sql.contains("MIN(`name`)"));
        assert!(!sql.contains("MAX(`name`)"));
    }

    #[test]
    fn test_stats_sql_mixed_columns() {
        let sql = stats_sql("table", &[
            ("id".to_string(), "bigint".to_string()),
            ("name".to_string(), "string".to_string()),
            ("price".to_string(), "double".to_string()),
        ]);
        assert!(sql.contains("MIN(`id`)"));
        assert!(sql.contains("MAX(`price`)"));
        assert!(!sql.contains("MIN(`name`)"));
    }

    #[test]
    fn test_stats_sql_empty_columns() {
        let sql = stats_sql("table", &[]);
        assert_eq!(sql, "SELECT COUNT(*) AS row_count FROM `table`");
    }

    // ============ join_keys_sql tests ============

    #[test]
    fn test_join_keys_sql_single_key() {
        let sql = join_keys_sql("table", &["id".to_string()]);
        assert!(sql.contains("COUNT(*) AS total_rows"));
        assert!(sql.contains("COUNT(DISTINCT `id`)"));
        assert!(sql.contains("`id_nulls`"));
    }

    #[test]
    fn test_join_keys_sql_multiple_keys() {
        let sql = join_keys_sql("table", &["id".to_string(), "date".to_string()]);
        assert!(sql.contains("`id_distinct`"));
        assert!(sql.contains("`date_distinct`"));
        assert!(sql.contains("`id_nulls`"));
        assert!(sql.contains("`date_nulls`"));
    }

    // ============ build_join_condition tests ============

    #[test]
    fn test_join_condition_single_key() {
        let cond = build_join_condition(
            "l", "r",
            &["id".to_string()],
            &["key".to_string()]
        );
        assert_eq!(cond, "l.`id` <=> r.`key`");
    }

    #[test]
    fn test_join_condition_multiple_keys() {
        let cond = build_join_condition(
            "l", "r",
            &["id".to_string(), "date".to_string()],
            &["key".to_string(), "dt".to_string()]
        );
        assert_eq!(cond, "l.`id` <=> r.`key` AND l.`date` <=> r.`dt`");
    }

    #[test]
    fn test_join_condition_null_safe_equality() {
        let cond = build_join_condition(
            "a", "b",
            &["col".to_string()],
            &["col".to_string()]
        );
        assert!(cond.contains("<=>"), "Should use null-safe equality operator");
    }

    // ============ build_null_check tests ============

    #[test]
    fn test_build_null_check_single() {
        let check = build_null_check("t", &["id".to_string()]);
        assert_eq!(check, "t.`id` IS NULL");
    }

    #[test]
    fn test_build_null_check_multiple() {
        let check = build_null_check("t", &["id".to_string(), "date".to_string()]);
        assert_eq!(check, "t.`id` IS NULL OR t.`date` IS NULL");
    }

    // ============ build_key_expr tests ============

    #[test]
    fn test_build_key_expr_single() {
        let expr = build_key_expr("t", &["id".to_string()]);
        assert_eq!(expr, "t.`id`");
    }

    #[test]
    fn test_build_key_expr_composite() {
        let expr = build_key_expr("t", &["id".to_string(), "date".to_string()]);
        assert!(expr.contains("CONCAT_WS('|'"));
        assert!(expr.contains("COALESCE(CAST(t.`id` AS STRING), '')"));
        assert!(expr.contains("COALESCE(CAST(t.`date` AS STRING), '')"));
    }

    // ============ join_analyze_sql tests ============

    #[test]
    fn test_join_analyze_sql_contains_ctes() {
        let sql = join_analyze_sql(
            "left_table", "right_table",
            &["id".to_string()], &["key".to_string()]
        );
        assert!(sql.contains("left_stats AS"));
        assert!(sql.contains("right_stats AS"));
        assert!(sql.contains("matched AS"));
        assert!(sql.contains("left_only AS"));
        assert!(sql.contains("right_only AS"));
    }

    #[test]
    fn test_join_analyze_sql_composite_keys() {
        let sql = join_analyze_sql(
            "left_table", "right_table",
            &["id".to_string(), "date".to_string()],
            &["key".to_string(), "dt".to_string()]
        );
        assert!(sql.contains("CONCAT_WS"));
    }

    // ============ join_unmatched_sql tests ============

    #[test]
    fn test_join_unmatched_sql_left() {
        let sql = join_unmatched_sql(
            "left", "right",
            &["id".to_string()], &["key".to_string()],
            "left", 0, 100
        );
        assert!(sql.contains("SELECT l.*"));
        assert!(sql.contains("NOT EXISTS"));
        assert!(sql.contains("LIMIT 100"));
        assert!(sql.contains("OFFSET 0"));
    }

    #[test]
    fn test_join_unmatched_sql_right() {
        let sql = join_unmatched_sql(
            "left", "right",
            &["id".to_string()], &["key".to_string()],
            "right", 0, 100
        );
        assert!(sql.contains("SELECT r.*"));
        assert!(sql.contains("NOT EXISTS"));
    }

    #[test]
    fn test_join_unmatched_sql_pagination() {
        let sql = join_unmatched_sql(
            "left", "right",
            &["id".to_string()], &["key".to_string()],
            "left", 500, 50
        );
        assert!(sql.contains("LIMIT 50"));
        assert!(sql.contains("OFFSET 500"));
    }

    // ============ join_unmatched_sql_limited tests ============

    #[test]
    fn test_join_unmatched_sql_limited_left() {
        let sql = join_unmatched_sql_limited(
            "left_table", "right_table",
            &["id".to_string()], &["key".to_string()],
            "left",
            &["id".to_string(), "name".to_string(), "amount".to_string()],
            0, 100
        );
        assert!(sql.contains("SELECT l.`id`, l.`name`, l.`amount`"));
        assert!(sql.contains("NOT EXISTS"));
        assert!(sql.contains("LIMIT 100"));
        assert!(sql.contains("OFFSET 0"));
    }

    #[test]
    fn test_join_unmatched_sql_limited_right() {
        let sql = join_unmatched_sql_limited(
            "left_table", "right_table",
            &["id".to_string()], &["key".to_string()],
            "right",
            &["key".to_string(), "value".to_string()],
            0, 100
        );
        assert!(sql.contains("SELECT r.`key`, r.`value`"));
        assert!(sql.contains("NOT EXISTS"));
    }

    #[test]
    fn test_join_unmatched_sql_limited_empty_columns_falls_back_to_star() {
        let sql = join_unmatched_sql_limited(
            "left_table", "right_table",
            &["id".to_string()], &["key".to_string()],
            "left",
            &[],
            0, 100
        );
        assert!(sql.contains("SELECT l.*"));
    }

    #[test]
    fn test_join_unmatched_sql_limited_preserves_pagination() {
        let sql = join_unmatched_sql_limited(
            "left", "right",
            &["id".to_string()], &["key".to_string()],
            "left",
            &["col1".to_string()],
            500, 50
        );
        assert!(sql.contains("LIMIT 50"));
        assert!(sql.contains("OFFSET 500"));
    }

    #[test]
    fn test_join_unmatched_sql_limited_special_chars() {
        let sql = join_unmatched_sql_limited(
            "my`table", "other",
            &["id".to_string()], &["id".to_string()],
            "left",
            &["col`name".to_string()],
            0, 100
        );
        assert!(sql.contains("`col``name`"));
        assert!(sql.contains("`my``table`"));
    }

    // ============ reconcile_agg_sql tests ============

    #[test]
    fn test_reconcile_agg_sql_valid_config() {
        let config = json!({
            "source_group_by": ["customer_id"],
            "target_group_by": ["cust_id"],
            "source_join_keys": ["customer_id"],
            "target_join_keys": ["cust_id"],
            "aggregations": [{
                "column": "amount",
                "aggregations": ["sum", "count"]
            }],
            "join_type": "inner",
            "sample_limit": 100
        });
        let result = reconcile_agg_sql("source", "target", &config);
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("source_agg AS"));
        assert!(sql.contains("target_agg AS"));
        assert!(sql.contains("SUM(`amount`)"));
        assert!(sql.contains("COUNT(`amount`)"));
    }

    #[test]
    fn test_reconcile_agg_sql_missing_group_by() {
        let config = json!({
            "target_group_by": ["cust_id"],
            "source_join_keys": ["customer_id"],
            "target_join_keys": ["cust_id"],
            "aggregations": []
        });
        let result = reconcile_agg_sql("source", "target", &config);
        assert!(result.is_err());
    }

    // ============ reconcile_stats_sql tests ============

    #[test]
    fn test_reconcile_stats_sql_valid() {
        let config = json!({
            "source_group_by": ["id"],
            "target_group_by": ["id"],
            "source_join_keys": ["id"],
            "target_join_keys": ["id"],
            "aggregations": [{"column": "val", "aggregations": ["sum"]}]
        });
        let result = reconcile_stats_sql("src", "tgt", &config);
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("source_count AS"));
        assert!(sql.contains("target_count AS"));
        assert!(sql.contains("key_matched AS"));
        assert!(sql.contains("value_matched AS"));
        assert!(sql.contains("value_mismatched AS"));
        assert!(sql.contains("source_only AS"));
        assert!(sql.contains("target_only AS"));
    }

    #[test]
    fn test_reconcile_stats_sql_includes_value_match_counts() {
        let config = json!({
            "source_group_by": ["id"],
            "target_group_by": ["id"],
            "source_join_keys": ["id"],
            "target_join_keys": ["id"],
            "aggregations": [{"column": "amount", "aggregations": ["sum"]}]
        });
        let result = reconcile_stats_sql("src", "tgt", &config);
        assert!(result.is_ok());
        let sql = result.unwrap();
        // Verify value comparison fields are present
        assert!(sql.contains("key_matched_groups"));
        assert!(sql.contains("value_matched_groups"));
        assert!(sql.contains("value_mismatched_groups"));
        // Verify tolerance-based comparison is used
        assert!(sql.contains("ABS(COALESCE"));
        assert!(sql.contains("<= 0.01"));
    }

    #[test]
    fn test_reconcile_stats_sql_missing_aggregations() {
        let config = json!({
            "source_group_by": ["id"],
            "target_group_by": ["id"],
            "source_join_keys": ["id"],
            "target_join_keys": ["id"]
        });
        let result = reconcile_stats_sql("src", "tgt", &config);
        assert!(result.is_err());
    }

    // ============ reconcile_mismatched_sql tests ============

    #[test]
    fn test_reconcile_mismatched_sql_returns_differing_values() {
        let config = json!({
            "source_group_by": ["id"],
            "target_group_by": ["id"],
            "source_join_keys": ["id"],
            "target_join_keys": ["id"],
            "aggregations": [{"column": "amount", "aggregations": ["sum"]}]
        });
        let result = reconcile_mismatched_sql("src", "tgt", &config, 50);
        assert!(result.is_ok());
        let sql = result.unwrap();
        // Should use INNER JOIN to find rows where keys match
        assert!(sql.contains("INNER JOIN"));
        // Should filter for value mismatches using NOT
        assert!(sql.contains("WHERE NOT"));
        // Should have tolerance-based comparison
        assert!(sql.contains("ABS(COALESCE"));
        assert!(sql.contains("LIMIT 50"));
    }

    #[test]
    fn test_reconcile_mismatched_sql_multiple_agg_columns() {
        let config = json!({
            "source_group_by": ["id"],
            "target_group_by": ["id"],
            "source_join_keys": ["id"],
            "target_join_keys": ["id"],
            "aggregations": [
                {"column": "amount", "aggregations": ["sum", "count"]},
                {"column": "quantity", "aggregations": ["sum"]}
            ]
        });
        let result = reconcile_mismatched_sql("src", "tgt", &config, 100);
        assert!(result.is_ok());
        let sql = result.unwrap();
        // Should have conditions for all aggregation columns
        assert!(sql.contains("`amount_sum`"));
        assert!(sql.contains("`amount_count`"));
        assert!(sql.contains("`quantity_sum`"));
    }

    // ============ build_value_match_condition tests ============

    #[test]
    fn test_value_comparison_with_tolerance() {
        let cond = build_value_match_condition("s", "t", &["amount_sum".to_string()]);
        // Verify tolerance-based comparison
        assert!(cond.contains("ABS(COALESCE(s.`amount_sum`, 0) - COALESCE(t.`amount_sum`, 0)) <= 0.01"));
        // Verify NULL handling
        assert!(cond.contains("s.`amount_sum` IS NULL AND t.`amount_sum` IS NULL"));
    }

    #[test]
    fn test_value_comparison_empty_returns_true() {
        let cond = build_value_match_condition("s", "t", &[]);
        assert_eq!(cond, "TRUE");
    }

    #[test]
    fn test_value_comparison_multiple_columns() {
        let cond = build_value_match_condition("s", "t", &["a".to_string(), "b".to_string()]);
        assert!(cond.contains("s.`a`"));
        assert!(cond.contains("t.`a`"));
        assert!(cond.contains("s.`b`"));
        assert!(cond.contains("t.`b`"));
        assert!(cond.contains(" AND "));
    }

    // ============ reconcile_source_only_sql tests ============

    #[test]
    fn test_reconcile_source_only_sql() {
        let config = json!({
            "source_group_by": ["id"],
            "target_group_by": ["id"],
            "source_join_keys": ["id"],
            "target_join_keys": ["id"],
            "aggregations": [{"column": "val", "aggregations": ["sum"]}]
        });
        let result = reconcile_source_only_sql("src", "tgt", &config, 50);
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("SELECT s.*"));
        assert!(sql.contains("LEFT JOIN"));
        assert!(sql.contains("IS NULL"));
        assert!(sql.contains("LIMIT 50"));
    }

    // ============ reconcile_target_only_sql tests ============

    #[test]
    fn test_reconcile_target_only_sql() {
        let config = json!({
            "source_group_by": ["id"],
            "target_group_by": ["id"],
            "source_join_keys": ["id"],
            "target_join_keys": ["id"],
            "aggregations": [{"column": "val", "aggregations": ["sum"]}]
        });
        let result = reconcile_target_only_sql("src", "tgt", &config, 50);
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("SELECT t.*"));
        assert!(sql.contains("LEFT JOIN"));
        assert!(sql.contains("IS NULL"));
        assert!(sql.contains("LIMIT 50"));
    }

    // ============ reconcile_matched_sql tests ============

    #[test]
    fn test_reconcile_matched_sql() {
        let config = json!({
            "source_group_by": ["id"],
            "target_group_by": ["id"],
            "source_join_keys": ["id"],
            "target_join_keys": ["id"],
            "aggregations": [{"column": "val", "aggregations": ["sum"]}]
        });
        let result = reconcile_matched_sql("src", "tgt", &config, 50);
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("INNER JOIN"));
        assert!(sql.contains("LIMIT 50"));
    }

    // ============ reconcile_totals_sql tests ============

    #[test]
    fn test_reconcile_totals_sql() {
        let config = json!({
            "aggregations": [{
                "column": "amount",
                "aggregations": ["sum", "avg"]
            }]
        });
        let result = reconcile_totals_sql("src", "tgt", &config);
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("source_amount_sum"));
        assert!(sql.contains("target_amount_sum"));
        assert!(sql.contains("source_amount_avg"));
        assert!(sql.contains("target_amount_avg"));
    }

    #[test]
    fn test_reconcile_totals_sql_all_agg_types() {
        let config = json!({
            "aggregations": [{
                "column": "value",
                "aggregations": ["sum", "count", "min", "max", "avg"]
            }]
        });
        let result = reconcile_totals_sql("src", "tgt", &config);
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("SUM(`value`)"));
        assert!(sql.contains("COUNT(`value`)"));
        assert!(sql.contains("MIN(`value`)"));
        assert!(sql.contains("MAX(`value`)"));
        assert!(sql.contains("AVG(`value`)"));
    }

    #[test]
    fn test_reconcile_totals_sql_missing_aggregations() {
        let config = json!({});
        let result = reconcile_totals_sql("src", "tgt", &config);
        assert!(result.is_err());
    }

    // ============ join_key_stats_sql tests ============

    #[test]
    fn test_join_key_stats_sql_single() {
        let sql = join_key_stats_sql("table", &["id".to_string()]);
        assert!(sql.contains("COUNT(*)"));
        assert!(sql.contains("COUNT(DISTINCT `id`)"));
        assert!(sql.contains("null_count"));
    }

    #[test]
    fn test_join_key_stats_sql_multiple() {
        let sql = join_key_stats_sql("table", &["id".to_string(), "date".to_string()]);
        assert!(sql.contains("CONCAT_WS"));
        assert!(sql.contains("cardinality"));
    }

    // ============ temporal_buckets_sql tests ============

    #[test]
    fn test_temporal_buckets_sql_day() {
        let sql = temporal_buckets_sql("table", "created_at", "day");
        assert!(sql.contains("DATE_TRUNC('DAY'"));
        assert!(sql.contains("GROUP BY 1"));
    }

    #[test]
    fn test_temporal_buckets_sql_week() {
        let sql = temporal_buckets_sql("table", "created_at", "week");
        assert!(sql.contains("DATE_TRUNC('WEEK'"));
    }

    #[test]
    fn test_temporal_buckets_sql_month() {
        let sql = temporal_buckets_sql("table", "created_at", "month");
        assert!(sql.contains("DATE_TRUNC('MONTH'"));
    }

    #[test]
    fn test_temporal_buckets_sql_year() {
        let sql = temporal_buckets_sql("table", "created_at", "year");
        assert!(sql.contains("DATE_TRUNC('YEAR'"));
    }

    #[test]
    fn test_temporal_buckets_sql_default() {
        let sql = temporal_buckets_sql("table", "created_at", "unknown");
        assert!(sql.contains("DATE_TRUNC('MONTH'"));
    }

    // ============ temporal_range_sql tests ============

    #[test]
    fn test_temporal_range_sql() {
        let sql = temporal_range_sql("table", "date_col");
        assert!(sql.contains("MIN(`date_col`)"));
        assert!(sql.contains("MAX(`date_col`)"));
        assert!(sql.contains("total_rows"));
        assert!(sql.contains("null_dates"));
        assert!(sql.contains("distinct_dates"));
    }

    // ============ join_overlap_sql tests ============

    #[test]
    fn test_join_overlap_sql() {
        let sql = join_overlap_sql(
            "left_table", "right_table",
            &["id".to_string()], &["key".to_string()]
        );
        assert!(sql.contains("left_keys AS"));
        assert!(sql.contains("right_keys AS"));
        assert!(sql.contains("left_only"));
        assert!(sql.contains("right_only"));
        assert!(sql.contains("overlap_pct"));
        assert!(sql.contains("`id` AS key_0"));
        assert!(sql.contains("`key` AS key_0"));
        // Uses LEFT JOIN pattern, not EXISTS (SPARK-47070)
        assert!(sql.contains("LEFT JOIN"));
        assert!(sql.contains("INNER JOIN"));
        assert!(!sql.contains("NOT EXISTS"));
    }

    #[test]
    fn test_join_overlap_sql_null_safe() {
        let sql = join_overlap_sql(
            "left", "right",
            &["id".to_string()], &["id".to_string()]
        );
        assert!(sql.contains("<=>"), "Should use null-safe equality");
        assert!(sql.contains("lk.key_0 <=> rk.key_0"));
        // JOIN conditions use null-safe equality
        assert!(sql.contains("LEFT JOIN right_keys rk ON lk.key_0 <=> rk.key_0"));
    }

    #[test]
    fn test_join_overlap_sql_same_column_names() {
        // Reproduces SPARK-47070: same-named columns in both tables cause
        // attribute ID mismatch with correlated subqueries on CTEs
        let sql = join_overlap_sql(
            "orders", "orders2",
            &["o_orderdate".to_string()], &["o_orderdate".to_string()]
        );
        // Both should alias to key_0, avoiding column name collision
        assert!(sql.contains("`o_orderdate` AS key_0"));
        assert!(sql.contains("lk.key_0 <=> rk.key_0"));
        assert!(!sql.contains("lk.`o_orderdate`"));
        assert!(!sql.contains("rk.`o_orderdate`"));
        // Must NOT use EXISTS/NOT EXISTS to avoid SPARK-47070
        assert!(!sql.contains("NOT EXISTS"), "SPARK-47070: must use LEFT JOIN, not NOT EXISTS");
        assert!(!sql.contains("EXISTS"), "SPARK-47070: must use JOIN, not EXISTS");
    }

    #[test]
    fn test_join_overlap_sql_multiple_keys_same_names() {
        let sql = join_overlap_sql(
            "table1", "table2",
            &["col_a".to_string(), "col_b".to_string()],
            &["col_a".to_string(), "col_b".to_string()]
        );
        assert!(sql.contains("`col_a` AS key_0"));
        assert!(sql.contains("`col_b` AS key_1"));
        assert!(sql.contains("lk.key_0 <=> rk.key_0 AND lk.key_1 <=> rk.key_1"));
    }

    #[test]
    fn test_join_overlap_sql_special_chars_in_column() {
        let sql = join_overlap_sql(
            "tbl", "tbl2",
            &["col`name".to_string()], &["other".to_string()]
        );
        // Backticks in column names should be escaped
        assert!(sql.contains("`col``name` AS key_0"));
        assert!(sql.contains("`other` AS key_0"));
    }

    // ============ temporal_loss_sql tests ============

    #[test]
    fn test_temporal_loss_sql() {
        let sql = temporal_loss_sql("table", "date_col", "2023-01-01", "2023-12-31");
        assert!(sql.contains("rows_before"));
        assert!(sql.contains("rows_after"));
        assert!(sql.contains("total_lost"));
        assert!(sql.contains("pct_lost"));
        assert!(sql.contains("'2023-01-01'"));
        assert!(sql.contains("'2023-12-31'"));
    }

    // ============ is_numeric_type tests ============

    #[test]
    fn test_is_numeric_type_integers() {
        assert!(is_numeric_type("int"));
        assert!(is_numeric_type("INT"));
        assert!(is_numeric_type("bigint"));
        assert!(is_numeric_type("BIGINT"));
        assert!(is_numeric_type("smallint"));
        assert!(is_numeric_type("tinyint"));
    }

    #[test]
    fn test_is_numeric_type_floats() {
        assert!(is_numeric_type("float"));
        assert!(is_numeric_type("FLOAT"));
        assert!(is_numeric_type("double"));
        assert!(is_numeric_type("DOUBLE"));
    }

    #[test]
    fn test_is_numeric_type_decimal() {
        assert!(is_numeric_type("decimal"));
        assert!(is_numeric_type("DECIMAL(10,2)"));
        assert!(is_numeric_type("numeric"));
        assert!(is_numeric_type("NUMERIC(18,4)"));
    }

    #[test]
    fn test_is_numeric_type_non_numeric() {
        assert!(!is_numeric_type("string"));
        assert!(!is_numeric_type("varchar"));
        assert!(!is_numeric_type("boolean"));
        assert!(!is_numeric_type("date"));
        assert!(!is_numeric_type("timestamp"));
    }

    // ============ Alert SQL Generation Tests ============

    #[test]
    fn test_alert_threshold_sql_greater_than() {
        let result = alert_threshold_sql("orders", "amount", ">", 1000.0);
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("`amount` > 1000"));
        assert!(sql.contains("violations"));
        assert!(sql.contains("violation_pct"));
        assert!(sql.contains("MAX(`amount`)"));
        assert!(sql.contains("MIN(`amount`)"));
        assert!(sql.contains("AVG(`amount`)"));
    }

    #[test]
    fn test_alert_threshold_sql_less_than_or_equal() {
        let result = alert_threshold_sql("inventory", "stock", "<=", 10.0);
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("`stock` <= 10"));
    }

    #[test]
    fn test_alert_threshold_sql_equality() {
        let result = alert_threshold_sql("status", "code", "==", 0.0);
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("`code` = 0")); // == converted to =
    }

    #[test]
    fn test_alert_threshold_sql_invalid_operator() {
        let result = alert_threshold_sql("test", "col", "~=", 1.0);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Invalid operator"));
    }

    #[test]
    fn test_alert_null_rate_sql() {
        let sql = alert_null_rate_sql("customers", "email");
        assert!(sql.contains("COUNT(`email`) as non_null"));
        assert!(sql.contains("null_count"));
        assert!(sql.contains("null_pct"));
        assert!(sql.contains("`customers`"));
    }

    #[test]
    fn test_alert_row_count_sql_min_only() {
        let result = alert_row_count_sql("orders", Some(100), None);
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("COUNT(*) < 100"));
        assert!(sql.contains("'below_minimum'"));
        assert!(sql.contains("100 as min_threshold"));
        assert!(sql.contains("NULL as max_threshold"));
    }

    #[test]
    fn test_alert_row_count_sql_max_only() {
        let result = alert_row_count_sql("logs", None, Some(1000000));
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("COUNT(*) > 1000000"));
        assert!(sql.contains("'above_maximum'"));
        assert!(sql.contains("NULL as min_threshold"));
        assert!(sql.contains("1000000 as max_threshold"));
    }

    #[test]
    fn test_alert_row_count_sql_both_thresholds() {
        let result = alert_row_count_sql("metrics", Some(10), Some(1000));
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("COUNT(*) < 10"));
        assert!(sql.contains("COUNT(*) > 1000"));
        assert!(sql.contains("'within_range'"));
    }

    #[test]
    fn test_alert_row_count_sql_no_thresholds() {
        let result = alert_row_count_sql("test", None, None);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("At least one"));
    }

    #[test]
    fn test_alert_data_freshness_sql() {
        let sql = alert_data_freshness_sql("events", "created_at", 24);
        assert!(sql.contains("MAX(`created_at`) as latest_date"));
        assert!(sql.contains("TIMESTAMPDIFF(HOUR"));
        assert!(sql.contains("24 as max_age_hours"));
        assert!(sql.contains("'stale'"));
        assert!(sql.contains("'fresh'"));
    }

    #[test]
    fn test_alert_duplicate_keys_sql_single_key() {
        let result = alert_duplicate_keys_sql(
            "users",
            &["email".to_string()],
            Some(5)
        );
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("`email` as key_value"));
        assert!(sql.contains("HAVING COUNT(*) > 1"));
        assert!(sql.contains("duplicate_key_count"));
        assert!(sql.contains("5 as max_allowed_duplicates"));
    }

    #[test]
    fn test_alert_duplicate_keys_sql_composite_key() {
        let result = alert_duplicate_keys_sql(
            "orders",
            &["customer_id".to_string(), "order_date".to_string()],
            None
        );
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("CONCAT_WS('|'"));
        assert!(sql.contains("`customer_id`"));
        assert!(sql.contains("`order_date`"));
    }

    #[test]
    fn test_alert_duplicate_keys_sql_empty_keys() {
        let result = alert_duplicate_keys_sql("test", &[], None);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("At least one key"));
    }

    #[test]
    fn test_alert_reconciliation_sql() {
        let result = alert_reconciliation_sql(
            "source",
            "target",
            &["id".to_string()],
            95.0
        );
        assert!(result.is_ok());
        let sql = result.unwrap();
        assert!(sql.contains("source_count AS"));
        assert!(sql.contains("target_count AS"));
        assert!(sql.contains("matched AS"));
        assert!(sql.contains("match_rate_pct"));
        assert!(sql.contains("95 as min_match_rate_pct"));
        assert!(sql.contains("'below_threshold'"));
        assert!(sql.contains("'acceptable'"));
    }

    #[test]
    fn test_alert_reconciliation_sql_invalid_rate() {
        let result = alert_reconciliation_sql(
            "source",
            "target",
            &["id".to_string()],
            101.0
        );
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("between 0 and 100"));
    }

    #[test]
    fn test_alert_reconciliation_sql_empty_keys() {
        let result = alert_reconciliation_sql(
            "source",
            "target",
            &[],
            95.0
        );
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("At least one join key"));
    }

    #[test]
    fn test_generate_databricks_alert_query() {
        let inner_sql = "SELECT COUNT(*) as count FROM orders";
        let sql = generate_databricks_alert_query(
            inner_sql,
            "count",
            "Order Count Alert"
        );
        assert!(sql.contains("-- MangleFrames Generated Alert Query"));
        assert!(sql.contains("-- Name: Order Count Alert"));
        assert!(sql.contains("WITH alert_data AS"));
        assert!(sql.contains("`count` as alert_value"));
    }
}
