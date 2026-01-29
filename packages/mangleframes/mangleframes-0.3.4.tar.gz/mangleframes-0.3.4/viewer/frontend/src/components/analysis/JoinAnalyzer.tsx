import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useDataStore } from '@/stores/dataStore'
import { Play, Loader2, Calendar } from 'lucide-react'
import { api, CoverageResult } from '@/lib/api'

interface JoinStatistics {
  left_total: number
  right_total: number
  matched_left: number
  matched_right: number
  match_rate_left: number
  match_rate_right: number
  cardinality: string
  left_null_keys: number
  right_null_keys: number
  left_duplicate_keys: number
  right_duplicate_keys: number
}

interface UnmatchedData {
  rows: Record<string, unknown>[]
  total: number
  columns_limited: boolean
}

interface JoinResult {
  statistics: JoinStatistics
  left_unmatched: UnmatchedData
  right_unmatched: UnmatchedData
}

export function JoinAnalyzer() {
  const frames = useDataStore((s) => s.frames)
  const [leftTable, setLeftTable] = useState('')
  const [rightTable, setRightTable] = useState('')
  const [leftKey, setLeftKey] = useState('')
  const [rightKey, setRightKey] = useState('')
  const [result, setResult] = useState<JoinResult | null>(null)
  const [bucketSize, setBucketSize] = useState<'day' | 'week' | 'month'>('month')
  const [coverageResult, setCoverageResult] = useState<CoverageResult | null>(null)

  const mutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/join/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          left_table: leftTable,
          right_table: rightTable,
          left_keys: [leftKey],
          right_keys: [rightKey],
        }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Analysis failed')
      }
      return response.json()
    },
    onSuccess: (data) => setResult(data),
  })

  const coverageMutation = useMutation({
    mutationFn: async () => {
      console.log('[JoinAnalyzer] Analyzing date coverage...')
      return api.analyzeHistory({
        frames: [
          { frame: leftTable, columns: [leftKey] },
          { frame: rightTable, columns: [rightKey] },
        ],
        join_pairs: [{
          source_frame: leftTable,
          target_frame: rightTable,
          source_keys: [leftKey],
          target_keys: [rightKey],
        }],
        bucket_size: bucketSize,
      })
    },
    onSuccess: (data) => {
      console.log('[JoinAnalyzer] Coverage analysis complete')
      setCoverageResult(data)
    },
  })

  const handleAnalyze = () => {
    if (leftTable && rightTable && leftKey && rightKey) {
      mutation.mutate()
    }
  }

  return (
    <div className="p-3">
      <h3 className="text-sm font-semibold text-mf-text mb-4">Join Analysis</h3>

      <div className="space-y-3">
        <div>
          <label className="block text-xs text-mf-muted mb-1">Left Table</label>
          <select
            value={leftTable}
            onChange={(e) => setLeftTable(e.target.value)}
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          >
            <option value="">Select table...</option>
            {frames.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs text-mf-muted mb-1">Left Key</label>
          <input
            type="text"
            value={leftKey}
            onChange={(e) => setLeftKey(e.target.value)}
            placeholder="Column name"
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          />
        </div>

        <div>
          <label className="block text-xs text-mf-muted mb-1">Right Table</label>
          <select
            value={rightTable}
            onChange={(e) => setRightTable(e.target.value)}
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          >
            <option value="">Select table...</option>
            {frames.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs text-mf-muted mb-1">Right Key</label>
          <input
            type="text"
            value={rightKey}
            onChange={(e) => setRightKey(e.target.value)}
            placeholder="Column name"
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          />
        </div>

        <button
          onClick={handleAnalyze}
          disabled={mutation.isPending || !leftTable || !rightTable || !leftKey || !rightKey}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs bg-mf-accent hover:bg-mf-accent/80 text-white rounded disabled:opacity-50"
        >
          {mutation.isPending ? (
            <Loader2 size={12} className="animate-spin" />
          ) : (
            <Play size={12} />
          )}
          Analyze Join
        </button>

        {mutation.isError && (
          <div className="p-2 text-xs text-red-400 bg-red-500/10 rounded">
            {mutation.error instanceof Error ? mutation.error.message : 'Analysis failed'}
          </div>
        )}

        {result && (
          <div className="mt-4 p-3 bg-mf-panel rounded border border-mf-border">
            <div className="text-xs font-medium text-mf-text mb-3">Results</div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-mf-muted">Left rows:</span>
                <span className="text-mf-text">{result.statistics.left_total.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-mf-muted">Right rows:</span>
                <span className="text-mf-text">{result.statistics.right_total.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-mf-muted">Matched (left):</span>
                <span className="text-green-400">{result.statistics.matched_left.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-mf-muted">Matched (right):</span>
                <span className="text-green-400">{result.statistics.matched_right.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-mf-muted">Left only:</span>
                <span className="text-yellow-400">{result.left_unmatched.total.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-mf-muted">Right only:</span>
                <span className="text-yellow-400">{result.right_unmatched.total.toLocaleString()}</span>
              </div>
              <div className="border-t border-mf-border pt-2 mt-2">
                <div className="flex justify-between">
                  <span className="text-mf-muted">Cardinality:</span>
                  <span className="text-mf-accent font-mono">{result.statistics.cardinality}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-mf-muted">Left match rate:</span>
                  <span className="text-mf-accent">{(result.statistics.match_rate_left * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-mf-muted">Right match rate:</span>
                  <span className="text-mf-accent">{(result.statistics.match_rate_right * 100).toFixed(1)}%</span>
                </div>
              </div>
              {(result.statistics.left_null_keys > 0 || result.statistics.right_null_keys > 0 ||
                result.statistics.left_duplicate_keys > 0 || result.statistics.right_duplicate_keys > 0) && (
                <div className="border-t border-mf-border pt-2 mt-2">
                  <div className="text-xs font-medium text-mf-muted mb-1">Key Quality</div>
                  {result.statistics.left_null_keys > 0 && (
                    <div className="flex justify-between">
                      <span className="text-mf-muted">Left null keys:</span>
                      <span className="text-red-400">{result.statistics.left_null_keys.toLocaleString()}</span>
                    </div>
                  )}
                  {result.statistics.right_null_keys > 0 && (
                    <div className="flex justify-between">
                      <span className="text-mf-muted">Right null keys:</span>
                      <span className="text-red-400">{result.statistics.right_null_keys.toLocaleString()}</span>
                    </div>
                  )}
                  {result.statistics.left_duplicate_keys > 0 && (
                    <div className="flex justify-between">
                      <span className="text-mf-muted">Left duplicate keys:</span>
                      <span className="text-orange-400">{result.statistics.left_duplicate_keys.toLocaleString()}</span>
                    </div>
                  )}
                  {result.statistics.right_duplicate_keys > 0 && (
                    <div className="flex justify-between">
                      <span className="text-mf-muted">Right duplicate keys:</span>
                      <span className="text-orange-400">{result.statistics.right_duplicate_keys.toLocaleString()}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Date Coverage Analysis */}
        <div className="mt-4 pt-4 border-t border-mf-border">
          <h4 className="text-xs font-medium text-mf-text mb-3 flex items-center gap-2">
            <Calendar size={12} />
            Date Coverage
          </h4>

          <div className="flex gap-1 mb-3">
            {(['day', 'week', 'month'] as const).map((size) => (
              <button
                key={size}
                onClick={() => setBucketSize(size)}
                className={`px-2 py-1 text-xs rounded ${
                  bucketSize === size
                    ? 'bg-mf-accent text-white'
                    : 'bg-mf-panel text-mf-muted hover:text-mf-text'
                }`}
              >
                {size.charAt(0).toUpperCase() + size.slice(1)}
              </button>
            ))}
          </div>

          <button
            onClick={() => coverageMutation.mutate()}
            disabled={coverageMutation.isPending || !leftTable || !rightTable || !leftKey || !rightKey}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs bg-mf-panel hover:bg-mf-border text-mf-text rounded disabled:opacity-50"
          >
            {coverageMutation.isPending ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Calendar size={12} />
            )}
            Analyze Coverage
          </button>

          {coverageMutation.isError && (
            <div className="mt-2 p-2 text-xs text-red-400 bg-red-500/10 rounded">
              {coverageMutation.error instanceof Error ? coverageMutation.error.message : 'Coverage analysis failed'}
            </div>
          )}

          {coverageResult && (
            <CoverageResults coverage={coverageResult} />
          )}
        </div>
      </div>
    </div>
  )
}

function CoverageResults({ coverage }: { coverage: CoverageResult }) {
  return (
    <div className="mt-3 space-y-3">
      {/* Overlap Zone Banner */}
      {coverage.overlap_zone && (
        <div className={`p-3 rounded text-xs ${
          coverage.overlap_zone.valid
            ? 'bg-green-500/10 border border-green-500/50 text-green-400'
            : 'bg-red-500/10 border border-red-500/50 text-red-400'
        }`}>
          {coverage.overlap_zone.valid
            ? `Overlap: ${coverage.overlap_zone.start} → ${coverage.overlap_zone.end} (${coverage.overlap_zone.span})`
            : 'No date overlap - INNER join would return 0 rows'}
        </div>
      )}

      {/* Temporal Range Table */}
      {coverage.temporal_ranges.length > 0 && (
        <div className="p-2 bg-mf-panel rounded">
          <div className="text-xs font-medium text-mf-text mb-2">Date Ranges</div>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-mf-muted text-left">
                <th className="pb-1">Frame</th>
                <th className="pb-1">Min</th>
                <th className="pb-1">Max</th>
                <th className="pb-1 text-right">Rows</th>
                <th className="pb-1 text-right">Nulls</th>
                <th className="pb-1 text-right">Gaps</th>
              </tr>
            </thead>
            <tbody className="text-mf-text">
              {coverage.temporal_ranges.map(r => (
                <tr key={`${r.frame}-${r.column}`}>
                  <td className="py-0.5 truncate max-w-[80px]" title={r.frame}>
                    {r.frame.split('.').pop()}
                  </td>
                  <td className="py-0.5">{r.min_date || '-'}</td>
                  <td className="py-0.5">{r.max_date || '-'}</td>
                  <td className="py-0.5 text-right">{r.total_rows.toLocaleString()}</td>
                  <td className={`py-0.5 text-right ${r.null_dates > 0 ? 'text-yellow-400' : ''}`}>
                    {r.null_dates}
                  </td>
                  <td className={`py-0.5 text-right ${r.internal_gaps.length > 0 ? 'text-yellow-400' : ''}`}>
                    {r.internal_gaps.length}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {coverage.temporal_ranges.length === 0 && (
        <div className="p-2 text-xs text-mf-muted bg-mf-panel rounded">
          No date columns detected
        </div>
      )}

      {/* Coverage Timeline */}
      {coverage.timeline.length > 0 && (
        <div className="p-2 bg-mf-panel rounded">
          <div className="text-xs font-medium text-mf-text mb-2">Timeline</div>
          <div className="space-y-1">
            {coverage.frames.map(frame => (
              <div key={frame} className="flex items-center gap-2">
                <span className="text-xs text-mf-muted w-20 truncate" title={frame}>
                  {frame.split('.').pop()}
                </span>
                <div className="flex flex-1 gap-px">
                  {coverage.timeline.map(bucket => (
                    <div
                      key={bucket.bucket}
                      className={`h-3 flex-1 rounded-sm ${
                        bucket.frame_counts[frame] > 0 ? 'bg-mf-accent' : 'bg-mf-border'
                      }`}
                      title={`${bucket.bucket}: ${bucket.frame_counts[frame] || 0} rows`}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-between text-[10px] text-mf-muted mt-1">
            <span>{coverage.timeline[0]?.bucket}</span>
            <span>{coverage.timeline[coverage.timeline.length - 1]?.bucket}</span>
          </div>
        </div>
      )}

      {/* Data Loss Section */}
      {coverage.data_loss.filter(d => d.total_lost > 0).length > 0 && (
        <div className="p-2 bg-mf-panel rounded">
          <div className="text-xs font-medium text-mf-text mb-2">Data Loss (INNER Join)</div>
          <div className="space-y-1">
            {coverage.data_loss.filter(d => d.total_lost > 0).map(loss => (
              <div key={loss.frame} className="p-2 bg-red-500/10 rounded text-xs">
                <span className="text-red-400">
                  {loss.frame.split('.').pop()}: {loss.total_lost.toLocaleString()} rows ({loss.pct_lost.toFixed(1)}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Join Predictions */}
      {coverage.predictions.length > 0 && (
        <div className="p-2 bg-mf-panel rounded">
          <div className="text-xs font-medium text-mf-text mb-2">Join Predictions</div>
          <div className="space-y-1">
            {coverage.predictions.map(pred => (
              <div key={pred.join_type} className="flex justify-between text-xs">
                <span className="text-mf-muted">{pred.join_type}</span>
                <span className="text-mf-text">
                  {pred.estimated_rows.toLocaleString()} rows ({pred.coverage_pct.toFixed(1)}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pairwise Overlaps */}
      {coverage.pairwise_overlaps.length > 0 && (
        <div className="p-2 bg-mf-panel rounded">
          <div className="text-xs font-medium text-mf-text mb-2">Key Overlap</div>
          <div className="space-y-2">
            {coverage.pairwise_overlaps.map(o => (
              <div key={`${o.frame1}-${o.frame2}`} className="text-xs">
                <div className="flex justify-between">
                  <span className="text-mf-muted">
                    {o.frame1.split('.').pop()} ↔ {o.frame2.split('.').pop()}
                  </span>
                  <span className="text-mf-accent">{o.overlap_pct.toFixed(1)}% overlap</span>
                </div>
                <div className="flex gap-3 text-mf-muted mt-0.5">
                  <span>Common: {o.both.toLocaleString()}</span>
                  <span>Left only: {o.left_only.toLocaleString()}</span>
                  <span>Right only: {o.right_only.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
