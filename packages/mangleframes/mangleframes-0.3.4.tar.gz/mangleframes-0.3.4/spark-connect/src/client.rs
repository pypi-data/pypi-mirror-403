//! Spark Connect gRPC client implementation.

use std::sync::Arc;
use std::time::Instant;

use arrow::record_batch::RecordBatch;
use arrow_ipc::reader::StreamReader;
use arrow_ipc::writer::StreamWriter;
use tonic::metadata::MetadataValue;
use tonic::service::Interceptor;
use tonic::transport::{Channel, ClientTlsConfig};
use tonic::{Request, Status};
use tracing::info;
use uuid::Uuid;

use crate::error::SparkConnectError;
use crate::proto::spark_connect_service_client::SparkConnectServiceClient;
use crate::proto::{
    ExecutePlanRequest, Plan, Relation, Sql, UserContext,
    execute_plan_response::ResponseType,
};

/// Interceptor that adds Databricks authentication headers.
#[derive(Clone)]
struct AuthInterceptor {
    token: Arc<String>,
    cluster_id: Option<Arc<String>>,
    session_id: Arc<String>,
}

impl Interceptor for AuthInterceptor {
    fn call(&mut self, mut req: Request<()>) -> Result<Request<()>, Status> {
        let auth_value = format!("Bearer {}", self.token);
        req.metadata_mut().insert(
            "authorization",
            MetadataValue::try_from(&auth_value)
                .map_err(|e| Status::internal(format!("Invalid auth header: {}", e)))?,
        );

        // Add compute mode header based on mode
        if let Some(ref cluster_id) = self.cluster_id {
            // Cluster mode: add cluster ID header
            req.metadata_mut().insert(
                "x-databricks-cluster-id",
                MetadataValue::try_from(cluster_id.as_str())
                    .map_err(|e| Status::internal(format!("Invalid cluster header: {}", e)))?,
            );
        } else {
            // Serverless mode: add session ID header
            req.metadata_mut().insert(
                "x-databricks-session-id",
                MetadataValue::try_from(self.session_id.as_str())
                    .map_err(|e| Status::internal(format!("Invalid session header: {}", e)))?,
            );
        }
        Ok(req)
    }
}

/// Schema information for a table column.
#[derive(Debug, Clone)]
pub struct ColumnSchema {
    pub name: String,
    pub data_type: String,
    pub nullable: bool,
}

/// No-op interceptor for proxy connections (proxy handles auth).
#[derive(Clone)]
struct NoOpInterceptor;

impl Interceptor for NoOpInterceptor {
    fn call(&mut self, req: Request<()>) -> Result<Request<()>, Status> {
        Ok(req)
    }
}

/// Inner client type that supports both direct and proxy connections.
enum ClientInner {
    Direct(SparkConnectServiceClient<tonic::service::interceptor::InterceptedService<Channel, AuthInterceptor>>),
    Proxy(SparkConnectServiceClient<tonic::service::interceptor::InterceptedService<Channel, NoOpInterceptor>>),
}

impl Clone for ClientInner {
    fn clone(&self) -> Self {
        match self {
            ClientInner::Direct(c) => ClientInner::Direct(c.clone()),
            ClientInner::Proxy(c) => ClientInner::Proxy(c.clone()),
        }
    }
}

/// Client for Spark Connect gRPC protocol.
pub struct SparkConnectClient {
    inner: ClientInner,
    session_id: String,
}

impl SparkConnectClient {
    /// Connect to a Databricks Spark Connect endpoint.
    ///
    /// # Arguments
    /// * `host` - Databricks workspace host (e.g., "dbc-xxx.cloud.databricks.com")
    /// * `token` - Databricks personal access token
    /// * `cluster_id` - Databricks cluster ID (None for serverless compute)
    pub async fn connect(
        host: &str,
        token: &str,
        cluster_id: Option<&str>,
    ) -> Result<Self, SparkConnectError> {
        let mode = if cluster_id.is_some() { "cluster" } else { "serverless" };

        // Strip protocol prefix if present
        let host = host
            .trim_start_matches("https://")
            .trim_start_matches("http://");

        info!("Connecting to Databricks at {} ({} mode)...", host, mode);

        let endpoint = format!("https://{}:443", host);
        let tls_config = ClientTlsConfig::new().with_native_roots();

        let channel = Channel::from_shared(endpoint)
            .map_err(|e| SparkConnectError::Config(e.to_string()))?
            .tls_config(tls_config)?
            .connect()
            .await?;

        // Generate session_id before creating interceptor (shared between interceptor and client)
        let session_id = Arc::new(Uuid::new_v4().to_string());

        let interceptor = AuthInterceptor {
            token: Arc::new(token.to_string()),
            cluster_id: cluster_id.map(|id| Arc::new(id.to_string())),
            session_id: session_id.clone(),
        };

        let client = SparkConnectServiceClient::with_interceptor(channel, interceptor)
            .max_decoding_message_size(256 * 1024 * 1024); // 256 MB

        info!("Connected to Databricks ({}), session_id: {}", mode, session_id);

        Ok(Self {
            inner: ClientInner::Direct(client),
            session_id: (*session_id).clone(),
        })
    }

