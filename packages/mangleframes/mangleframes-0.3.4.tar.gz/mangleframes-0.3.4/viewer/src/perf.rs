//! Performance metrics collection and aggregation.

use std::collections::{HashMap, VecDeque};
use std::time::Instant;

use serde::Serialize;
use tokio::sync::RwLock;

const MAX_SAMPLES_PER_FRAME: usize = 1000;

#[derive(Clone)]
pub struct TimingSample {
    pub timestamp: Instant,
    pub rows: usize,
    pub bytes: usize,
    pub spark_ms: u64,
    pub ipc_ms: u64,
    pub socket_ms: u64,
    pub parse_ms: u64,
    pub json_ms: u64,
    pub total_ms: u64,
    pub cached: bool,
}

#[derive(Serialize)]
pub struct FrameMetrics {
    pub sample_count: usize,
    pub rows_per_sec: f64,
    pub bytes_per_sec: f64,
    pub latency_p50_ms: u64,
    pub latency_p95_ms: u64,
    pub latency_p99_ms: u64,
    pub avg_spark_ms: f64,
    pub avg_ipc_ms: f64,
    pub avg_socket_ms: f64,
    pub avg_parse_ms: f64,
    pub avg_json_ms: f64,
    pub cache_hit_rate: f64,
}

#[derive(Serialize)]
pub struct GlobalMetrics {
    pub total_requests: usize,
    pub uptime_seconds: u64,
}

pub struct PerfCollector {
    samples: RwLock<HashMap<String, VecDeque<TimingSample>>>,
    start_time: Instant,
    total_requests: RwLock<usize>,
}

impl PerfCollector {
    pub fn new() -> Self {
        Self {
            samples: RwLock::new(HashMap::new()),
            start_time: Instant::now(),
            total_requests: RwLock::new(0),
        }
    }

    pub async fn record(&self, frame_name: &str, sample: TimingSample) {
        let mut samples = self.samples.write().await;
        let frame_samples = samples.entry(frame_name.to_string()).or_default();

        if frame_samples.len() >= MAX_SAMPLES_PER_FRAME {
            frame_samples.pop_front();
        }
        frame_samples.push_back(sample);

        let mut total = self.total_requests.write().await;
        *total += 1;
    }

    pub async fn get_frame_metrics(&self, frame_name: &str) -> Option<FrameMetrics> {
        let samples = self.samples.read().await;
        let frame_samples = samples.get(frame_name)?;

        if frame_samples.is_empty() {
            return None;
        }

        Some(compute_metrics(frame_samples))
    }

    pub async fn get_all_metrics(&self) -> HashMap<String, FrameMetrics> {
        let samples = self.samples.read().await;
        samples
            .iter()
            .filter_map(|(name, s)| {
                if s.is_empty() {
                    None
                } else {
                    Some((name.clone(), compute_metrics(s)))
                }
            })
            .collect()
    }

    pub async fn get_global_metrics(&self) -> GlobalMetrics {
        let total = *self.total_requests.read().await;
        GlobalMetrics {
            total_requests: total,
            uptime_seconds: self.start_time.elapsed().as_secs(),
        }
    }

    pub async fn clear(&self) {
        self.samples.write().await.clear();
        *self.total_requests.write().await = 0;
    }
}

fn compute_metrics(samples: &VecDeque<TimingSample>) -> FrameMetrics {
    let count = samples.len();
    let non_cached: Vec<_> = samples.iter().filter(|s| !s.cached).collect();
    let cached_count = count - non_cached.len();

    // Compute averages from non-cached samples
    let (avg_spark, avg_ipc, avg_socket, avg_parse, avg_json) = if non_cached.is_empty() {
        (0.0, 0.0, 0.0, 0.0, 0.0)
    } else {
        let n = non_cached.len() as f64;
        (
            non_cached.iter().map(|s| s.spark_ms as f64).sum::<f64>() / n,
            non_cached.iter().map(|s| s.ipc_ms as f64).sum::<f64>() / n,
            non_cached.iter().map(|s| s.socket_ms as f64).sum::<f64>() / n,
            non_cached.iter().map(|s| s.parse_ms as f64).sum::<f64>() / n,
            non_cached.iter().map(|s| s.json_ms as f64).sum::<f64>() / n,
        )
    };

    // Compute latency percentiles from all samples
    let mut latencies: Vec<u64> = samples.iter().map(|s| s.total_ms).collect();
    latencies.sort_unstable();

    let p50 = percentile(&latencies, 50);
    let p95 = percentile(&latencies, 95);
    let p99 = percentile(&latencies, 99);

    // Compute throughput from non-cached samples
    let (rows_per_sec, bytes_per_sec) = if non_cached.is_empty() {
        (0.0, 0.0)
    } else {
        let total_rows: usize = non_cached.iter().map(|s| s.rows).sum();
        let total_bytes: usize = non_cached.iter().map(|s| s.bytes).sum();
        let total_ms: u64 = non_cached.iter().map(|s| s.total_ms).sum();
        let total_secs = total_ms as f64 / 1000.0;
        if total_secs > 0.0 {
            (total_rows as f64 / total_secs, total_bytes as f64 / total_secs)
        } else {
            (0.0, 0.0)
        }
    };

    FrameMetrics {
        sample_count: count,
        rows_per_sec,
        bytes_per_sec,
        latency_p50_ms: p50,
        latency_p95_ms: p95,
        latency_p99_ms: p99,
        avg_spark_ms: avg_spark,
        avg_ipc_ms: avg_ipc,
        avg_socket_ms: avg_socket,
        avg_parse_ms: avg_parse,
        avg_json_ms: avg_json,
        cache_hit_rate: cached_count as f64 / count as f64,
    }
}

