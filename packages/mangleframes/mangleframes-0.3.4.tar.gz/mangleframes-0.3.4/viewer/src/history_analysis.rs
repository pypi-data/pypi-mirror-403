//! History coverage analysis for multi-frame join scenarios.

use std::collections::HashMap;

use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum HistoryError {
    #[error("Frame not found: {0}")]
    FrameNotFound(String),
    #[error("No frames configured")]
    NoFrames,
    #[error("Key configuration missing for frame: {0}")]
    MissingKeys(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FrameKeyStats {
    pub frame: String,
    pub columns: Vec<String>,
    pub cardinality: usize,
    pub null_count: usize,
    pub total_rows: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FrameTemporalStats {
    pub frame: String,
    pub column: String,
    pub bucket_size: String,
    pub min: Option<String>,
    pub max: Option<String>,
    pub buckets: HashMap<String, usize>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PairwiseOverlap {
    pub frame1: String,
    pub frame2: String,
    pub left_total: usize,
    pub right_total: usize,
    pub left_only: usize,
    pub right_only: usize,
    pub both: usize,
    pub overlap_pct: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimelineBucket {
    pub bucket: String,
    pub frame_counts: HashMap<String, usize>,
    pub all_present: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JoinPrediction {
    pub join_type: String,
    pub estimated_rows: usize,
    pub null_columns: HashMap<String, usize>,
    pub coverage_pct: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DateGap {
    pub start: String,
    pub end: String,
    pub periods: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemporalRangeStats {
    pub frame: String,
    pub column: String,
    pub granularity: String,
    pub min_date: Option<String>,
    pub max_date: Option<String>,
    pub total_rows: usize,
    pub null_dates: usize,
    pub distinct_dates: usize,
    pub internal_gaps: Vec<DateGap>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OverlapZone {
    pub start: String,
    pub end: String,
    pub span: String,
    pub days: i64,
    pub valid: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FrameDataLoss {
    pub frame: String,
    pub rows_before_overlap: usize,
    pub rows_after_overlap: usize,
    pub total_lost: usize,
    pub pct_lost: f64,
    pub range_lost_before: Option<String>,
    pub range_lost_after: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoverageResult {
    pub frames: Vec<String>,
    pub key_stats: Vec<FrameKeyStats>,
    pub temporal_stats: Vec<FrameTemporalStats>,
    pub pairwise_overlaps: Vec<PairwiseOverlap>,
    pub timeline: Vec<TimelineBucket>,
    pub predictions: Vec<JoinPrediction>,
    pub temporal_ranges: Vec<TemporalRangeStats>,
    pub overlap_zone: Option<OverlapZone>,
    pub data_loss: Vec<FrameDataLoss>,
}

pub struct HistoryAnalyzer {
    key_stats: HashMap<String, FrameKeyStats>,
    temporal_stats: HashMap<String, FrameTemporalStats>,
    overlaps: Vec<PairwiseOverlap>,
    temporal_ranges: HashMap<String, TemporalRangeStats>,
    data_loss: HashMap<String, FrameDataLoss>,
}

impl HistoryAnalyzer {
    pub fn new() -> Self {
        Self {
            key_stats: HashMap::new(),
            temporal_stats: HashMap::new(),
            overlaps: Vec::new(),
            temporal_ranges: HashMap::new(),
            data_loss: HashMap::new(),
        }
    }

    pub fn add_key_stats(&mut self, stats: FrameKeyStats) {
        self.key_stats.insert(stats.frame.clone(), stats);
    }

    pub fn add_temporal_stats(&mut self, stats: FrameTemporalStats) {
        self.temporal_stats.insert(stats.frame.clone(), stats);
    }

    pub fn add_overlap(&mut self, overlap: PairwiseOverlap) {
        self.overlaps.push(overlap);
    }

    pub fn add_temporal_range(&mut self, stats: TemporalRangeStats) {
        self.temporal_ranges.insert(stats.frame.clone(), stats);
    }

    pub fn add_data_loss(&mut self, loss: FrameDataLoss) {
        self.data_loss.insert(loss.frame.clone(), loss);
    }

    pub fn compute_coverage(&self, frames: &[String]) -> Result<CoverageResult, HistoryError> {
        if frames.is_empty() {
            return Err(HistoryError::NoFrames);
        }

        let key_stats: Vec<FrameKeyStats> = frames
            .iter()
            .filter_map(|f| self.key_stats.get(f).cloned())
            .collect();

        let temporal_stats: Vec<FrameTemporalStats> = frames
            .iter()
            .filter_map(|f| self.temporal_stats.get(f).cloned())
            .collect();

        let pairwise_overlaps: Vec<PairwiseOverlap> = self
            .overlaps
            .iter()
            .filter(|o| frames.contains(&o.frame1) && frames.contains(&o.frame2))
            .cloned()
            .collect();

        let timeline = self.build_timeline(frames);
        let predictions = self.compute_predictions(frames, &pairwise_overlaps);

        let temporal_ranges: Vec<TemporalRangeStats> = frames
            .iter()
            .filter_map(|f| self.temporal_ranges.get(f).cloned())
            .collect();

        let overlap_zone = self.compute_overlap_zone(&temporal_ranges);

        let data_loss: Vec<FrameDataLoss> = frames
            .iter()
            .filter_map(|f| self.data_loss.get(f).cloned())
            .collect();

        Ok(CoverageResult {
            frames: frames.to_vec(),
            key_stats,
            temporal_stats,
            pairwise_overlaps,
            timeline,
            predictions,
            temporal_ranges,
            overlap_zone,
            data_loss,
        })
    }

    fn compute_overlap_zone(&self, ranges: &[TemporalRangeStats]) -> Option<OverlapZone> {
        if ranges.is_empty() {
            return None;
        }

        let min_dates: Vec<&str> = ranges
            .iter()
            .filter_map(|r| r.min_date.as_deref())
            .collect();

        let max_dates: Vec<&str> = ranges
            .iter()
            .filter_map(|r| r.max_date.as_deref())
            .collect();

        if min_dates.is_empty() || max_dates.is_empty() {
            return None;
        }

        let overlap_start = min_dates.iter().max()?.to_string();
        let overlap_end = max_dates.iter().min()?.to_string();

        if overlap_start > overlap_end {
            return Some(OverlapZone {
                start: overlap_start,
                end: overlap_end,
                span: "No overlap".to_string(),
                days: 0,
                valid: false,
            });
        }

        let days = Self::compute_days_between(&overlap_start, &overlap_end);
        let span = Self::format_date_span(days);

        Some(OverlapZone {
            start: overlap_start,
            end: overlap_end,
            span,
            days,
            valid: true,
        })
    }

    fn compute_days_between(start: &str, end: &str) -> i64 {
        use chrono::NaiveDate;
        let start_date = NaiveDate::parse_from_str(start, "%Y-%m-%d").ok();
        let end_date = NaiveDate::parse_from_str(end, "%Y-%m-%d").ok();
        match (start_date, end_date) {
            (Some(s), Some(e)) => (e - s).num_days(),
            _ => 0,
        }
    }

    fn format_date_span(days: i64) -> String {
        if days < 0 {
            return "No overlap".to_string();
        }
        let years = days / 365;
        let months = (days % 365) / 30;
        let remaining_days = days % 30;

        let mut parts = Vec::new();
        if years > 0 {
            parts.push(format!("{}y", years));
        }
        if months > 0 {
            parts.push(format!("{}m", months));
        }
        if remaining_days > 0 || parts.is_empty() {
            parts.push(format!("{}d", remaining_days));
        }
        parts.join(" ")
    }

    fn build_timeline(&self, frames: &[String]) -> Vec<TimelineBucket> {
        let mut all_buckets: HashMap<String, HashMap<String, usize>> = HashMap::new();

        for frame in frames {
            if let Some(ts) = self.temporal_stats.get(frame) {
                for (bucket, count) in &ts.buckets {
                    all_buckets
                        .entry(bucket.clone())
                        .or_default()
                        .insert(frame.clone(), *count);
                }
            }
        }

        let mut timeline: Vec<TimelineBucket> = all_buckets
            .into_iter()
            .map(|(bucket, frame_counts)| {
                let all_present = frames.iter().all(|f| frame_counts.contains_key(f));
                TimelineBucket { bucket, frame_counts, all_present }
            })
            .collect();

        timeline.sort_by(|a, b| a.bucket.cmp(&b.bucket));
        timeline
    }

    fn compute_predictions(
        &self,
        frames: &[String],
        overlaps: &[PairwiseOverlap],
    ) -> Vec<JoinPrediction> {
        if frames.len() < 2 {
            return vec![];
        }

        let mut predictions = Vec::new();

        // INNER JOIN: bounded by minimum pairwise overlap
        let min_overlap = overlaps.iter().map(|o| o.both).min().unwrap_or(0);
        let max_rows: usize = self.key_stats.values().map(|s| s.total_rows).max().unwrap_or(0);
        let inner_coverage = if max_rows > 0 {
            (min_overlap as f64 / max_rows as f64) * 100.0
        } else {
            0.0
        };

        predictions.push(JoinPrediction {
            join_type: "INNER".to_string(),
            estimated_rows: min_overlap,
            null_columns: HashMap::new(),
            coverage_pct: inner_coverage.min(100.0),
        });

        // LEFT JOIN predictions for each frame as the "left" side
        for frame in frames {
            if let Some(stats) = self.key_stats.get(frame) {
                let mut null_columns: HashMap<String, usize> = HashMap::new();

                for other in frames {
                    if other == frame {
                        continue;
                    }
                    // Find overlap where this frame is involved
                    let overlap = overlaps.iter().find(|o| {
                        (o.frame1 == *frame && o.frame2 == *other)
                            || (o.frame1 == *other && o.frame2 == *frame)
                    });

                    if let Some(o) = overlap {
                        let unmatched = if o.frame1 == *frame {
                            o.left_only
                        } else {
                            o.right_only
                        };
                        null_columns.insert(other.clone(), unmatched);
                    }
                }

                predictions.push(JoinPrediction {
                    join_type: format!("LEFT ({})", frame),
                    estimated_rows: stats.total_rows,
                    null_columns,
                    coverage_pct: 100.0,
                });
            }
        }

        predictions
    }
}

impl Default for HistoryAnalyzer {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_analyzer() {
        let analyzer = HistoryAnalyzer::new();
        let result = analyzer.compute_coverage(&[]);
        assert!(result.is_err());
    }

    #[test]
    fn test_single_frame() {
        let mut analyzer = HistoryAnalyzer::new();
        analyzer.add_key_stats(FrameKeyStats {
            frame: "orders".to_string(),
            columns: vec!["id".to_string()],
            cardinality: 1000,
            null_count: 0,
            total_rows: 1000,
        });

        let result = analyzer.compute_coverage(&["orders".to_string()]).unwrap();
        assert_eq!(result.frames.len(), 1);
        assert_eq!(result.key_stats.len(), 1);
    }

    #[test]
    fn test_pairwise_overlap() {
        let mut analyzer = HistoryAnalyzer::new();

        analyzer.add_key_stats(FrameKeyStats {
            frame: "orders".to_string(),
            columns: vec!["customer_id".to_string()],
            cardinality: 800,
            null_count: 0,
            total_rows: 1000,
        });

        analyzer.add_key_stats(FrameKeyStats {
            frame: "customers".to_string(),
            columns: vec!["id".to_string()],
            cardinality: 1000,
            null_count: 0,
            total_rows: 1000,
        });

        analyzer.add_overlap(PairwiseOverlap {
            frame1: "orders".to_string(),
            frame2: "customers".to_string(),
            left_total: 800,
            right_total: 1000,
            left_only: 50,
            right_only: 250,
            both: 750,
            overlap_pct: 75.0,
        });

        let result = analyzer
            .compute_coverage(&["orders".to_string(), "customers".to_string()])
            .unwrap();

        assert_eq!(result.pairwise_overlaps.len(), 1);
        assert_eq!(result.predictions.len(), 3); // INNER + 2 LEFT
    }
}