    /// Connect via a local Spark Connect proxy.
    ///
    /// The proxy handles authentication, so no token is needed.
    ///
    /// # Arguments
    /// * `proxy_url` - Proxy URL (e.g., "sc://localhost:15002" or "http://localhost:15002")
    pub async fn connect_via_proxy(proxy_url: &str) -> Result<Self, SparkConnectError> {
        // Parse proxy URL - support sc:// and http:// schemes
        let url = proxy_url
            .trim_start_matches("sc://")
            .trim_start_matches("http://")
            .trim_start_matches("https://");

        info!("Connecting to Spark Connect proxy at {}...", url);

        let endpoint = format!("http://{}", url);

        let channel = Channel::from_shared(endpoint)
            .map_err(|e| SparkConnectError::Config(e.to_string()))?
            .connect()
            .await?;

        // Generate UUID session_id - the proxy will rewrite it to share sessions
        let session_id = Uuid::new_v4().to_string();

        let client = SparkConnectServiceClient::with_interceptor(channel, NoOpInterceptor)
            .max_decoding_message_size(256 * 1024 * 1024); // 256 MB

        info!("Connected to proxy at {}, session_id: {}", url, session_id);

        Ok(Self {
            inner: ClientInner::Proxy(client),
            session_id,
        })
    }

    /// Execute a SQL query and return Arrow record batches.
    pub async fn sql(&self, query: &str) -> Result<Vec<RecordBatch>, SparkConnectError> {
        self.sql_limit(query, u32::MAX).await
    }

    /// Execute a SQL query with a row limit and return Arrow record batches.
    pub async fn sql_limit(
        &self,
        query: &str,
        limit: u32,
    ) -> Result<Vec<RecordBatch>, SparkConnectError> {
        let start = Instant::now();
        info!("Executing SQL via Spark Connect: {}", query);

        // Build SQL relation with limit
        let sql_relation = Relation {
            common: None,
            rel_type: Some(crate::proto::relation::RelType::Sql(Sql {
                query: query.to_string(),
                args: Default::default(),
                pos_args: vec![],
                named_arguments: Default::default(),
                pos_arguments: vec![],
            })),
        };

        // Wrap with limit if specified
        let relation = if limit < u32::MAX {
            Relation {
                common: None,
                rel_type: Some(crate::proto::relation::RelType::Limit(Box::new(
                    crate::proto::Limit {
                        input: Some(Box::new(sql_relation)),
                        limit: limit as i32,
                    },
                ))),
            }
        } else {
            sql_relation
        };

        let plan = Plan {
            op_type: Some(crate::proto::plan::OpType::Root(relation)),
        };

        let request = ExecutePlanRequest {
            session_id: self.session_id.clone(),
            user_context: Some(UserContext {
                user_id: "spark-connect-rs".to_string(),
                user_name: "spark-connect-rs".to_string(),
                extensions: vec![],
            }),
            operation_id: Some(Uuid::new_v4().to_string()),
            plan: Some(plan),
            client_type: Some("spark-connect-rs".to_string()),
            request_options: vec![],
            tags: vec![],
            client_observed_server_side_session_id: None,
        };

        let response = match &self.inner {
            ClientInner::Direct(c) => c.clone().execute_plan(request).await?,
            ClientInner::Proxy(c) => c.clone().execute_plan(request).await?,
        };
        let mut stream = response.into_inner();

        let mut batches = Vec::new();
        let mut arrow_data = Vec::new();

        while let Some(resp) = stream.message().await? {
            if let Some(response_type) = resp.response_type {
                if let ResponseType::ArrowBatch(batch) = response_type {
                    arrow_data.extend_from_slice(&batch.data);
                }
            }
        }

        if !arrow_data.is_empty() {
            batches = parse_arrow_ipc(&arrow_data)?;
        }

        let elapsed_ms = start.elapsed().as_millis();
        let row_count: usize = batches.iter().map(|b| b.num_rows()).sum();
        info!(
            "SQL executed in {}ms, {} rows returned",
            elapsed_ms, row_count
        );

        if batches.is_empty() {
            return Err(SparkConnectError::NoData);
        }

        Ok(batches)
    }

