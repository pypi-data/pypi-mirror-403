import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useDataStore } from '@/stores/dataStore'
import { useUIStore } from '@/stores/uiStore'

export function ColumnStats() {
  const activeFrame = useDataStore((s) => s.activeFrame)
  const setSelectedColumn = useUIStore((s) => s.setSelectedColumn)
  const selectedColumn = useUIStore((s) => s.selectedColumn)

  const { data, isLoading, error } = useQuery({
    queryKey: ['stats', activeFrame],
    queryFn: () => api.getStats(activeFrame!),
    enabled: !!activeFrame,
  })

  if (!activeFrame) return null

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-mf-muted">
        Computing statistics...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-400 text-sm">
        Error: {error instanceof Error ? error.message : 'Failed to load stats'}
      </div>
    )
  }

  const columns = data?.columns ?? []
  const rowCount = data?.row_count ?? 0

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-mf-text">
          Statistics: {activeFrame}
        </h2>
        <span className="text-xs text-mf-muted">
          {rowCount.toLocaleString()} total rows
        </span>
      </div>

      <div className="border border-mf-border rounded overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-mf-panel">
              <th className="text-left px-3 py-2 text-mf-muted font-medium border-b border-mf-border">
                Column
              </th>
              <th className="text-left px-3 py-2 text-mf-muted font-medium border-b border-mf-border">
                Type
              </th>
              <th className="text-right px-3 py-2 text-mf-muted font-medium border-b border-mf-border">
                Nulls
              </th>
              <th className="text-right px-3 py-2 text-mf-muted font-medium border-b border-mf-border">
                Distinct
              </th>
              <th className="text-right px-3 py-2 text-mf-muted font-medium border-b border-mf-border">
                Min
              </th>
              <th className="text-right px-3 py-2 text-mf-muted font-medium border-b border-mf-border">
                Max
              </th>
              <th className="text-right px-3 py-2 text-mf-muted font-medium border-b border-mf-border">
                Avg
              </th>
            </tr>
          </thead>
          <tbody>
            {columns.map((col, index) => (
              <tr
                key={col.name}
                onClick={() => setSelectedColumn(col.name)}
                className={`cursor-pointer ${
                  selectedColumn === col.name ? 'bg-mf-accent/20' : ''
                } ${index % 2 === 0 ? 'bg-mf-bg' : 'bg-mf-panel/30'} hover:bg-mf-hover`}
              >
                <td className="px-3 py-2 text-mf-text border-b border-mf-border">
                  {col.name}
                </td>
                <td className="px-3 py-2 text-mf-accent font-mono border-b border-mf-border">
                  {col.type}
                </td>
                <td className="px-3 py-2 text-right text-mf-text border-b border-mf-border">
                  {col.null_count.toLocaleString()}
                  {rowCount > 0 && (
                    <span className="text-mf-muted ml-1">
                      ({((col.null_count / rowCount) * 100).toFixed(1)}%)
                    </span>
                  )}
                </td>
                <td className="px-3 py-2 text-right text-mf-text border-b border-mf-border font-mono">
                  {col.distinct_count?.toLocaleString() ?? '-'}
                </td>
                <td className="px-3 py-2 text-right text-mf-text border-b border-mf-border font-mono">
                  {col.min !== undefined ? String(col.min) : '-'}
                </td>
                <td className="px-3 py-2 text-right text-mf-text border-b border-mf-border font-mono">
                  {col.max !== undefined ? String(col.max) : '-'}
                </td>
                <td className="px-3 py-2 text-right text-mf-text border-b border-mf-border font-mono">
                  {col.avg !== undefined ? col.avg.toFixed(2) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
