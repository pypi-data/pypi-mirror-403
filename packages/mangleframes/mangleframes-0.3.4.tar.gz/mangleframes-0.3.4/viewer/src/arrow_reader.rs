//! Arrow IPC stream parsing and JSON conversion.

use std::io::Cursor;

use arrow::array::{Array, AsArray, RecordBatch};
use arrow::datatypes::{DataType, Date32Type, Decimal128Type, DecimalType};
use arrow::temporal_conversions::date32_to_datetime;
use arrow_ipc::reader::StreamReader;
use serde_json::{json, Value};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ArrowError {
    #[error("Failed to parse Arrow IPC: {0}")]
    ParseError(#[from] arrow::error::ArrowError),
}

pub fn parse_arrow_stream(data: &[u8]) -> Result<Vec<RecordBatch>, ArrowError> {
    let cursor = Cursor::new(data);
    let reader = StreamReader::try_new(cursor, None)?;
    let batches: Result<Vec<_>, _> = reader.collect();
    Ok(batches?)
}

/// Convert Arrow batches to JSON bytes with proper type handling.
/// Handles Decimal128, Date32, Timestamp, and all primitive types correctly.
pub fn batches_to_json_bytes(batches: &[RecordBatch], offset: usize, limit: usize) -> (Vec<u8>, usize) {
    if batches.is_empty() {
        return (b"[]".to_vec(), 0);
    }

    let total_rows: usize = batches.iter().map(|b| b.num_rows()).sum();
    let actual_limit = limit.min(total_rows.saturating_sub(offset));
    if actual_limit == 0 {
        return (b"[]".to_vec(), 0);
    }

    let sliced = slice_batches(batches, offset, actual_limit);
    if sliced.is_empty() {
        return (b"[]".to_vec(), 0);
    }

    // Build JSON array using custom type handling
    let mut rows: Vec<Value> = Vec::with_capacity(actual_limit);
    for batch in &sliced {
        for row_idx in 0..batch.num_rows() {
            let mut row = serde_json::Map::new();
            for (col_idx, field) in batch.schema().fields().iter().enumerate() {
                let col = batch.column(col_idx);
                let value = array_value_to_json(col.as_ref(), row_idx);
                row.insert(field.name().clone(), value);
            }
            rows.push(Value::Object(row));
        }
    }

    let row_count = rows.len();
    let bytes = serde_json::to_vec(&rows).unwrap_or_else(|_| b"[]".to_vec());
    (bytes, row_count)
}

fn array_value_to_json(array: &dyn Array, index: usize) -> Value {
    if array.is_null(index) {
        return Value::Null;
    }

    match array.data_type() {
        DataType::Boolean => {
            json!(array.as_boolean().value(index))
        }
        DataType::Int8 => {
            json!(array.as_primitive::<arrow::datatypes::Int8Type>().value(index))
        }
        DataType::Int16 => {
            json!(array.as_primitive::<arrow::datatypes::Int16Type>().value(index))
        }
        DataType::Int32 => {
            json!(array.as_primitive::<arrow::datatypes::Int32Type>().value(index))
        }
        DataType::Int64 => {
            json!(array.as_primitive::<arrow::datatypes::Int64Type>().value(index))
        }
        DataType::UInt8 => {
            json!(array.as_primitive::<arrow::datatypes::UInt8Type>().value(index))
        }
        DataType::UInt16 => {
            json!(array.as_primitive::<arrow::datatypes::UInt16Type>().value(index))
        }
        DataType::UInt32 => {
            json!(array.as_primitive::<arrow::datatypes::UInt32Type>().value(index))
        }
        DataType::UInt64 => {
            json!(array.as_primitive::<arrow::datatypes::UInt64Type>().value(index))
        }
        DataType::Float32 => {
            json!(array.as_primitive::<arrow::datatypes::Float32Type>().value(index))
        }
        DataType::Float64 => {
            json!(array.as_primitive::<arrow::datatypes::Float64Type>().value(index))
        }
        DataType::Utf8 => {
            json!(array.as_string::<i32>().value(index))
        }
        DataType::LargeUtf8 => {
            json!(array.as_string::<i64>().value(index))
        }
        DataType::Date32 => {
            let days = array.as_primitive::<Date32Type>().value(index);
            match date32_to_datetime(days) {
                Some(dt) => json!(dt.format("%Y-%m-%d").to_string()),
                None => Value::Null,
            }
        }
        DataType::Decimal128(precision, scale) => {
            let arr = array.as_primitive::<Decimal128Type>();
            let value = arr.value(index);
            json!(Decimal128Type::format_decimal(value, *precision, *scale))
        }
        DataType::Timestamp(_, _) => {
            // Format timestamp as ISO string
            use arrow::array::TimestampMicrosecondArray;
            if let Some(ts_array) = array.as_any().downcast_ref::<TimestampMicrosecondArray>() {
                let micros = ts_array.value(index);
                let secs = micros / 1_000_000;
                let nsecs = ((micros % 1_000_000) * 1000) as u32;
                if let Some(dt) = chrono::DateTime::from_timestamp(secs, nsecs) {
                    return json!(dt.format("%Y-%m-%dT%H:%M:%S%.6f").to_string());
                }
            }
            json!(format!("{:?}", array.data_type()))
        }
        _ => json!(format!("{:?}", array.data_type())),
    }
}

/// Legacy function for compatibility - parses back to Value
pub fn batches_to_json(batches: &[RecordBatch], offset: usize, limit: usize) -> Value {
    let (bytes, _) = batches_to_json_bytes(batches, offset, limit);
    serde_json::from_slice(&bytes).unwrap_or(Value::Array(vec![]))
}

/// Slice batches to extract rows in range [offset, offset+limit)
fn slice_batches(batches: &[RecordBatch], offset: usize, limit: usize) -> Vec<RecordBatch> {
    let mut result = Vec::new();
    let mut current_offset = 0;
    let mut remaining = limit;

    for batch in batches {
        let batch_rows = batch.num_rows();

        if current_offset + batch_rows <= offset {
            current_offset += batch_rows;
            continue;
        }

        let start = if current_offset < offset { offset - current_offset } else { 0 };
        let len = remaining.min(batch_rows - start);

        if len > 0 {
            let sliced = batch.slice(start, len);
            result.push(sliced);
            remaining -= len;
        }

        if remaining == 0 {
            break;
        }
        current_offset += batch_rows;
    }

    result
}

pub fn total_row_count(batches: &[RecordBatch]) -> usize {
    batches.iter().map(|b| b.num_rows()).sum()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_helpers::*;

    // ============ batches_to_json_bytes tests ============

    #[test]
    fn test_batches_to_json_bytes_empty() {
        let (bytes, count) = batches_to_json_bytes(&[], 0, 100);
        assert_eq!(bytes, b"[]");
        assert_eq!(count, 0);
    }

    #[test]
    fn test_batches_to_json_bytes_standard() {
        let batch = build_string_batch(&[
            ("name", vec![Some("Alice"), Some("Bob")]),
            ("city", vec![Some("NYC"), Some("LA")]),
        ]);
        let (bytes, count) = batches_to_json_bytes(&[batch], 0, 10);
        assert_eq!(count, 2);
        let json: Value = serde_json::from_slice(&bytes).unwrap();
        let arr = json.as_array().unwrap();
        assert_eq!(arr.len(), 2);
        assert_eq!(arr[0]["name"], "Alice");
        assert_eq!(arr[1]["city"], "LA");
    }

    #[test]
    fn test_batches_to_json_bytes_with_offset() {
        let batch = build_int64_batch(&[("id", vec![Some(1), Some(2), Some(3), Some(4), Some(5)])]);
        let (bytes, count) = batches_to_json_bytes(&[batch], 2, 2);
        assert_eq!(count, 2);
        let json: Value = serde_json::from_slice(&bytes).unwrap();
        let arr = json.as_array().unwrap();
        assert_eq!(arr[0]["id"], 3);
        assert_eq!(arr[1]["id"], 4);
    }

    #[test]
    fn test_batches_to_json_bytes_offset_beyond_data() {
        let batch = build_int64_batch(&[("id", vec![Some(1), Some(2)])]);
        let (bytes, count) = batches_to_json_bytes(&[batch], 100, 10);
        assert_eq!(bytes, b"[]");
        assert_eq!(count, 0);
    }

    #[test]
    fn test_batches_to_json_bytes_limit_exceeds_data() {
        let batch = build_int64_batch(&[("id", vec![Some(1), Some(2)])]);
        let (bytes, count) = batches_to_json_bytes(&[batch], 0, 1000);
        assert_eq!(count, 2);
    }

    // ============ batches_to_json tests ============

    #[test]
    fn test_batches_to_json_roundtrip() {
        let batch = build_string_batch(&[
            ("col1", vec![Some("a"), Some("b")]),
        ]);
        let json = batches_to_json(&[batch], 0, 10);
        let arr = json.as_array().unwrap();
        assert_eq!(arr.len(), 2);
        assert_eq!(arr[0]["col1"], "a");
    }

    #[test]
    fn test_batches_to_json_empty() {
        let json = batches_to_json(&[], 0, 10);
        assert_eq!(json, Value::Array(vec![]));
    }

    // ============ slice_batches tests ============

    #[test]
    fn test_slice_batches_within_single_batch() {
        let batch = build_int64_batch(&[("id", vec![Some(1), Some(2), Some(3), Some(4), Some(5)])]);
        let sliced = slice_batches(&[batch], 1, 2);
        assert_eq!(sliced.len(), 1);
        assert_eq!(sliced[0].num_rows(), 2);
    }

    #[test]
    fn test_slice_batches_across_batches() {
        let batch1 = build_int64_batch(&[("id", vec![Some(1), Some(2)])]);
        let batch2 = build_int64_batch(&[("id", vec![Some(3), Some(4)])]);
        let sliced = slice_batches(&[batch1, batch2], 1, 3);
        let total_rows: usize = sliced.iter().map(|b| b.num_rows()).sum();
        assert_eq!(total_rows, 3);
    }

    #[test]
    fn test_slice_batches_empty_input() {
        let sliced = slice_batches(&[], 0, 10);
        assert!(sliced.is_empty());
    }

    #[test]
    fn test_slice_batches_offset_skips_entire_batch() {
        let batch1 = build_int64_batch(&[("id", vec![Some(1), Some(2)])]);
        let batch2 = build_int64_batch(&[("id", vec![Some(3), Some(4)])]);
        let sliced = slice_batches(&[batch1, batch2], 2, 2);
        assert_eq!(sliced.len(), 1);
        assert_eq!(sliced[0].num_rows(), 2);
    }

    // ============ total_row_count tests ============

    #[test]
    fn test_total_row_count_single_batch() {
        let batch = build_int64_batch(&[("id", vec![Some(1), Some(2), Some(3)])]);
        assert_eq!(total_row_count(&[batch]), 3);
    }

    #[test]
    fn test_total_row_count_multiple_batches() {
        let batch1 = build_int64_batch(&[("id", vec![Some(1), Some(2)])]);
        let batch2 = build_int64_batch(&[("id", vec![Some(3), Some(4), Some(5)])]);
        assert_eq!(total_row_count(&[batch1, batch2]), 5);
    }

    #[test]
    fn test_total_row_count_empty() {
        assert_eq!(total_row_count(&[]), 0);
    }

    // ============ array_value_to_json tests ============

    #[test]
    fn test_array_value_to_json_boolean() {
        let batch = build_boolean_batch("flag", vec![Some(true), Some(false), None]);
        let col = batch.column(0);
        assert_eq!(array_value_to_json(col.as_ref(), 0), json!(true));
        assert_eq!(array_value_to_json(col.as_ref(), 1), json!(false));
        assert_eq!(array_value_to_json(col.as_ref(), 2), Value::Null);
    }

    #[test]
    fn test_array_value_to_json_int64() {
        let batch = build_int64_batch(&[("num", vec![Some(42), Some(-100), None])]);
        let col = batch.column(0);
        assert_eq!(array_value_to_json(col.as_ref(), 0), json!(42));
        assert_eq!(array_value_to_json(col.as_ref(), 1), json!(-100));
        assert_eq!(array_value_to_json(col.as_ref(), 2), Value::Null);
    }

    #[test]
    fn test_array_value_to_json_float64() {
        let batch = build_float64_batch(&[("val", vec![Some(3.14), Some(-2.5), None])]);
        let col = batch.column(0);
        assert_eq!(array_value_to_json(col.as_ref(), 0), json!(3.14));
        assert_eq!(array_value_to_json(col.as_ref(), 1), json!(-2.5));
        assert_eq!(array_value_to_json(col.as_ref(), 2), Value::Null);
    }

    #[test]
    fn test_array_value_to_json_string() {
        let batch = build_string_batch(&[("name", vec![Some("hello"), Some(""), None])]);
        let col = batch.column(0);
        assert_eq!(array_value_to_json(col.as_ref(), 0), json!("hello"));
        assert_eq!(array_value_to_json(col.as_ref(), 1), json!(""));
        assert_eq!(array_value_to_json(col.as_ref(), 2), Value::Null);
    }

    #[test]
    fn test_array_value_to_json_date32() {
        // 19358 days since epoch = 2023-01-01
        let batch = build_date32_batch("date", vec![Some(19358), None]);
        let col = batch.column(0);
        let val = array_value_to_json(col.as_ref(), 0);
        assert!(val.as_str().unwrap().contains("2023"));
        assert_eq!(array_value_to_json(col.as_ref(), 1), Value::Null);
    }

    #[test]
    fn test_array_value_to_json_decimal128() {
        // 12345 with scale 2 = 123.45
        let batch = build_decimal128_batch("amount", vec![Some(12345), None], 10, 2);
        let col = batch.column(0);
        let val = array_value_to_json(col.as_ref(), 0);
        assert!(val.as_str().unwrap().contains("123.45"));
        assert_eq!(array_value_to_json(col.as_ref(), 1), Value::Null);
    }

    #[test]
    fn test_array_value_to_json_timestamp() {
        // 1672531200000000 microseconds since epoch = 2023-01-01 00:00:00 UTC
        let batch = build_timestamp_batch("ts", vec![Some(1672531200000000), None]);
        let col = batch.column(0);
        let val = array_value_to_json(col.as_ref(), 0);
        assert!(val.as_str().unwrap().contains("2023-01-01"));
        assert_eq!(array_value_to_json(col.as_ref(), 1), Value::Null);
    }

    #[test]
    fn test_array_value_to_json_all_numeric_types() {
        let batch = build_all_numeric_types_batch(3);

        // Test Int8
        let int8_col = batch.column(0);
        assert_eq!(array_value_to_json(int8_col.as_ref(), 0), json!(0));
        assert_eq!(array_value_to_json(int8_col.as_ref(), 1), json!(1));

        // Test Int32
        let int32_col = batch.column(1);
        assert_eq!(array_value_to_json(int32_col.as_ref(), 0), json!(0));
        assert_eq!(array_value_to_json(int32_col.as_ref(), 1), json!(10));

        // Test Float32
        let float32_col = batch.column(5);
        let f32_val = array_value_to_json(float32_col.as_ref(), 1);
        assert!((f32_val.as_f64().unwrap() - 1.5).abs() < 0.01);
    }

    // ============ Integration tests ============

    #[test]
    fn test_json_conversion_preserves_nulls() {
        let batch = build_batch_with_nulls(5, &[1, 3]);
        let json = batches_to_json(&[batch], 0, 10);
        let arr = json.as_array().unwrap();

        assert!(arr[1]["id"].is_null());
        assert!(arr[1]["name"].is_null());
        assert!(arr[3]["id"].is_null());
        assert!(!arr[0]["id"].is_null());
        assert!(!arr[2]["id"].is_null());
    }

    #[test]
    fn test_json_conversion_mixed_types() {
        let batch = build_mixed_batch(
            &[("name", vec![Some("Alice"), Some("Bob")])],
            &[("age", vec![Some(30), Some(25)])],
            &[("score", vec![Some(95.5), Some(88.0)])],
        );
        let json = batches_to_json(&[batch], 0, 10);
        let arr = json.as_array().unwrap();

        assert_eq!(arr[0]["name"], "Alice");
        assert_eq!(arr[0]["age"], 30);
        assert_eq!(arr[0]["score"], 95.5);
    }
}