    /// Execute SQL and return a single row as JSON Value.
    pub async fn sql_single_row(
        &self,
        query: &str,
    ) -> Result<serde_json::Value, SparkConnectError> {
        let batches = self.sql_limit(query, 1).await?;
        if batches.is_empty() || batches[0].num_rows() == 0 {
            return Ok(serde_json::json!({}));
        }

        let batch = &batches[0];
        let schema = batch.schema();
        let mut row = serde_json::Map::new();

        for (col_idx, field) in schema.fields().iter().enumerate() {
            let col = batch.column(col_idx);
            let value = extract_json_value(col.as_ref(), 0);
            row.insert(field.name().clone(), value);
        }

        Ok(serde_json::Value::Object(row))
    }

    /// Get schema for a table via DESCRIBE TABLE.
    pub async fn get_schema(
        &self,
        table: &str,
    ) -> Result<Vec<ColumnSchema>, SparkConnectError> {
        let query = format!("DESCRIBE TABLE `{}`", table.replace('`', "``"));
        info!("Getting schema for table: {}", table);

        let batches = self.sql(&query).await?;
        let mut columns = Vec::new();

        for batch in &batches {
            let schema = batch.schema();
            let name_idx = schema.index_of("col_name").unwrap_or(0);
            let type_idx = schema.index_of("data_type").unwrap_or(1);

            let name_col = batch.column(name_idx);
            let type_col = batch.column(type_idx);

            for row in 0..batch.num_rows() {
                let name = extract_string(name_col.as_ref(), row);
                let data_type = extract_string(type_col.as_ref(), row);

                // Skip partition/metadata rows
                if name.starts_with('#') || name.is_empty() {
                    continue;
                }

                columns.push(ColumnSchema {
                    name,
                    data_type,
                    nullable: true, // Default to nullable
                });
            }
        }

        info!("Schema for {}: {} columns", table, columns.len());
        Ok(columns)
    }

    /// List all tables/views in the current catalog.
    pub async fn list_tables(&self) -> Result<Vec<String>, SparkConnectError> {
        info!("Listing tables via SHOW TABLES");
        let batches = self.sql("SHOW TABLES").await?;
        let mut tables = Vec::new();

        for batch in &batches {
            let schema = batch.schema();
            // Look for tableName or table_name column
            let name_idx = schema.index_of("tableName")
                .or_else(|_| schema.index_of("table_name"))
                .unwrap_or(1);

            let name_col = batch.column(name_idx);
            for row in 0..batch.num_rows() {
                let name = extract_string(name_col.as_ref(), row);
                if !name.is_empty() {
                    tables.push(name);
                }
            }
        }

        info!("Found {} tables", tables.len());
        Ok(tables)
    }

    /// Register Arrow record batches as a temporary view in Spark.
    pub async fn create_temp_view(
        &self,
        view_name: &str,
        batches: &[RecordBatch],
    ) -> Result<(), SparkConnectError> {
        if batches.is_empty() {
            return Err(SparkConnectError::Config("No batches to register".to_string()));
        }

        info!("Registering temp view '{}' with {} batches", view_name, batches.len());

        // Serialize batches to Arrow IPC streaming format
        let ipc_data = serialize_batches_to_ipc(batches)?;
        info!("Serialized {} bytes of Arrow IPC data", ipc_data.len());

        // Create LocalRelation with the IPC data
        let local_relation = Relation {
            common: None,
            rel_type: Some(crate::proto::relation::RelType::LocalRelation(
                crate::proto::LocalRelation {
                    data: Some(ipc_data),
                    schema: None,
                },
            )),
        };

        // Create the temp view command
        let command = crate::proto::Command {
            command_type: Some(crate::proto::command::CommandType::CreateDataframeView(
                crate::proto::CreateDataFrameViewCommand {
                    input: Some(local_relation),
                    name: view_name.to_string(),
                    is_global: false,
                    replace: true,
                },
            )),
        };

        self.execute_command(command).await?;
        info!("Successfully registered temp view '{}'", view_name);
        Ok(())
    }

    /// Execute a Spark Connect command (non-query operation).
    async fn execute_command(
        &self,
        command: crate::proto::Command,
    ) -> Result<(), SparkConnectError> {
        let plan = Plan {
            op_type: Some(crate::proto::plan::OpType::Command(command)),
        };

        let request = ExecutePlanRequest {
            session_id: self.session_id.clone(),
            user_context: Some(UserContext {
                user_id: "spark-connect-rs".to_string(),
                user_name: "spark-connect-rs".to_string(),
                extensions: vec![],
            }),
            operation_id: Some(Uuid::new_v4().to_string()),
            plan: Some(plan),
            client_type: Some("spark-connect-rs".to_string()),
            request_options: vec![],
            tags: vec![],
            client_observed_server_side_session_id: None,
        };

        let response = match &self.inner {
            ClientInner::Direct(c) => c.clone().execute_plan(request).await?,
            ClientInner::Proxy(c) => c.clone().execute_plan(request).await?,
        };

        // Drain the response stream
        let mut stream = response.into_inner();
        while stream.message().await?.is_some() {}

        Ok(())
    }
}

