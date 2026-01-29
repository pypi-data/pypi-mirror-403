//! Export DataFrame to various formats.

use arrow::record_batch::RecordBatch;
use arrow_csv::WriterBuilder as CsvWriterBuilder;
use arrow_json::LineDelimitedWriter;
use parquet::arrow::ArrowWriter;
use parquet::basic::Compression;
use parquet::file::properties::WriterProperties;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ExportError {
    #[error("Arrow error: {0}")]
    Arrow(#[from] arrow::error::ArrowError),
    #[error("Parquet error: {0}")]
    Parquet(#[from] parquet::errors::ParquetError),
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("No data to export")]
    NoData,
}

pub fn to_csv(batches: &[RecordBatch]) -> Result<Vec<u8>, ExportError> {
    if batches.is_empty() {
        return Err(ExportError::NoData);
    }

    let mut buffer = Vec::new();
    let mut writer = CsvWriterBuilder::new()
        .with_header(true)
        .build(&mut buffer);

    for batch in batches {
        writer.write(batch)?;
    }

    drop(writer);
    Ok(buffer)
}

pub fn to_json(batches: &[RecordBatch]) -> Result<Vec<u8>, ExportError> {
    if batches.is_empty() {
        return Err(ExportError::NoData);
    }

    let mut buffer = Vec::new();
    let mut writer = LineDelimitedWriter::new(&mut buffer);

    for batch in batches {
        writer.write(batch)?;
    }

    writer.finish()?;
    Ok(buffer)
}

pub fn to_parquet(batches: &[RecordBatch]) -> Result<Vec<u8>, ExportError> {
    if batches.is_empty() {
        return Err(ExportError::NoData);
    }

    let schema = batches[0].schema();
    let mut buffer = Vec::new();

    let props = WriterProperties::builder()
        .set_compression(Compression::SNAPPY)
        .build();

    let mut writer = ArrowWriter::try_new(&mut buffer, schema, Some(props))?;

    for batch in batches {
        writer.write(batch)?;
    }

    writer.close()?;
    Ok(buffer)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_helpers::*;

    // ============ to_csv tests ============

    #[test]
    fn test_to_csv_success() {
        let batch = build_string_batch(&[
            ("name", vec![Some("Alice"), Some("Bob")]),
            ("city", vec![Some("NYC"), Some("LA")]),
        ]);
        let result = to_csv(&[batch]);
        assert!(result.is_ok());

        let csv_str = String::from_utf8(result.unwrap()).unwrap();
        assert!(csv_str.contains("name"));
        assert!(csv_str.contains("city"));
        assert!(csv_str.contains("Alice"));
        assert!(csv_str.contains("Bob"));
    }

    #[test]
    fn test_to_csv_empty_batches() {
        let result = to_csv(&[]);
        assert!(matches!(result, Err(ExportError::NoData)));
    }

    #[test]
    fn test_to_csv_numeric_data() {
        let batch = build_int64_batch(&[
            ("id", vec![Some(1), Some(2), Some(3)]),
            ("value", vec![Some(100), Some(200), Some(300)]),
        ]);
        let result = to_csv(&[batch]);
        assert!(result.is_ok());

        let csv_str = String::from_utf8(result.unwrap()).unwrap();
        assert!(csv_str.contains("id"));
        assert!(csv_str.contains("100"));
        assert!(csv_str.contains("200"));
    }

    // ============ to_json tests ============

    #[test]
    fn test_to_json_success() {
        let batch = build_string_batch(&[
            ("name", vec![Some("Alice"), Some("Bob")]),
        ]);
        let result = to_json(&[batch]);
        assert!(result.is_ok());

        let json_str = String::from_utf8(result.unwrap()).unwrap();
        assert!(json_str.contains("Alice"));
        assert!(json_str.contains("Bob"));
    }

    #[test]
    fn test_to_json_empty_batches() {
        let result = to_json(&[]);
        assert!(matches!(result, Err(ExportError::NoData)));
    }

    #[test]
    fn test_to_json_mixed_types() {
        let batch = build_mixed_batch(
            &[("name", vec![Some("Test")])],
            &[("count", vec![Some(42)])],
            &[("rate", vec![Some(3.14)])],
        );
        let result = to_json(&[batch]);
        assert!(result.is_ok());

        let json_str = String::from_utf8(result.unwrap()).unwrap();
        assert!(json_str.contains("Test"));
        assert!(json_str.contains("42"));
    }

    // ============ to_parquet tests ============

    #[test]
    fn test_to_parquet_success() {
        let batch = build_int64_batch(&[("id", vec![Some(1), Some(2), Some(3)])]);
        let result = to_parquet(&[batch]);
        assert!(result.is_ok());

        let data = result.unwrap();
        // Parquet files start with "PAR1" magic bytes
        assert!(data.len() >= 4);
        assert_eq!(&data[0..4], b"PAR1");
    }

    #[test]
    fn test_to_parquet_empty_batches() {
        let result = to_parquet(&[]);
        assert!(matches!(result, Err(ExportError::NoData)));
    }

    #[test]
    fn test_to_parquet_string_data() {
        let batch = build_string_batch(&[
            ("name", vec![Some("Alice"), Some("Bob"), Some("Charlie")]),
        ]);
        let result = to_parquet(&[batch]);
        assert!(result.is_ok());

        let data = result.unwrap();
        assert!(data.len() > 10);
        assert_eq!(&data[0..4], b"PAR1");
    }

    // ============ Multiple batches tests ============

    #[test]
    fn test_to_csv_multiple_batches() {
        let batch1 = build_int64_batch(&[("id", vec![Some(1), Some(2)])]);
        let batch2 = build_int64_batch(&[("id", vec![Some(3), Some(4)])]);
        let result = to_csv(&[batch1, batch2]);
        assert!(result.is_ok());

        let csv_str = String::from_utf8(result.unwrap()).unwrap();
        assert!(csv_str.contains("1"));
        assert!(csv_str.contains("4"));
    }

    #[test]
    fn test_to_json_multiple_batches() {
        let batch1 = build_string_batch(&[("name", vec![Some("A")])]);
        let batch2 = build_string_batch(&[("name", vec![Some("B")])]);
        let result = to_json(&[batch1, batch2]);
        assert!(result.is_ok());

        let json_str = String::from_utf8(result.unwrap()).unwrap();
        assert!(json_str.contains("A"));
        assert!(json_str.contains("B"));
    }
}
