"""SparkSession wrapper that uses Rust Spark Connect proxy."""
from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession as PySparkSession


_proxy_process: subprocess.Popen | None = None
_proxy_port: int | None = None
_spark_session: "PySparkSession | None" = None
_cleanup_registered = False


def get_proxy_port() -> int | None:
    """Get the port of the running proxy, if any."""
    return _proxy_port


def get_spark_session() -> "PySparkSession | None":
    """Get the current SparkSession, if any."""
    return _spark_session


def _find_proxy_binary() -> Path | None:
    """Find the spark-connect-proxy binary."""
    pkg_dir = Path(__file__).parent
    pkg_binary = pkg_dir / "bin" / "spark-connect-proxy"
    if pkg_binary.exists():
        return pkg_binary

    venv_binary = Path(sys.executable).parent / "spark-connect-proxy"
    if venv_binary.exists():
        return venv_binary

    path_binary = shutil.which("spark-connect-proxy")
    if path_binary:
        return Path(path_binary)

    # Development: check cargo target directory
    repo_root = pkg_dir.parent.parent
    dev_binary = repo_root / "target" / "release" / "spark-connect-proxy"
    if dev_binary.exists():
        return dev_binary

    dev_binary_debug = repo_root / "target" / "debug" / "spark-connect-proxy"
    if dev_binary_debug.exists():
        return dev_binary_debug

    return None


def _cleanup_proxy() -> None:
    """Clean up proxy process."""
    global _proxy_process, _proxy_port

    if _proxy_process is not None:
        print("[MangleFrames] Stopping Spark Connect proxy...")
        _proxy_process.terminate()
        try:
            _proxy_process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            _proxy_process.kill()
        _proxy_process = None
        _proxy_port = None


def _start_proxy(serverless: bool, cluster_id: str | None, port: int) -> None:
    """Start the Rust Spark Connect proxy."""
    global _proxy_process, _proxy_port, _cleanup_registered

    if _proxy_process is not None:
        return  # Already running

    if not _cleanup_registered:
        atexit.register(_cleanup_proxy)
        _cleanup_registered = True

    binary = _find_proxy_binary()
    if binary is None:
        raise RuntimeError(
            "spark-connect-proxy binary not found. "
            "Build with: cargo build -p spark-connect-proxy --release"
        )

    cmd = [str(binary), "--port", str(port)]

    if serverless:
        cmd.append("--serverless")
    elif cluster_id:
        cmd.extend(["--cluster-id", cluster_id])

    env = os.environ.copy()
    env["RUST_LOG"] = env.get("RUST_LOG", "info")

    print(f"[MangleFrames] Starting Spark Connect proxy on port {port}...")

    _proxy_process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # Wait for proxy to start
    time.sleep(0.5)
    if _proxy_process.poll() is not None:
        stdout, _ = _proxy_process.communicate()
        raise RuntimeError(f"Proxy failed to start: {stdout.decode()}")

    _proxy_port = port
    print(f"[MangleFrames] Proxy running on sc://localhost:{port}")


class SparkSessionBuilder:
    """Builder for SparkSession with Rust proxy backend."""

    def __init__(self, serverless: bool = False, cluster_id: str | None = None):
        self._serverless = serverless
        self._cluster_id = cluster_id
        self._port = 15002

    def port(self, port: int) -> "SparkSessionBuilder":
        """Set the proxy port."""
        self._port = port
        return self

    def getOrCreate(self) -> "PySparkSession":
        """Start proxy and return PySpark session connected to it."""
        global _spark_session
        from pyspark.sql import SparkSession as PySparkSession

        # Start the Rust proxy
        _start_proxy(self._serverless, self._cluster_id, self._port)

        # Create and store PySpark session connected to proxy
        _spark_session = (
            PySparkSession.builder.remote(f"sc://localhost:{self._port}").getOrCreate()
        )
        return _spark_session


class SparkSession:
    """SparkSession factory using Rust Spark Connect proxy.

    Usage:
        spark = SparkSession.serverless().getOrCreate()
        # OR
        spark = SparkSession.cluster(cluster_id="...").getOrCreate()
    """

    @classmethod
    def serverless(cls) -> SparkSessionBuilder:
        """Create session builder for serverless compute."""
        return SparkSessionBuilder(serverless=True)

    @classmethod
    def cluster(cls, cluster_id: str) -> SparkSessionBuilder:
        """Create session builder for cluster compute."""
        return SparkSessionBuilder(cluster_id=cluster_id)
