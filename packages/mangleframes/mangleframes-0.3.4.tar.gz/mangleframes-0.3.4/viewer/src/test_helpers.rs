//! Test helpers for building Arrow RecordBatches.

use std::sync::Arc;

use arrow::array::{
    ArrayRef, BooleanArray, Date32Array, Decimal128Array, Float32Array, Float64Array,
    Int32Array, Int64Array, Int8Array, StringArray, TimestampMicrosecondArray,
    UInt32Array, UInt64Array,
};
use arrow::datatypes::{DataType, Field, Schema};
use arrow::record_batch::RecordBatch;

/// Build a RecordBatch with string columns.
pub fn build_string_batch(columns: &[(&str, Vec<Option<&str>>)]) -> RecordBatch {
    let fields: Vec<Field> = columns
        .iter()
        .map(|(name, _)| Field::new(*name, DataType::Utf8, true))
        .collect();
    let schema = Arc::new(Schema::new(fields));

    let arrays: Vec<ArrayRef> = columns
        .iter()
        .map(|(_, values)| Arc::new(StringArray::from(values.clone())) as ArrayRef)
        .collect();

    RecordBatch::try_new(schema, arrays).unwrap()
}

/// Build a RecordBatch with Int64 columns.
pub fn build_int64_batch(columns: &[(&str, Vec<Option<i64>>)]) -> RecordBatch {
    let fields: Vec<Field> = columns
        .iter()
        .map(|(name, _)| Field::new(*name, DataType::Int64, true))
        .collect();
    let schema = Arc::new(Schema::new(fields));

    let arrays: Vec<ArrayRef> = columns
        .iter()
        .map(|(_, values)| Arc::new(Int64Array::from(values.clone())) as ArrayRef)
        .collect();

    RecordBatch::try_new(schema, arrays).unwrap()
}

/// Build a RecordBatch with Float64 columns.
pub fn build_float64_batch(columns: &[(&str, Vec<Option<f64>>)]) -> RecordBatch {
    let fields: Vec<Field> = columns
        .iter()
        .map(|(name, _)| Field::new(*name, DataType::Float64, true))
        .collect();
    let schema = Arc::new(Schema::new(fields));

    let arrays: Vec<ArrayRef> = columns
        .iter()
        .map(|(_, values)| Arc::new(Float64Array::from(values.clone())) as ArrayRef)
        .collect();

    RecordBatch::try_new(schema, arrays).unwrap()
}

/// Build a RecordBatch simulating SHOW TABLES result.
pub fn build_tables_batch(tables: &[(&str, &str)]) -> RecordBatch {
    let namespaces: Vec<Option<&str>> = tables.iter().map(|(ns, _)| Some(*ns)).collect();
    let table_names: Vec<Option<&str>> = tables.iter().map(|(_, t)| Some(*t)).collect();

    build_string_batch(&[("namespace", namespaces), ("tableName", table_names)])
}

/// Build a RecordBatch simulating DESCRIBE TABLE result.
pub fn build_describe_batch(columns: &[(&str, &str, &str)]) -> RecordBatch {
    let col_names: Vec<Option<&str>> = columns.iter().map(|(n, _, _)| Some(*n)).collect();
    let data_types: Vec<Option<&str>> = columns.iter().map(|(_, t, _)| Some(*t)).collect();
    let comments: Vec<Option<&str>> = columns.iter().map(|(_, _, c)| Some(*c)).collect();

    build_string_batch(&[
        ("col_name", col_names),
        ("data_type", data_types),
        ("comment", comments),
    ])
}

/// Build a RecordBatch with mixed types.
pub fn build_mixed_batch(
    string_cols: &[(&str, Vec<Option<&str>>)],
    int_cols: &[(&str, Vec<Option<i64>>)],
    float_cols: &[(&str, Vec<Option<f64>>)],
) -> RecordBatch {
    let mut fields = Vec::new();
    let mut arrays: Vec<ArrayRef> = Vec::new();

    for (name, values) in string_cols {
        fields.push(Field::new(*name, DataType::Utf8, true));
        arrays.push(Arc::new(StringArray::from(values.clone())));
    }
    for (name, values) in int_cols {
        fields.push(Field::new(*name, DataType::Int64, true));
        arrays.push(Arc::new(Int64Array::from(values.clone())));
    }
    for (name, values) in float_cols {
        fields.push(Field::new(*name, DataType::Float64, true));
        arrays.push(Arc::new(Float64Array::from(values.clone())));
    }

    let schema = Arc::new(Schema::new(fields));
    RecordBatch::try_new(schema, arrays).unwrap()
}

