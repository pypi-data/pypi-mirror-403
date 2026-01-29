//! Statistics computation for DataFrame columns.

use arrow::array::Array;
use arrow::datatypes::{DataType, Schema};
use arrow::record_batch::RecordBatch;
use serde_json::{json, Value};
use tracing::info;

pub fn compute_stats(batches: &[RecordBatch]) -> Value {
    if batches.is_empty() {
        return json!({"columns": []});
    }

    let schema = batches[0].schema();
    let total_rows: usize = batches.iter().map(|b| b.num_rows()).sum();

    let columns: Vec<Value> = schema
        .fields()
        .iter()
        .enumerate()
        .map(|(col_idx, field)| {
            let mut null_count = 0usize;
            for batch in batches {
                null_count += batch.column(col_idx).null_count();
            }

            let mut stats = json!({
                "name": field.name(),
                "type": format!("{:?}", field.data_type()),
                "null_count": null_count,
                "non_null_count": total_rows - null_count,
            });

            if is_numeric(field.data_type()) {
                if let Some((min, max)) = compute_min_max(batches, col_idx) {
                    stats["min"] = json!(min);
                    stats["max"] = json!(max);
                }
            }

            stats
        })
        .collect();

    json!({
        "row_count": total_rows,
        "columns": columns
    })
}

fn is_numeric(dtype: &DataType) -> bool {
    matches!(
        dtype,
        DataType::Int8 | DataType::Int16 | DataType::Int32 | DataType::Int64
        | DataType::UInt8 | DataType::UInt16 | DataType::UInt32 | DataType::UInt64
        | DataType::Float32 | DataType::Float64
    )
}

fn compute_min_max(batches: &[RecordBatch], col_idx: usize) -> Option<(f64, f64)> {
    let mut min: Option<f64> = None;
    let mut max: Option<f64> = None;

    for batch in batches {
        let col = batch.column(col_idx);
        for i in 0..col.len() {
            if col.is_null(i) {
                continue;
            }
            if let Some(val) = extract_numeric(col.as_ref(), i) {
                min = Some(min.map_or(val, |m| m.min(val)));
                max = Some(max.map_or(val, |m| m.max(val)));
            }
        }
    }

    min.zip(max)
}

fn extract_numeric(array: &dyn Array, index: usize) -> Option<f64> {
    match array.data_type() {
        DataType::Int8 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Int8Array>()?;
            Some(arr.value(index) as f64)
        }
        DataType::Int16 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Int16Array>()?;
            Some(arr.value(index) as f64)
        }
        DataType::Int32 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Int32Array>()?;
            Some(arr.value(index) as f64)
        }
        DataType::Int64 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Int64Array>()?;
            Some(arr.value(index) as f64)
        }
        DataType::Float32 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Float32Array>()?;
            Some(arr.value(index) as f64)
        }
        DataType::Float64 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Float64Array>()?;
            Some(arr.value(index))
        }
        _ => None,
    }
}

/// Generate SQL aggregation query for computing stats on a Databricks table.
pub fn generate_stats_sql(table_name: &str, schema: &Schema) -> String {
    info!("Generating stats SQL for table: {}", table_name);

    let mut select_parts = vec!["COUNT(*) AS row_count".to_string()];

    for field in schema.fields() {
        let col_name = field.name();
        let quoted = format!("`{}`", col_name);

        select_parts.push(format!("COUNT({}) AS `{}_non_null`", quoted, col_name));
        select_parts.push(format!(
            "COUNT(*) - COUNT({}) AS `{}_null`",
            quoted, col_name
        ));

        if is_numeric(field.data_type()) {
            select_parts.push(format!("MIN({}) AS `{}_min`", quoted, col_name));
            select_parts.push(format!("MAX({}) AS `{}_max`", quoted, col_name));
        }
    }

    format!("SELECT {} FROM {}", select_parts.join(", "), table_name)
}