/// Serialize Arrow RecordBatches to IPC streaming format.
fn serialize_batches_to_ipc(batches: &[RecordBatch]) -> Result<Vec<u8>, SparkConnectError> {
    let schema = batches[0].schema();
    let mut ipc_data = Vec::new();

    {
        let mut writer = StreamWriter::try_new(&mut ipc_data, &schema)?;
        for batch in batches {
            writer.write(batch)?;
        }
        writer.finish()?;
    }

    Ok(ipc_data)
}

/// Extract a JSON value from an Arrow array at a specific index.
fn extract_json_value(array: &dyn arrow::array::Array, index: usize) -> serde_json::Value {
    use arrow::array::Array;
    use arrow::datatypes::DataType;

    if array.is_null(index) {
        return serde_json::Value::Null;
    }

    match array.data_type() {
        DataType::Int8 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Int8Array>().unwrap();
            serde_json::json!(arr.value(index))
        }
        DataType::Int16 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Int16Array>().unwrap();
            serde_json::json!(arr.value(index))
        }
        DataType::Int32 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Int32Array>().unwrap();
            serde_json::json!(arr.value(index))
        }
        DataType::Int64 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Int64Array>().unwrap();
            serde_json::json!(arr.value(index))
        }
        DataType::Float32 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Float32Array>().unwrap();
            serde_json::json!(arr.value(index))
        }
        DataType::Float64 => {
            let arr = array.as_any().downcast_ref::<arrow::array::Float64Array>().unwrap();
            serde_json::json!(arr.value(index))
        }
        DataType::Boolean => {
            let arr = array.as_any().downcast_ref::<arrow::array::BooleanArray>().unwrap();
            serde_json::json!(arr.value(index))
        }
        DataType::Utf8 => {
            let arr = array.as_any().downcast_ref::<arrow::array::StringArray>().unwrap();
            serde_json::json!(arr.value(index))
        }
        DataType::LargeUtf8 => {
            let arr = array.as_any().downcast_ref::<arrow::array::LargeStringArray>().unwrap();
            serde_json::json!(arr.value(index))
        }
        _ => serde_json::json!(format!("{:?}", array.data_type()))
    }
}

/// Extract a string value from an Arrow array.
fn extract_string(array: &dyn arrow::array::Array, index: usize) -> String {
    use arrow::array::Array;
    use arrow::datatypes::DataType;

    if array.is_null(index) {
        return String::new();
    }

    match array.data_type() {
        DataType::Utf8 => {
            let arr = array.as_any().downcast_ref::<arrow::array::StringArray>().unwrap();
            arr.value(index).to_string()
        }
        DataType::LargeUtf8 => {
            let arr = array.as_any().downcast_ref::<arrow::array::LargeStringArray>().unwrap();
            arr.value(index).to_string()
        }
        _ => String::new()
    }
}

/// Parse Arrow IPC data into record batches.
fn parse_arrow_ipc(data: &[u8]) -> Result<Vec<RecordBatch>, SparkConnectError> {
    let cursor = std::io::Cursor::new(data);
    let reader = StreamReader::try_new(cursor, None)?;

    let batches: Result<Vec<_>, _> = reader.collect();
    Ok(batches?)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    #[ignore] // Requires Databricks credentials
    async fn test_sql_execution_cluster() {
        let host = std::env::var("DATABRICKS_HOST").unwrap();
        let token = std::env::var("DATABRICKS_TOKEN").unwrap();
        let cluster_id = std::env::var("DATABRICKS_CLUSTER_ID").unwrap();

        let client = SparkConnectClient::connect(&host, &token, Some(&cluster_id))
            .await
            .unwrap();

        let batches = client.sql("SELECT 1 as test_col").await.unwrap();
        assert!(!batches.is_empty());
    }

    #[tokio::test]
    #[ignore] // Requires Databricks credentials with serverless enabled
    async fn test_sql_execution_serverless() {
        let host = std::env::var("DATABRICKS_HOST").unwrap();
        let token = std::env::var("DATABRICKS_TOKEN").unwrap();

        let client = SparkConnectClient::connect(&host, &token, None)
            .await
            .unwrap();

        let batches = client.sql("SELECT 1 as test_col").await.unwrap();
        assert!(!batches.is_empty());
    }
}
