import { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import Editor from '@monaco-editor/react'
import { Play, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import { useDataStore } from '@/stores/dataStore'

export function SQLEditor() {
  const [sql, setSql] = useState('SELECT * FROM ')
  const [result, setResult] = useState<{
    rows: Record<string, unknown>[]
    total: number
    timing: { execution_ms: number }
  } | null>(null)

  const addRecentQuery = useDataStore((s) => s.addRecentQuery)
  const recentQueries = useDataStore((s) => s.recentQueries)

  const mutation = useMutation({
    mutationFn: (query: string) => api.executeQuery(query),
    onSuccess: (data) => {
      setResult(data)
      addRecentQuery(sql)
    },
  })

  const handleExecute = useCallback(() => {
    if (sql.trim()) {
      mutation.mutate(sql)
    }
  }, [sql, mutation])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        handleExecute()
      }
    },
    [handleExecute]
  )

  return (
    <div className="flex flex-col h-full" onKeyDown={handleKeyDown}>
      <div className="flex items-center justify-between px-3 py-2 border-b border-mf-border">
        <span className="text-xs text-mf-muted">SQL Query Editor</span>
        <button
          onClick={handleExecute}
          disabled={mutation.isPending || !sql.trim()}
          className="flex items-center gap-1 px-3 py-1 text-xs bg-mf-accent hover:bg-mf-accent/80 text-white rounded disabled:opacity-50"
        >
          {mutation.isPending ? (
            <Loader2 size={12} className="animate-spin" />
          ) : (
            <Play size={12} />
          )}
          Run
        </button>
      </div>

      <div className="h-48 border-b border-mf-border">
        <Editor
          height="100%"
          defaultLanguage="sql"
          value={sql}
          onChange={(value) => setSql(value ?? '')}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            fontFamily: 'JetBrains Mono, monospace',
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            padding: { top: 8 },
          }}
        />
      </div>

      <div className="flex-1 overflow-auto">
        {mutation.isError && (
          <div className="p-3 text-sm text-red-400 bg-red-500/10 border-b border-red-500/20">
            {mutation.error instanceof Error
              ? mutation.error.message
              : 'Query failed'}
          </div>
        )}

        {result && (
          <>
            <div className="flex items-center justify-between px-3 py-2 border-b border-mf-border text-xs text-mf-muted">
              <span>{result.total} rows returned</span>
              <span>{result.timing.execution_ms}ms</span>
            </div>

            {result.rows.length > 0 && (
              <div className="overflow-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-mf-panel sticky top-0">
                      {Object.keys(result.rows[0]).map((col) => (
                        <th
                          key={col}
                          className="text-left px-3 py-2 text-mf-muted font-medium border-b border-r border-mf-border"
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.rows.map((row, i) => (
                      <tr
                        key={i}
                        className={`${
                          i % 2 === 0 ? 'bg-mf-bg' : 'bg-mf-panel/30'
                        } hover:bg-mf-hover`}
                      >
                        {Object.values(row).map((val, j) => (
                          <td
                            key={j}
                            className="px-3 py-2 text-mf-text border-b border-r border-mf-border font-mono"
                          >
                            {formatValue(val)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {!result && !mutation.isError && recentQueries.length > 0 && (
          <div className="p-3">
            <div className="text-xs text-mf-muted mb-2">Recent Queries</div>
            <div className="space-y-1">
              {recentQueries.slice(0, 5).map((query, i) => (
                <button
                  key={i}
                  onClick={() => setSql(query)}
                  className="block w-full text-left px-2 py-1 text-xs text-mf-text hover:bg-mf-hover rounded truncate font-mono"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return 'NULL'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