/// Parse SQL aggregation result into stats JSON format.
pub fn parse_stats_result(batches: &[RecordBatch], schema: &Schema) -> Value {
    info!("Parsing stats result from {} batches", batches.len());

    if batches.is_empty() || batches[0].num_rows() == 0 {
        return json!({"row_count": 0, "columns": []});
    }

    let result_batch = &batches[0];
    let result_schema = result_batch.schema();

    let row_count = get_result_value(result_batch, &result_schema, "row_count")
        .and_then(|v| v.as_i64())
        .unwrap_or(0) as usize;

    let columns: Vec<Value> = schema
        .fields()
        .iter()
        .map(|field| {
            let col_name = field.name();

            let non_null = get_result_value(
                result_batch,
                &result_schema,
                &format!("{}_non_null", col_name),
            )
            .and_then(|v| v.as_i64())
            .unwrap_or(0) as usize;

            let null_count = get_result_value(
                result_batch,
                &result_schema,
                &format!("{}_null", col_name),
            )
            .and_then(|v| v.as_i64())
            .unwrap_or(0) as usize;

            let mut stats = json!({
                "name": col_name,
                "type": format!("{:?}", field.data_type()),
                "null_count": null_count,
                "non_null_count": non_null,
            });

            if is_numeric(field.data_type()) {
                if let Some(min) = get_result_value(
                    result_batch,
                    &result_schema,
                    &format!("{}_min", col_name),
                )
                .and_then(|v| v.as_f64())
                {
                    stats["min"] = json!(min);
                }
                if let Some(max) = get_result_value(
                    result_batch,
                    &result_schema,
                    &format!("{}_max", col_name),
                )
                .and_then(|v| v.as_f64())
                {
                    stats["max"] = json!(max);
                }
            }

            stats
        })
        .collect();

    json!({
        "row_count": row_count,
        "columns": columns
    })
}

