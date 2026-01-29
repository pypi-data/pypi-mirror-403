//! Spark Connect Rust client for Apache Spark gRPC protocol.
//!
//! This crate provides a Rust client for connecting to Spark clusters via the
//! Spark Connect gRPC protocol, with specific support for Databricks.

pub mod client;
pub mod error;

#[allow(clippy::all)]
mod proto {
    include!("proto/spark.connect.rs");
}

pub use client::{ColumnSchema, SparkConnectClient};
pub use error::SparkConnectError;

#[cfg(test)]
mod tests {
    use super::proto::{relation, Limit, Relation};
    use prost::Message;

    /// Build a deeply nested Relation with `depth` levels of Limit operations.
    fn build_nested_relation(depth: usize) -> Relation {
        let mut current = Relation {
            common: None,
            rel_type: None,
        };

        for i in 0..depth {
            current = Relation {
                common: None,
                rel_type: Some(relation::RelType::Limit(Box::new(Limit {
                    input: Some(Box::new(current)),
                    limit: i as i32,
                }))),
            };
        }

        current
    }

    /// Verifies the no-recursion-limit feature works by encoding/decoding
    /// a deeply nested protobuf message (150+ levels exceeds old 100 limit).
    #[test]
    fn test_deeply_nested_relation_decodes() {
        let depth = 150;
        let relation = build_nested_relation(depth);

        let encoded = relation.encode_to_vec();
        let decoded = Relation::decode(encoded.as_slice())
            .expect("should decode deeply nested relation without recursion limit");

        // Verify the structure by walking down to confirm depth
        let mut count = 0;
        let mut current = &decoded;
        while let Some(relation::RelType::Limit(limit)) = &current.rel_type {
            count += 1;
            if let Some(input) = &limit.input {
                current = input;
            } else {
                break;
            }
        }

        assert_eq!(count, depth, "decoded relation should have correct nesting depth");
    }
}
