//! Build script to fetch and compile Spark Connect proto files.

use std::fs;
use std::path::Path;

const SPARK_VERSION: &str = "v4.0.0";
const PROTO_BASE_URL: &str = "https://raw.githubusercontent.com/apache/spark";

const PROTO_FILES: &[&str] = &[
    "base.proto",
    "commands.proto",
    "relations.proto",
    "expressions.proto",
    "types.proto",
    "common.proto",
    "catalog.proto",
    "ml.proto",
    "ml_common.proto",
];

fn main() {
    let proto_dir = Path::new("proto/spark/connect");
    fs::create_dir_all(proto_dir).expect("Failed to create proto directory");
    fs::create_dir_all("src/proto").expect("Failed to create src/proto directory");

    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=proto");

    // Fetch proto files if not present
    for proto in PROTO_FILES {
        let proto_path = proto_dir.join(proto);
        if !proto_path.exists() {
            fetch_proto(proto, &proto_path);
        }
        println!("cargo:rerun-if-changed={}", proto_path.display());
    }

    // Get protoc include path from environment or use default
    let home = std::env::var("HOME").unwrap_or_else(|_| "/home".to_string());
    let protoc_include = format!("{}/.local/include", home);

    // Build main proto file - tonic-build will resolve imports
    tonic_build::configure()
        .build_server(false)
        .out_dir("src/proto")
        .compile_protos(
            &["proto/spark/connect/base.proto"],
            &["proto", &protoc_include],
        )
        .expect("Failed to compile proto files");
}

fn fetch_proto(name: &str, path: &Path) {
    let url = format!(
        "{}/{}/sql/connect/common/src/main/protobuf/spark/connect/{}",
        PROTO_BASE_URL, SPARK_VERSION, name
    );

    println!("cargo:warning=Fetching proto: {}", url);

    let response = reqwest::blocking::get(&url)
        .unwrap_or_else(|e| panic!("Failed to fetch {}: {}", name, e));

    if !response.status().is_success() {
        panic!("Failed to fetch {}: HTTP {}", name, response.status());
    }

    let content = response.text().expect("Failed to read response");
    fs::write(path, content).unwrap_or_else(|e| panic!("Failed to write {}: {}", name, e));

    println!("cargo:warning=Downloaded {}", name);
}