/// Extract a value from the result batch by column name.
fn get_result_value(
    batch: &RecordBatch,
    schema: &std::sync::Arc<Schema>,
    col_name: &str,
) -> Option<Value> {
    let col_idx = schema.index_of(col_name).ok()?;
    let col = batch.column(col_idx);

    if col.is_null(0) {
        return None;
    }

    match col.data_type() {
        DataType::Int64 => {
            let arr = col.as_any().downcast_ref::<arrow::array::Int64Array>()?;
            Some(json!(arr.value(0)))
        }
        DataType::Float64 => {
            let arr = col.as_any().downcast_ref::<arrow::array::Float64Array>()?;
            Some(json!(arr.value(0)))
        }
        DataType::Int32 => {
            let arr = col.as_any().downcast_ref::<arrow::array::Int32Array>()?;
            Some(json!(arr.value(0) as i64))
        }
        DataType::Float32 => {
            let arr = col.as_any().downcast_ref::<arrow::array::Float32Array>()?;
            Some(json!(arr.value(0) as f64))
        }
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use arrow::datatypes::Field;
    use crate::test_helpers::*;

    // ============ compute_stats tests ============

    #[test]
    fn test_compute_stats_empty() {
        let result = compute_stats(&[]);
        assert_eq!(result["columns"], json!([]));
    }

    #[test]
    fn test_compute_stats_string_column() {
        let batch = build_string_batch(&[
            ("name", vec![Some("Alice"), Some("Bob"), None]),
        ]);
        let result = compute_stats(&[batch]);

        assert_eq!(result["row_count"], 3);
        let columns = result["columns"].as_array().unwrap();
        assert_eq!(columns.len(), 1);
        assert_eq!(columns[0]["name"], "name");
        assert_eq!(columns[0]["null_count"], 1);
        assert_eq!(columns[0]["non_null_count"], 2);
    }

    #[test]
    fn test_compute_stats_numeric_column() {
        let batch = build_int64_batch(&[
            ("value", vec![Some(10), Some(20), Some(30), None]),
        ]);
        let result = compute_stats(&[batch]);

        assert_eq!(result["row_count"], 4);
        let columns = result["columns"].as_array().unwrap();
        assert_eq!(columns[0]["null_count"], 1);
        assert_eq!(columns[0]["non_null_count"], 3);
        assert_eq!(columns[0]["min"], 10.0);
        assert_eq!(columns[0]["max"], 30.0);
    }

    #[test]
    fn test_compute_stats_with_nulls() {
        let batch = build_batch_with_nulls(5, &[1, 3]);
        let result = compute_stats(&[batch]);

        assert_eq!(result["row_count"], 5);
        let columns = result["columns"].as_array().unwrap();
        // id column
        assert_eq!(columns[0]["null_count"], 2);
        assert_eq!(columns[0]["non_null_count"], 3);
        // name column
        assert_eq!(columns[1]["null_count"], 2);
        assert_eq!(columns[1]["non_null_count"], 3);
    }

    #[test]
    fn test_compute_stats_multiple_batches() {
        let batch1 = build_int64_batch(&[("id", vec![Some(1), Some(2)])]);
        let batch2 = build_int64_batch(&[("id", vec![Some(3), Some(4), Some(5)])]);
        let result = compute_stats(&[batch1, batch2]);

        assert_eq!(result["row_count"], 5);
        let columns = result["columns"].as_array().unwrap();
        assert_eq!(columns[0]["min"], 1.0);
        assert_eq!(columns[0]["max"], 5.0);
    }

    #[test]
    fn test_compute_stats_float_column() {
        let batch = build_float64_batch(&[
            ("rate", vec![Some(1.5), Some(2.5), Some(3.5)]),
        ]);
        let result = compute_stats(&[batch]);

        let columns = result["columns"].as_array().unwrap();
        assert_eq!(columns[0]["min"], 1.5);
        assert_eq!(columns[0]["max"], 3.5);
    }

    #[test]
    fn test_compute_stats_all_nulls() {
        let batch = build_int64_batch(&[("val", vec![None, None, None])]);
        let result = compute_stats(&[batch]);

        let columns = result["columns"].as_array().unwrap();
        assert_eq!(columns[0]["null_count"], 3);
        assert_eq!(columns[0]["non_null_count"], 0);
        // min/max should not be present for all-null numeric columns
        assert!(columns[0].get("min").is_none());
        assert!(columns[0].get("max").is_none());
    }

    // ============ is_numeric tests ============

    #[test]
    fn test_is_numeric_integers() {
        assert!(is_numeric(&DataType::Int8));
        assert!(is_numeric(&DataType::Int16));
        assert!(is_numeric(&DataType::Int32));
        assert!(is_numeric(&DataType::Int64));
    }

    #[test]
    fn test_is_numeric_unsigned() {
        assert!(is_numeric(&DataType::UInt8));
        assert!(is_numeric(&DataType::UInt16));
        assert!(is_numeric(&DataType::UInt32));
        assert!(is_numeric(&DataType::UInt64));
    }

    #[test]
    fn test_is_numeric_floats() {
        assert!(is_numeric(&DataType::Float32));
        assert!(is_numeric(&DataType::Float64));
    }

    #[test]
    fn test_is_numeric_non_numeric() {
        assert!(!is_numeric(&DataType::Utf8));
        assert!(!is_numeric(&DataType::Boolean));
        assert!(!is_numeric(&DataType::Date32));
    }

    // ============ compute_min_max tests ============

    #[test]
    fn test_compute_min_max_basic() {
        let batch = build_int64_batch(&[("val", vec![Some(5), Some(1), Some(10)])]);
        let result = compute_min_max(&[batch], 0);
        assert_eq!(result, Some((1.0, 10.0)));
    }

    #[test]
    fn test_compute_min_max_with_nulls() {
        let batch = build_int64_batch(&[("val", vec![Some(5), None, Some(10), None])]);
        let result = compute_min_max(&[batch], 0);
        assert_eq!(result, Some((5.0, 10.0)));
    }

    #[test]
    fn test_compute_min_max_all_nulls() {
        let batch = build_int64_batch(&[("val", vec![None, None])]);
        let result = compute_min_max(&[batch], 0);
        assert_eq!(result, None);
    }

    #[test]
    fn test_compute_min_max_negative() {
        let batch = build_int64_batch(&[("val", vec![Some(-10), Some(-5), Some(5)])]);
        let result = compute_min_max(&[batch], 0);
        assert_eq!(result, Some((-10.0, 5.0)));
    }

    // ============ extract_numeric tests ============

    #[test]
    fn test_extract_numeric_int64() {
        let batch = build_int64_batch(&[("val", vec![Some(42)])]);
        let col = batch.column(0);
        let result = extract_numeric(col.as_ref(), 0);
        assert_eq!(result, Some(42.0));
    }

    #[test]
    fn test_extract_numeric_float64() {
        let batch = build_float64_batch(&[("val", vec![Some(3.14)])]);
        let col = batch.column(0);
        let result = extract_numeric(col.as_ref(), 0);
        assert_eq!(result, Some(3.14));
    }

    #[test]
    fn test_extract_numeric_non_numeric() {
        let batch = build_string_batch(&[("val", vec![Some("test")])]);
        let col = batch.column(0);
        let result = extract_numeric(col.as_ref(), 0);
        assert_eq!(result, None);
    }

    // ============ generate_stats_sql tests ============

    #[test]
    fn test_generate_stats_sql_numeric() {
        let schema = Schema::new(vec![
            Field::new("id", DataType::Int64, true),
            Field::new("amount", DataType::Float64, true),
        ]);
        let sql = generate_stats_sql("my_table", &schema);

        assert!(sql.contains("COUNT(*) AS row_count"));
        assert!(sql.contains("`id_non_null`"));
        assert!(sql.contains("`id_null`"));
        assert!(sql.contains("MIN(`id`)"));
        assert!(sql.contains("MAX(`id`)"));
        assert!(sql.contains("MIN(`amount`)"));
        assert!(sql.contains("MAX(`amount`)"));
    }

    #[test]
    fn test_generate_stats_sql_non_numeric() {
        let schema = Schema::new(vec![Field::new("name", DataType::Utf8, true)]);
        let sql = generate_stats_sql("my_table", &schema);

        assert!(sql.contains("`name_non_null`"));
        assert!(sql.contains("`name_null`"));
        assert!(!sql.contains("MIN(`name`)"));
        assert!(!sql.contains("MAX(`name`)"));
    }

    // ============ parse_stats_result tests ============

    #[test]
    fn test_parse_stats_result_empty() {
        let schema = Schema::new(vec![Field::new("id", DataType::Int64, true)]);
        let result = parse_stats_result(&[], &schema);
        assert_eq!(result["row_count"], 0);
        assert_eq!(result["columns"], json!([]));
    }

    #[test]
    fn test_parse_stats_result_basic() {
        // Create a mock stats result batch
        let batch = build_int64_batch(&[
            ("row_count", vec![Some(100)]),
            ("id_non_null", vec![Some(95)]),
            ("id_null", vec![Some(5)]),
            ("id_min", vec![Some(1)]),
            ("id_max", vec![Some(1000)]),
        ]);
        let schema = Schema::new(vec![Field::new("id", DataType::Int64, true)]);
        let result = parse_stats_result(&[batch], &schema);

        assert_eq!(result["row_count"], 100);
        let columns = result["columns"].as_array().unwrap();
        assert_eq!(columns.len(), 1);
        assert_eq!(columns[0]["name"], "id");
        assert_eq!(columns[0]["non_null_count"], 95);
        assert_eq!(columns[0]["null_count"], 5);
    }
}
