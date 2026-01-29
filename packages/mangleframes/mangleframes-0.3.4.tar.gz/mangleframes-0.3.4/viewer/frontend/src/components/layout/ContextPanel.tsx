import { useQuery } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { api } from '@/lib/api'
import { useDataStore } from '@/stores/dataStore'
import { useUIStore } from '@/stores/uiStore'

export function ContextPanel() {
  const toggleContextPanel = useUIStore((s) => s.toggleContextPanel)
  const selectedColumn = useUIStore((s) => s.selectedColumn)
  const activeFrame = useDataStore((s) => s.activeFrame)

  const { data: stats } = useQuery({
    queryKey: ['stats', activeFrame],
    queryFn: () => api.getStats(activeFrame!),
    enabled: !!activeFrame,
  })

  const columnStats = stats?.columns?.find((c) => c.name === selectedColumn)

  return (
    <div className="w-56 bg-mf-panel border-l border-mf-border flex flex-col">
      <div className="flex items-center justify-between p-2 border-b border-mf-border">
        <span className="text-xs text-mf-muted font-semibold uppercase">Context</span>
        <button
          onClick={toggleContextPanel}
          className="p-1 text-mf-muted hover:text-mf-text rounded hover:bg-mf-hover"
        >
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {selectedColumn && columnStats ? (
          <div className="space-y-3">
            <div>
              <div className="text-xs text-mf-muted mb-1">Column</div>
              <div className="text-sm font-medium text-mf-text">{selectedColumn}</div>
            </div>
            <div>
              <div className="text-xs text-mf-muted mb-1">Type</div>
              <div className="text-sm text-mf-text">{columnStats.type}</div>
            </div>
            <div>
              <div className="text-xs text-mf-muted mb-1">Nulls</div>
              <div className="text-sm text-mf-text">{columnStats.null_count}</div>
            </div>
            {columnStats.distinct_count !== undefined && (
              <div>
                <div className="text-xs text-mf-muted mb-1">Distinct</div>
                <div className="text-sm text-mf-text">{columnStats.distinct_count}</div>
              </div>
            )}
            {columnStats.min !== undefined && (
              <div>
                <div className="text-xs text-mf-muted mb-1">Min</div>
                <div className="text-sm text-mf-text font-mono">{String(columnStats.min)}</div>
              </div>
            )}
            {columnStats.max !== undefined && (
              <div>
                <div className="text-xs text-mf-muted mb-1">Max</div>
                <div className="text-sm text-mf-text font-mono">{String(columnStats.max)}</div>
              </div>
            )}
            {columnStats.avg !== undefined && (
              <div>
                <div className="text-xs text-mf-muted mb-1">Average</div>
                <div className="text-sm text-mf-text font-mono">{columnStats.avg.toFixed(2)}</div>
              </div>
            )}
          </div>
        ) : activeFrame ? (
          <div className="text-xs text-mf-muted">
            Click a column header to see statistics
          </div>
        ) : (
          <div className="text-xs text-mf-muted">
            Select a table to view details
          </div>
        )}
      </div>
    </div>
  )
}