fn percentile(sorted: &[u64], p: usize) -> u64 {
    if sorted.is_empty() {
        return 0;
    }
    let idx = (p * sorted.len() / 100).min(sorted.len() - 1);
    sorted[idx]
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::VecDeque;

    fn create_sample(total_ms: u64, rows: usize, cached: bool) -> TimingSample {
        TimingSample {
            timestamp: Instant::now(),
            rows,
            bytes: rows * 100,
            spark_ms: total_ms / 2,
            ipc_ms: total_ms / 10,
            socket_ms: total_ms / 10,
            parse_ms: total_ms / 10,
            json_ms: total_ms / 10,
            total_ms,
            cached,
        }
    }

    // ============ percentile tests ============

    #[test]
    fn test_percentile_empty() {
        assert_eq!(percentile(&[], 50), 0);
    }

    #[test]
    fn test_percentile_single_element() {
        assert_eq!(percentile(&[100], 50), 100);
        assert_eq!(percentile(&[100], 99), 100);
    }

    #[test]
    fn test_percentile_p50() {
        let sorted = vec![10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
        let p50 = percentile(&sorted, 50);
        assert!(p50 >= 50 && p50 <= 60);
    }

    #[test]
    fn test_percentile_p95() {
        let sorted: Vec<u64> = (1..=100).collect();
        let p95 = percentile(&sorted, 95);
        assert!(p95 >= 95);
    }

    #[test]
    fn test_percentile_p99() {
        let sorted: Vec<u64> = (1..=100).collect();
        let p99 = percentile(&sorted, 99);
        assert!(p99 >= 99);
    }

    // ============ compute_metrics tests ============

    #[test]
    fn test_compute_metrics_single_sample() {
        let mut samples = VecDeque::new();
        samples.push_back(create_sample(100, 1000, false));

        let metrics = compute_metrics(&samples);
        assert_eq!(metrics.sample_count, 1);
        assert_eq!(metrics.latency_p50_ms, 100);
        assert!((metrics.cache_hit_rate - 0.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_compute_metrics_cache_hit_rate() {
        let mut samples = VecDeque::new();
        samples.push_back(create_sample(100, 1000, false));
        samples.push_back(create_sample(50, 1000, true));
        samples.push_back(create_sample(60, 1000, true));
        samples.push_back(create_sample(110, 1000, false));

        let metrics = compute_metrics(&samples);
        assert_eq!(metrics.sample_count, 4);
        assert!((metrics.cache_hit_rate - 0.5).abs() < f64::EPSILON);
    }

    #[test]
    fn test_compute_metrics_all_cached() {
        let mut samples = VecDeque::new();
        samples.push_back(create_sample(10, 100, true));
        samples.push_back(create_sample(20, 100, true));

        let metrics = compute_metrics(&samples);
        assert!((metrics.cache_hit_rate - 1.0).abs() < f64::EPSILON);
        // Throughput should be 0 when all cached
        assert!((metrics.rows_per_sec - 0.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_compute_metrics_throughput() {
        let mut samples = VecDeque::new();
        // 1000 rows in 100ms = 10000 rows/sec
        samples.push_back(create_sample(100, 1000, false));

        let metrics = compute_metrics(&samples);
        assert!(metrics.rows_per_sec > 0.0);
        assert!(metrics.bytes_per_sec > 0.0);
    }

    #[test]
    fn test_compute_metrics_latency_percentiles() {
        let mut samples = VecDeque::new();
        for i in 1..=100 {
            samples.push_back(create_sample(i as u64, 100, false));
        }

        let metrics = compute_metrics(&samples);
        // p50 should be around 50
        assert!(metrics.latency_p50_ms >= 45 && metrics.latency_p50_ms <= 55);
        // p95 should be around 95
        assert!(metrics.latency_p95_ms >= 90 && metrics.latency_p95_ms <= 100);
        // p99 should be around 99
        assert!(metrics.latency_p99_ms >= 95 && metrics.latency_p99_ms <= 100);
    }

    // ============ PerfCollector tests ============

    #[tokio::test]
    async fn test_perf_collector_record() {
        let collector = PerfCollector::new();
        let sample = create_sample(100, 1000, false);

        collector.record("test_frame", sample).await;

        let metrics = collector.get_frame_metrics("test_frame").await;
        assert!(metrics.is_some());
        assert_eq!(metrics.unwrap().sample_count, 1);
    }

    #[tokio::test]
    async fn test_perf_collector_multiple_frames() {
        let collector = PerfCollector::new();

        collector.record("frame1", create_sample(100, 1000, false)).await;
        collector.record("frame2", create_sample(200, 2000, false)).await;
        collector.record("frame1", create_sample(150, 1500, false)).await;

        let all_metrics = collector.get_all_metrics().await;
        assert_eq!(all_metrics.len(), 2);
        assert!(all_metrics.contains_key("frame1"));
        assert!(all_metrics.contains_key("frame2"));
        assert_eq!(all_metrics["frame1"].sample_count, 2);
        assert_eq!(all_metrics["frame2"].sample_count, 1);
    }

    #[tokio::test]
    async fn test_perf_collector_global_metrics() {
        let collector = PerfCollector::new();

        collector.record("frame1", create_sample(100, 1000, false)).await;
        collector.record("frame2", create_sample(200, 2000, false)).await;
        collector.record("frame1", create_sample(150, 1500, false)).await;

        let global = collector.get_global_metrics().await;
        assert_eq!(global.total_requests, 3);
        assert!(global.uptime_seconds >= 0);
    }

    #[tokio::test]
    async fn test_perf_collector_clear() {
        let collector = PerfCollector::new();

        collector.record("frame1", create_sample(100, 1000, false)).await;
        collector.record("frame2", create_sample(200, 2000, false)).await;

        collector.clear().await;

        let all_metrics = collector.get_all_metrics().await;
        assert!(all_metrics.is_empty());

        let global = collector.get_global_metrics().await;
        assert_eq!(global.total_requests, 0);
    }

    #[tokio::test]
    async fn test_perf_collector_nonexistent_frame() {
        let collector = PerfCollector::new();
        let metrics = collector.get_frame_metrics("nonexistent").await;
        assert!(metrics.is_none());
    }

    #[tokio::test]
    async fn test_perf_collector_max_samples() {
        let collector = PerfCollector::new();

        // Add more than MAX_SAMPLES_PER_FRAME (1000) samples
        for i in 0..1100 {
            collector.record("test", create_sample(i as u64, 100, false)).await;
        }

        let metrics = collector.get_frame_metrics("test").await.unwrap();
        // Should be capped at MAX_SAMPLES_PER_FRAME
        assert_eq!(metrics.sample_count, MAX_SAMPLES_PER_FRAME);
    }

    // ============ FrameMetrics serialization tests ============

    #[test]
    fn test_frame_metrics_serialization() {
        let metrics = FrameMetrics {
            sample_count: 10,
            rows_per_sec: 1000.5,
            bytes_per_sec: 50000.0,
            latency_p50_ms: 50,
            latency_p95_ms: 95,
            latency_p99_ms: 99,
            avg_spark_ms: 25.0,
            avg_ipc_ms: 5.0,
            avg_socket_ms: 5.0,
            avg_parse_ms: 5.0,
            avg_json_ms: 5.0,
            cache_hit_rate: 0.3,
        };

        let json = serde_json::to_value(&metrics).unwrap();
        assert_eq!(json["sample_count"], 10);
        assert_eq!(json["latency_p50_ms"], 50);
        assert!((json["cache_hit_rate"].as_f64().unwrap() - 0.3).abs() < f64::EPSILON);
    }

    // ============ GlobalMetrics serialization tests ============

    #[test]
    fn test_global_metrics_serialization() {
        let metrics = GlobalMetrics {
            total_requests: 1000,
            uptime_seconds: 3600,
        };

        let json = serde_json::to_value(&metrics).unwrap();
        assert_eq!(json["total_requests"], 1000);
        assert_eq!(json["uptime_seconds"], 3600);
    }
}