/// Build a RecordBatch with all supported numeric types for comprehensive testing.
pub fn build_all_numeric_types_batch(row_count: usize) -> RecordBatch {
    let fields = vec![
        Field::new("int8_col", DataType::Int8, true),
        Field::new("int32_col", DataType::Int32, true),
        Field::new("int64_col", DataType::Int64, true),
        Field::new("uint32_col", DataType::UInt32, true),
        Field::new("uint64_col", DataType::UInt64, true),
        Field::new("float32_col", DataType::Float32, true),
        Field::new("float64_col", DataType::Float64, true),
    ];
    let schema = Arc::new(Schema::new(fields));

    let int8_values: Vec<Option<i8>> = (0..row_count).map(|i| Some(i as i8)).collect();
    let int32_values: Vec<Option<i32>> = (0..row_count).map(|i| Some(i as i32 * 10)).collect();
    let int64_values: Vec<Option<i64>> = (0..row_count).map(|i| Some(i as i64 * 100)).collect();
    let uint32_values: Vec<Option<u32>> = (0..row_count).map(|i| Some(i as u32 * 5)).collect();
    let uint64_values: Vec<Option<u64>> = (0..row_count).map(|i| Some(i as u64 * 50)).collect();
    let float32_values: Vec<Option<f32>> = (0..row_count).map(|i| Some(i as f32 * 1.5)).collect();
    let float64_values: Vec<Option<f64>> = (0..row_count).map(|i| Some(i as f64 * 2.5)).collect();

    let arrays: Vec<ArrayRef> = vec![
        Arc::new(Int8Array::from(int8_values)),
        Arc::new(Int32Array::from(int32_values)),
        Arc::new(Int64Array::from(int64_values)),
        Arc::new(UInt32Array::from(uint32_values)),
        Arc::new(UInt64Array::from(uint64_values)),
        Arc::new(Float32Array::from(float32_values)),
        Arc::new(Float64Array::from(float64_values)),
    ];

    RecordBatch::try_new(schema, arrays).unwrap()
}

/// Build a RecordBatch with boolean column.
pub fn build_boolean_batch(name: &str, values: Vec<Option<bool>>) -> RecordBatch {
    let fields = vec![Field::new(name, DataType::Boolean, true)];
    let schema = Arc::new(Schema::new(fields));
    let arrays: Vec<ArrayRef> = vec![Arc::new(BooleanArray::from(values))];
    RecordBatch::try_new(schema, arrays).unwrap()
}

/// Build a RecordBatch with Date32 column.
pub fn build_date32_batch(name: &str, values: Vec<Option<i32>>) -> RecordBatch {
    let fields = vec![Field::new(name, DataType::Date32, true)];
    let schema = Arc::new(Schema::new(fields));
    let arrays: Vec<ArrayRef> = vec![Arc::new(Date32Array::from(values))];
    RecordBatch::try_new(schema, arrays).unwrap()
}

/// Build a RecordBatch with Decimal128 column.
pub fn build_decimal128_batch(
    name: &str,
    values: Vec<Option<i128>>,
    precision: u8,
    scale: i8,
) -> RecordBatch {
    let fields = vec![Field::new(name, DataType::Decimal128(precision, scale), true)];
    let schema = Arc::new(Schema::new(fields));
    let arrays: Vec<ArrayRef> = vec![Arc::new(
        Decimal128Array::from(values)
            .with_precision_and_scale(precision, scale)
            .unwrap(),
    )];
    RecordBatch::try_new(schema, arrays).unwrap()
}

/// Build a RecordBatch with TimestampMicrosecond column.
pub fn build_timestamp_batch(name: &str, values: Vec<Option<i64>>) -> RecordBatch {
    let fields = vec![Field::new(
        name,
        DataType::Timestamp(arrow::datatypes::TimeUnit::Microsecond, None),
        true,
    )];
    let schema = Arc::new(Schema::new(fields));
    let arrays: Vec<ArrayRef> = vec![Arc::new(TimestampMicrosecondArray::from(values))];
    RecordBatch::try_new(schema, arrays).unwrap()
}

