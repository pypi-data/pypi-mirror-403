import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useDataStore } from '@/stores/dataStore'
import { useUIStore } from '@/stores/uiStore'

export function SchemaView() {
  const activeFrame = useDataStore((s) => s.activeFrame)
  const setSelectedColumn = useUIStore((s) => s.setSelectedColumn)
  const selectedColumn = useUIStore((s) => s.selectedColumn)

  const { data, isLoading, error } = useQuery({
    queryKey: ['schema', activeFrame],
    queryFn: () => api.getSchema(activeFrame!),
    enabled: !!activeFrame,
  })

  if (!activeFrame) return null

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-mf-muted">
        Loading schema...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-400 text-sm">
        Error: {error instanceof Error ? error.message : 'Failed to load schema'}
      </div>
    )
  }

  const columns = data?.columns ?? []

  return (
    <div className="p-4">
      <h2 className="text-sm font-semibold text-mf-text mb-4">
        Schema: {activeFrame}
      </h2>
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
              <th className="text-left px-3 py-2 text-mf-muted font-medium border-b border-mf-border">
                Nullable
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
                <td className="px-3 py-2 text-mf-muted border-b border-mf-border">
                  {col.nullable ? 'Yes' : 'No'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 text-xs text-mf-muted">
        {columns.length} columns
      </div>
    </div>
  )
}
