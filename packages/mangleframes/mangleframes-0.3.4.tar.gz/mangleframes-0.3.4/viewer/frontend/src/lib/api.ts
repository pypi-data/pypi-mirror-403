const BASE_URL = ''

export interface Column {
  name: string
  type: string
  nullable: boolean
}

export interface Timing {
  spark_ms: number
  ipc_ms: number
  json_ms: number
  total_ms: number
  cached: boolean
}

export interface DataResponse {
  rows: Record<string, unknown>[]
  total: number
  offset: number
  timing: Timing
}

export interface SchemaResponse {
  columns: Column[]
}

export interface FramesResponse {
  frames: string[]
}

export interface StatsResponse {
  row_count: number
  columns: ColumnStats[]
}

export interface ColumnStats {
  name: string
  type: string
  null_count: number
  distinct_count?: number
  min?: string | number
  max?: string | number
  avg?: number
}

export interface QueryResponse {
  rows: Record<string, unknown>[]
  total: number
  timing: { execution_ms: number }
}

export interface CsvUploadResponse {
  frame_name: string
  columns: { name: string; data_type: string; nullable: boolean }[]
  row_count: number
}

export interface CsvFramesResponse {
  frames: string[]
}

export interface ReconcileStatistics {
  key_match_rate: number
  value_match_rate: number
  key_matched_groups: number
  value_matched_groups: number
  value_mismatched_groups: number
  source_groups: number
  source_only_groups: number
  target_groups: number
  target_only_groups: number
}

export interface ColumnTotal {
  column: string
  aggregation: string
  source_total: number
  target_total: number
  difference: number
  percent_diff: number
}

export interface ReconcileResponse {
  statistics: ReconcileStatistics
  column_totals: ColumnTotal[]
  source_only: { total: number; rows: Record<string, unknown>[] }
  target_only: { total: number; rows: Record<string, unknown>[] }
  matched_rows: { rows: Record<string, unknown>[] }
  mismatched_rows: { total: number; rows: Record<string, unknown>[] }
  source_frame: string
  target_frame: string
}

export interface ReconcileRequest {
  source_frame: string
  target_frame: string
  source_type?: string
  source_group_by: string[]
  target_group_by: string[]
  source_join_keys: string[]
  target_join_keys: string[]
  join_type: 'inner' | 'left' | 'right' | 'full'
  aggregations: { column: string; aggregations: string[] }[]
  sample_limit?: number
}

// History/Coverage Analysis Types
export interface HistoryFrameConfig {
  frame: string
  columns: string[]
}

export interface HistoryJoinPair {
  source_frame: string
  target_frame: string
  source_keys: string[]
  target_keys: string[]
}

export interface HistoryRequest {
  frames: HistoryFrameConfig[]
  join_pairs: HistoryJoinPair[]
  bucket_size?: 'day' | 'week' | 'month'
}

export interface TimelineBucket {
  bucket: string
  frame_counts: Record<string, number>
  all_present: boolean
}

export interface DateGap {
  start: string
  end: string
  periods: number
}

export interface TemporalRangeStats {
  frame: string
  column: string
  granularity: string
  min_date: string | null
  max_date: string | null
  total_rows: number
  null_dates: number
  distinct_dates: number
  internal_gaps: DateGap[]
}

export interface OverlapZone {
  start: string
  end: string
  span: string
  days: number
  valid: boolean
}

export interface FrameDataLoss {
  frame: string
  rows_before_overlap: number
  rows_after_overlap: number
  total_lost: number
  pct_lost: number
}

export interface JoinPrediction {
  join_type: string
  estimated_rows: number
  null_columns: Record<string, number>
  coverage_pct: number
}

export interface PairwiseOverlap {
  frame1: string
  frame2: string
  left_only: number
  right_only: number
  both: number
  overlap_pct: number
}

export interface CoverageResult {
  frames: string[]
  timeline: TimelineBucket[]
  temporal_ranges: TemporalRangeStats[]
  overlap_zone: OverlapZone | null
  data_loss: FrameDataLoss[]
  predictions: JoinPrediction[]
  pairwise_overlaps: PairwiseOverlap[]
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }))
    throw new Error(error.error || `Request failed: ${response.status}`)
  }

  return response.json()
}

export const api = {
  listFrames: () => request<FramesResponse>('/api/frames'),

  getSchema: (name: string) =>
    request<SchemaResponse>(`/api/frames/${encodeURIComponent(name)}/schema`),

  getData: (name: string, offset = 0, limit = 100) =>
    request<DataResponse>(
      `/api/frames/${encodeURIComponent(name)}/data?offset=${offset}&limit=${limit}`
    ),

  getStats: (name: string) =>
    request<StatsResponse>(`/api/frames/${encodeURIComponent(name)}/stats`),

  executeQuery: (sql: string) =>
    request<QueryResponse>('/api/query', {
      method: 'POST',
      body: JSON.stringify({ sql }),
    }),

  exportFrame: (name: string, format: 'csv' | 'json' | 'parquet') =>
    fetch(`${BASE_URL}/api/frames/${encodeURIComponent(name)}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format }),
    }),

  uploadCsv: async (file: File, frameName: string): Promise<CsvUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('frame_name', frameName)
    const response = await fetch(`${BASE_URL}/api/reconcile/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: response.statusText }))
      throw new Error(error.error || `Upload failed: ${response.status}`)
    }
    return response.json()
  },

  listCsvFrames: () => request<CsvFramesResponse>('/api/reconcile/frames'),

  reconcile: (req: ReconcileRequest) =>
    request<ReconcileResponse>('/api/reconcile', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  exportReconciliation: (req: ReconcileRequest) =>
    fetch(`${BASE_URL}/api/reconcile/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),

  analyzeHistory: (req: HistoryRequest) =>
    request<CoverageResult>('/api/history/analyze', {
      method: 'POST',
      body: JSON.stringify(req),
    }),
}
