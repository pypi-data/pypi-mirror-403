"""MangleFrames - DataFrame viewer via Spark Connect.

This package provides utilities for viewing DataFrames through the MangleFrames
web UI. Uses a fast Rust Spark Connect proxy for Databricks authentication.

Usage:
    from mangleframes import SparkSession, register, show

    # Create SparkSession via Rust proxy
    spark = SparkSession.serverless().getOrCreate()

    # Work with DataFrames using full PySpark API
    df = spark.table("my_catalog.my_schema.my_table")
    gold = df.filter(df.amount > 100).groupBy("category").agg({"amount": "sum"})

    # Register for viewing
    register("gold_table", gold)

    # Launch the viewer
    show()
"""
from __future__ import annotations

import atexit
import os
import subprocess
from typing import TYPE_CHECKING

from .launcher import find_viewer_binary
from .session import SparkSession, get_proxy_port, get_spark_session

if TYPE_CHECKING:
    from pyspark.sql import DataFrame

__version__ = "0.3.4"

# Import alert classes for convenience (optional dependency)
try:
    from .alerts import (
        AlertGenerator,
        ThresholdAlert,
        NullRateAlert,
        RowCountAlert,
        DataFreshnessAlert,
        DuplicateKeysAlert,
        ReconciliationAlert,
        threshold_alert,
        null_rate_alert,
        row_count_alert,
        data_freshness_alert,
        duplicate_keys_alert,
        reconciliation_alert,
    )
    __all__ = [
        "SparkSession", "register", "show", "cleanup",
        "AlertGenerator",
        "ThresholdAlert", "NullRateAlert", "RowCountAlert",
        "DataFreshnessAlert", "DuplicateKeysAlert", "ReconciliationAlert",
        "threshold_alert", "null_rate_alert", "row_count_alert",
        "data_freshness_alert", "duplicate_keys_alert", "reconciliation_alert",
    ]
except ImportError:
    # Alerts module requires requests, which may not be installed
    __all__ = ["SparkSession", "register", "show", "cleanup"]

_viewer_process: subprocess.Popen | None = None
_cleanup_registered = False


def cleanup() -> None:
    """Clean up MangleFrames viewer process."""
    global _viewer_process

    if _viewer_process is not None:
        print("[MangleFrames] Stopping viewer...")
        _viewer_process.terminate()
        try:
            _viewer_process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            _viewer_process.kill()
        _viewer_process = None


def register(name: str, df: DataFrame) -> None:
    """Register a DataFrame as a temp view for viewing.

    Args:
        name: Name for the temp view
        df: PySpark DataFrame to register
    """
    df.createOrReplaceTempView(name)
    print(f"[MangleFrames] Created temp view: {name}")


def show(
    port: int = 8765,
    serverless: bool = True,
    cluster_id: str | None = None,
    block: bool = True,
) -> subprocess.Popen | None:
    """Show the MangleFrames viewer.

    If a SparkSession proxy is running, connects through it to share the session.
    Otherwise, requires DATABRICKS_HOST and DATABRICKS_TOKEN environment variables.

    Args:
        port: Port for the web server (default: 8765)
        serverless: Use serverless compute (default: True)
        cluster_id: Databricks cluster ID (required if serverless=False)
        block: If True, block until Ctrl+C

    Returns:
        The viewer subprocess (if block=False)
    """
    global _viewer_process, _cleanup_registered

    if not _cleanup_registered:
        atexit.register(cleanup)
        _cleanup_registered = True

    # Find and launch the viewer binary
    binary = find_viewer_binary()
    if binary is None:
        raise RuntimeError(
            "mangleframes-viewer binary not found. "
            "Install with: cargo install --path viewer"
        )

    cmd = [str(binary), "--port", str(port)]

    # Check if we have a running proxy to connect through
    proxy_port = get_proxy_port()
    if proxy_port is not None:
        # Connect via proxy - this shares the same Spark session
        proxy_url = f"sc://localhost:{proxy_port}"
        cmd.extend(["--proxy-url", proxy_url])
        print(f"[MangleFrames] Connecting viewer via proxy at {proxy_url}")
    else:
        # Direct connection - requires Databricks credentials
        if not os.environ.get("DATABRICKS_HOST"):
            raise RuntimeError("DATABRICKS_HOST environment variable is required")
        if not os.environ.get("DATABRICKS_TOKEN"):
            raise RuntimeError("DATABRICKS_TOKEN environment variable is required")

        if not serverless and not cluster_id:
            cluster_id = os.environ.get("DATABRICKS_CLUSTER_ID")
            if not cluster_id:
                raise RuntimeError(
                    "Either serverless=True or cluster_id must be provided, "
                    "or set DATABRICKS_CLUSTER_ID environment variable"
                )

        if serverless:
            cmd.append("--serverless")
        elif cluster_id:
            cmd.extend(["--databricks-cluster-id", cluster_id])

    env = os.environ.copy()
    env["RUST_LOG"] = env.get("RUST_LOG", "info")

    print(f"[MangleFrames] Launching viewer on port {port}...")

    _viewer_process = subprocess.Popen(
        cmd,
        env=env,
        stdout=None,  # Inherit stdout to see logs
        stderr=None,
    )

    if block:
        try:
            print(f"[MangleFrames] Viewer running at http://localhost:{port}")
            print("[MangleFrames] Press Ctrl+C to stop...")
            _viewer_process.wait()
        except KeyboardInterrupt:
            print("\n[MangleFrames] Stopping viewer...")
            cleanup()
        return None

    return _viewer_process
