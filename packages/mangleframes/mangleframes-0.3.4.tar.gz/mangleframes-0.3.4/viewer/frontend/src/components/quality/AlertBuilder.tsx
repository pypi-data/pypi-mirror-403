import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useDataStore } from '@/stores/dataStore'
import { Play, Loader2, Copy, Check } from 'lucide-react'

type AlertType = 'threshold' | 'null_rate' | 'row_count' | 'duplicate_keys'

const alertTypes: { id: AlertType; label: string; description: string }[] = [
  { id: 'threshold', label: 'Threshold', description: 'Check if values exceed limits' },
  { id: 'null_rate', label: 'Null Rate', description: 'Monitor null percentage' },
  { id: 'row_count', label: 'Row Count', description: 'Validate expected row counts' },
  { id: 'duplicate_keys', label: 'Duplicates', description: 'Detect duplicate keys' },
]

export function AlertBuilder() {
  const frames = useDataStore((s) => s.frames)
  const [alertType, setAlertType] = useState<AlertType>('threshold')
  const [table, setTable] = useState('')
  const [column, setColumn] = useState('')
  const [minValue, setMinValue] = useState('')
  const [maxValue, setMaxValue] = useState('')
  const [threshold, setThreshold] = useState('5')
  const [generatedSql, setGeneratedSql] = useState('')
  const [copied, setCopied] = useState(false)

  const mutation = useMutation({
    mutationFn: async () => {
      let endpoint = ''
      let body: Record<string, unknown> = { table }

      switch (alertType) {
        case 'threshold':
          endpoint = '/api/alerts/threshold'
          body = {
            table,
            column,
            min_value: minValue ? parseFloat(minValue) : null,
            max_value: maxValue ? parseFloat(maxValue) : null,
          }
          break
        case 'null_rate':
          endpoint = '/api/alerts/null_rate'
          body = {
            table,
            columns: column.split(',').map((c) => c.trim()),
            threshold: parseFloat(threshold) / 100,
          }
          break
        case 'row_count':
          endpoint = '/api/alerts/row_count'
          body = {
            table,
            min_rows: minValue ? parseInt(minValue) : null,
            max_rows: maxValue ? parseInt(maxValue) : null,
          }
          break
        case 'duplicate_keys':
          endpoint = '/api/alerts/duplicate_keys'
          body = {
            table,
            key_columns: column.split(',').map((c) => c.trim()),
          }
          break
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Generation failed')
      }
      return response.json()
    },
    onSuccess: (data) => setGeneratedSql(data.sql || ''),
  })

  const handleGenerate = () => {
    if (table) {
      mutation.mutate()
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedSql)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="p-3">
      <h3 className="text-sm font-semibold text-mf-text mb-4">Alert Builder</h3>

      <div className="space-y-3">
        <div>
          <label className="block text-xs text-mf-muted mb-1">Alert Type</label>
          <div className="grid grid-cols-2 gap-1">
            {alertTypes.map((type) => (
              <button
                key={type.id}
                onClick={() => setAlertType(type.id)}
                className={`p-2 text-xs rounded border ${
                  alertType === type.id
                    ? 'bg-mf-accent/20 border-mf-accent text-mf-text'
                    : 'bg-mf-bg border-mf-border text-mf-muted hover:text-mf-text'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs text-mf-muted mb-1">Table</label>
          <select
            value={table}
            onChange={(e) => setTable(e.target.value)}
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          >
            <option value="">Select table...</option>
            {frames.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>

        {(alertType === 'threshold' || alertType === 'null_rate' || alertType === 'duplicate_keys') && (
          <div>
            <label className="block text-xs text-mf-muted mb-1">
              {alertType === 'duplicate_keys' ? 'Key Columns' : 'Column(s)'}
            </label>
            <input
              type="text"
              value={column}
              onChange={(e) => setColumn(e.target.value)}
              placeholder={alertType === 'threshold' ? 'column' : 'col1, col2, ...'}
              className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
            />
          </div>
        )}

        {alertType === 'threshold' && (
          <>
            <div>
              <label className="block text-xs text-mf-muted mb-1">Min Value</label>
              <input
                type="number"
                value={minValue}
                onChange={(e) => setMinValue(e.target.value)}
                placeholder="Optional"
                className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
              />
            </div>
            <div>
              <label className="block text-xs text-mf-muted mb-1">Max Value</label>
              <input
                type="number"
                value={maxValue}
                onChange={(e) => setMaxValue(e.target.value)}
                placeholder="Optional"
                className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
              />
            </div>
          </>
        )}

        {alertType === 'null_rate' && (
          <div>
            <label className="block text-xs text-mf-muted mb-1">Threshold (%)</label>
            <input
              type="number"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              placeholder="5"
              className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
            />
          </div>
        )}

        {alertType === 'row_count' && (
          <>
            <div>
              <label className="block text-xs text-mf-muted mb-1">Min Rows</label>
              <input
                type="number"
                value={minValue}
                onChange={(e) => setMinValue(e.target.value)}
                placeholder="Optional"
                className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
              />
            </div>
            <div>
              <label className="block text-xs text-mf-muted mb-1">Max Rows</label>
              <input
                type="number"
                value={maxValue}
                onChange={(e) => setMaxValue(e.target.value)}
                placeholder="Optional"
                className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
              />
            </div>
          </>
        )}

        <button
          onClick={handleGenerate}
          disabled={mutation.isPending || !table}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs bg-mf-accent hover:bg-mf-accent/80 text-white rounded disabled:opacity-50"
        >
          {mutation.isPending ? (
            <Loader2 size={12} className="animate-spin" />
          ) : (
            <Play size={12} />
          )}
          Generate SQL
        </button>

        {mutation.isError && (
          <div className="p-2 text-xs text-red-400 bg-red-500/10 rounded">
            {mutation.error instanceof Error ? mutation.error.message : 'Failed'}
          </div>
        )}

        {generatedSql && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-mf-text">Generated SQL</span>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-xs text-mf-muted hover:text-mf-text"
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
            <pre className="p-2 text-xs bg-mf-bg border border-mf-border rounded overflow-x-auto font-mono text-mf-text">
              {generatedSql}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
