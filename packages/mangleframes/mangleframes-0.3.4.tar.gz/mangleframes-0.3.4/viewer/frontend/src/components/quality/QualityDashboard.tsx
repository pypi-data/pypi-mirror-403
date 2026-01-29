import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useDataStore } from '@/stores/dataStore'
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

export function QualityDashboard() {
  const activeFrame = useDataStore((s) => s.activeFrame)

  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['stats', activeFrame],
    queryFn: () => api.getStats(activeFrame!),
    enabled: !!activeFrame,
  })

  if (!activeFrame) {
    return (
      <div className="flex items-center justify-center h-full text-mf-muted">
        Select a table to view quality metrics
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-mf-muted">
        Loading quality metrics...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-400 text-sm">
        Failed to load quality metrics
      </div>
    )
  }

  const columns = stats?.columns ?? []
  const rowCount = stats?.row_count ?? 0

  const qualityMetrics = columns.map((col) => {
    const nullRate = rowCount > 0 ? (col.null_count / rowCount) * 100 : 0
    const hasHighNullRate = nullRate > 10
    const hasLowDistinct = col.distinct_count !== undefined && col.distinct_count < 3

    return {
      name: col.name,
      type: col.type,
      nullRate,
      nullCount: col.null_count,
      distinctCount: col.distinct_count,
      issues: [
        hasHighNullRate ? `High null rate (${nullRate.toFixed(1)}%)` : null,
        hasLowDistinct ? `Low cardinality (${col.distinct_count} distinct)` : null,
      ].filter(Boolean),
    }
  })

  const totalIssues = qualityMetrics.reduce((acc, m) => acc + m.issues.length, 0)
  const healthScore = Math.max(0, 100 - totalIssues * 10)

  return (
    <div className="p-4">
      <h2 className="text-sm font-semibold text-mf-text mb-4">
        Data Quality: {activeFrame}
      </h2>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-mf-panel rounded border border-mf-border">
          <div className="text-xs text-mf-muted mb-1">Health Score</div>
          <div className={`text-2xl font-bold ${
            healthScore >= 80 ? 'text-green-400' :
            healthScore >= 50 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {healthScore}%
          </div>
        </div>
        <div className="p-4 bg-mf-panel rounded border border-mf-border">
          <div className="text-xs text-mf-muted mb-1">Total Rows</div>
          <div className="text-2xl font-bold text-mf-text">
            {rowCount.toLocaleString()}
          </div>
        </div>
        <div className="p-4 bg-mf-panel rounded border border-mf-border">
          <div className="text-xs text-mf-muted mb-1">Issues Found</div>
          <div className={`text-2xl font-bold ${totalIssues > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
            {totalIssues}
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-xs font-semibold text-mf-muted uppercase">Column Health</h3>
        {qualityMetrics.map((metric) => (
          <div
            key={metric.name}
            className="flex items-center justify-between p-3 bg-mf-panel rounded border border-mf-border"
          >
            <div className="flex items-center gap-3">
              {metric.issues.length === 0 ? (
                <CheckCircle size={16} className="text-green-400" />
              ) : metric.issues.length >= 2 ? (
                <XCircle size={16} className="text-red-400" />
              ) : (
                <AlertTriangle size={16} className="text-yellow-400" />
              )}
              <div>
                <div className="text-sm text-mf-text">{metric.name}</div>
                <div className="text-xs text-mf-muted">{metric.type}</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-mf-muted">
                {metric.nullRate.toFixed(1)}% nulls
              </div>
              {metric.issues.length > 0 && (
                <div className="text-xs text-yellow-400">
                  {metric.issues[0]}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