/// Build a RecordBatch with nulls in specific positions.
pub fn build_batch_with_nulls(row_count: usize, null_positions: &[usize]) -> RecordBatch {
    let fields = vec![
        Field::new("id", DataType::Int64, true),
        Field::new("name", DataType::Utf8, true),
    ];
    let schema = Arc::new(Schema::new(fields));

    let id_values: Vec<Option<i64>> = (0..row_count)
        .map(|i| {
            if null_positions.contains(&i) {
                None
            } else {
                Some(i as i64)
            }
        })
        .collect();
    let name_values: Vec<Option<&str>> = (0..row_count)
        .map(|i| {
            if null_positions.contains(&i) {
                None
            } else {
                Some("value")
            }
        })
        .collect();

    let arrays: Vec<ArrayRef> = vec![
        Arc::new(Int64Array::from(id_values)),
        Arc::new(StringArray::from(name_values)),
    ];

    RecordBatch::try_new(schema, arrays).unwrap()
}

/// Build a simple RecordBatch for join statistics testing.
pub fn build_join_stats_batch(
    left_total: i64,
    left_distinct: i64,
    left_null_keys: i64,
    left_duplicate_keys: i64,
    right_total: i64,
    right_distinct: i64,
    right_null_keys: i64,
    right_duplicate_keys: i64,
    left_matched: i64,
    right_matched: i64,
    pairs: i64,
    left_only: i64,
    right_only: i64,
) -> RecordBatch {
    build_int64_batch(&[
        ("left_total", vec![Some(left_total)]),
        ("left_distinct", vec![Some(left_distinct)]),
        ("left_null_keys", vec![Some(left_null_keys)]),
        ("left_duplicate_keys", vec![Some(left_duplicate_keys)]),
        ("right_total", vec![Some(right_total)]),
        ("right_distinct", vec![Some(right_distinct)]),
        ("right_null_keys", vec![Some(right_null_keys)]),
        ("right_duplicate_keys", vec![Some(right_duplicate_keys)]),
        ("left_matched", vec![Some(left_matched)]),
        ("right_matched", vec![Some(right_matched)]),
        ("pairs", vec![Some(pairs)]),
        ("left_only", vec![Some(left_only)]),
        ("right_only", vec![Some(right_only)]),
    ])
}

/// Build an empty RecordBatch with a given schema.
pub fn build_empty_batch(field_names: &[(&str, DataType)]) -> RecordBatch {
    let fields: Vec<Field> = field_names
        .iter()
        .map(|(name, dtype)| Field::new(*name, dtype.clone(), true))
        .collect();
    let schema = Arc::new(Schema::new(fields));
    RecordBatch::new_empty(schema)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_build_string_batch() {
        let batch = build_string_batch(&[
            ("col1", vec![Some("a"), Some("b"), None]),
            ("col2", vec![Some("x"), None, Some("z")]),
        ]);
        assert_eq!(batch.num_rows(), 3);
        assert_eq!(batch.num_columns(), 2);
    }

    #[test]
    fn test_build_int64_batch() {
        let batch = build_int64_batch(&[
            ("id", vec![Some(1), Some(2), Some(3)]),
            ("amount", vec![Some(100), None, Some(300)]),
        ]);
        assert_eq!(batch.num_rows(), 3);
        assert_eq!(batch.num_columns(), 2);
    }

    #[test]
    fn test_build_tables_batch() {
        let batch = build_tables_batch(&[("default", "users"), ("catalog", "orders")]);
        assert_eq!(batch.num_rows(), 2);
        assert_eq!(batch.schema().fields().len(), 2);
    }

    #[test]
    fn test_build_batch_with_nulls() {
        let batch = build_batch_with_nulls(5, &[1, 3]);
        assert_eq!(batch.num_rows(), 5);
        assert_eq!(batch.column(0).null_count(), 2);
        assert_eq!(batch.column(1).null_count(), 2);
    }

    #[test]
    fn test_build_empty_batch() {
        let batch = build_empty_batch(&[
            ("id", DataType::Int64),
            ("name", DataType::Utf8),
        ]);
        assert_eq!(batch.num_rows(), 0);
        assert_eq!(batch.num_columns(), 2);
    }
}
