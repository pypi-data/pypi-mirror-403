import { useState, useEffect, useCallback } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useDataStore } from '@/stores/dataStore'
import { api, ReconcileResponse, ReconcileRequest } from '@/lib/api'
import { Play, Loader2, Upload, FileSpreadsheet, X, Download } from 'lucide-react'

const JOIN_TYPES = ['inner', 'left', 'right', 'full'] as const
const AGG_FUNCTIONS = ['sum', 'count', 'min', 'max', 'avg'] as const

export function Reconciliation() {
  const sparkFrames = useDataStore((s) => s.frames)
  const [csvFrames, setCsvFrames] = useState<string[]>([])
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadFrameName, setUploadFrameName] = useState('')
  const [sourceFrame, setSourceFrame] = useState('')
  const [targetFrame, setTargetFrame] = useState('')
  const [sourceGroupBy, setSourceGroupBy] = useState('')
  const [targetGroupBy, setTargetGroupBy] = useState('')
  const [sourceJoinKeys, setSourceJoinKeys] = useState('')
  const [targetJoinKeys, setTargetJoinKeys] = useState('')
  const [joinType, setJoinType] = useState<typeof JOIN_TYPES[number]>('inner')
  const [aggColumn, setAggColumn] = useState('')
  const [aggFunctions, setAggFunctions] = useState<string[]>(['sum'])
  const [sampleLimit, setSampleLimit] = useState(100)
  const [result, setResult] = useState<ReconcileResponse | null>(null)

  const csvFramesQuery = useQuery({
    queryKey: ['csvFrames'],
    queryFn: () => api.listCsvFrames(),
    refetchOnWindowFocus: false,
  })

  useEffect(() => {
    if (csvFramesQuery.data) {
      setCsvFrames(csvFramesQuery.data.frames)
      console.log('[Reconciliation] Loaded CSV frames:', csvFramesQuery.data.frames)
    }
  }, [csvFramesQuery.data])

  const allFrames = [
    ...csvFrames.map((f) => ({ name: f, type: 'csv' as const })),
    ...sparkFrames.map((f) => ({ name: f, type: 'spark' as const })),
  ]

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!uploadFile) throw new Error('No file selected')
      const name = uploadFrameName || uploadFile.name.replace(/\.csv$/i, '')
      console.log('[Reconciliation] Uploading CSV:', name)
      return api.uploadCsv(uploadFile, name)
    },
    onSuccess: (data) => {
      console.log('[Reconciliation] Upload success:', data)
      setCsvFrames((prev) => [...prev, data.frame_name])
      setUploadFile(null)
      setUploadFrameName('')
      csvFramesQuery.refetch()
    },
    onError: (err) => {
      console.error('[Reconciliation] Upload failed:', err)
    },
  })

  const buildRequest = (): ReconcileRequest => ({
    source_frame: sourceFrame,
    target_frame: targetFrame,
    source_type: csvFrames.includes(sourceFrame) ? 'csv' : 'spark',
    source_group_by: parseList(sourceGroupBy),
    target_group_by: parseList(targetGroupBy),
    source_join_keys: parseList(sourceJoinKeys),
    target_join_keys: parseList(targetJoinKeys),
    join_type: joinType,
    aggregations: aggColumn
      ? [{ column: aggColumn, aggregations: aggFunctions }]
      : [],
    sample_limit: sampleLimit,
  })

  const reconcileMutation = useMutation({
    mutationFn: async () => {
      const req = buildRequest()
      console.log('[Reconciliation] Executing:', req)
      return api.reconcile(req)
    },
    onSuccess: (data) => {
      console.log('[Reconciliation] Result:', data)
      setResult(data)
    },
  })

  const exportMutation = useMutation({
    mutationFn: async () => {
      const req = buildRequest()
      console.log('[Reconciliation] Exporting dashboard:', req)
      const response = await api.exportReconciliation(req)
      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: response.statusText }))
        throw new Error(error.error || `Export failed: ${response.status}`)
      }
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `reconciliation_${sourceFrame}_${targetFrame}.html`
      a.click()
      URL.revokeObjectURL(url)
      console.log('[Reconciliation] Dashboard exported successfully')
    },
  })

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) {
        setUploadFile(file)
        if (!uploadFrameName) {
          setUploadFrameName(file.name.replace(/\.csv$/i, ''))
        }
      }
    },
    [uploadFrameName]
  )

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file?.name.endsWith('.csv')) {
      setUploadFile(file)
      setUploadFrameName(file.name.replace(/\.csv$/i, ''))
    }
  }, [])

  const toggleAggFunction = (fn: string) => {
    setAggFunctions((prev) =>
      prev.includes(fn) ? prev.filter((f) => f !== fn) : [...prev, fn]
    )
  }

  const canReconcile =
    sourceFrame &&
    targetFrame &&
    sourceGroupBy &&
    targetGroupBy &&
    sourceJoinKeys &&
    targetJoinKeys &&
    aggColumn &&
    aggFunctions.length > 0

  return (
    <div className="p-3 space-y-4">
      <h3 className="text-sm font-semibold text-mf-text">Reconciliation</h3>

      <CsvUploadSection
        uploadFile={uploadFile}
        uploadFrameName={uploadFrameName}
        setUploadFrameName={setUploadFrameName}
        onFileChange={handleFileChange}
        onDrop={handleDrop}
        onClearFile={() => setUploadFile(null)}
        onUpload={() => uploadMutation.mutate()}
        isUploading={uploadMutation.isPending}
        uploadError={uploadMutation.error}
      />

      <ReconcileForm
        allFrames={allFrames}
        csvFrames={csvFrames}
        sourceFrame={sourceFrame}
        setSourceFrame={setSourceFrame}
        targetFrame={targetFrame}
        setTargetFrame={setTargetFrame}
        sourceGroupBy={sourceGroupBy}
        setSourceGroupBy={setSourceGroupBy}
        targetGroupBy={targetGroupBy}
        setTargetGroupBy={setTargetGroupBy}
        sourceJoinKeys={sourceJoinKeys}
        setSourceJoinKeys={setSourceJoinKeys}
        targetJoinKeys={targetJoinKeys}
        setTargetJoinKeys={setTargetJoinKeys}
        joinType={joinType}
        setJoinType={setJoinType}
        aggColumn={aggColumn}
        setAggColumn={setAggColumn}
        aggFunctions={aggFunctions}
        toggleAggFunction={toggleAggFunction}
        sampleLimit={sampleLimit}
        setSampleLimit={setSampleLimit}
      />

      <div className="flex gap-2">
        <button
          onClick={() => reconcileMutation.mutate()}
          disabled={reconcileMutation.isPending || !canReconcile}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs bg-mf-accent hover:bg-mf-accent/80 text-white rounded disabled:opacity-50"
        >
          {reconcileMutation.isPending ? (
            <Loader2 size={12} className="animate-spin" />
          ) : (
            <Play size={12} />
          )}
          Run Reconciliation
        </button>

        {result && (
          <button
            onClick={() => exportMutation.mutate()}
            disabled={exportMutation.isPending}
            className="flex items-center justify-center gap-2 px-3 py-2 text-xs bg-green-600 hover:bg-green-700 text-white rounded disabled:opacity-50"
            title="Export HTML Dashboard"
          >
            {exportMutation.isPending ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Download size={12} />
            )}
            Export
          </button>
        )}
      </div>

      {reconcileMutation.isError && (
        <div className="p-2 text-xs text-red-400 bg-red-500/10 rounded">
          {reconcileMutation.error instanceof Error
            ? reconcileMutation.error.message
            : 'Failed'}
        </div>
      )}

      {exportMutation.isError && (
        <div className="p-2 text-xs text-red-400 bg-red-500/10 rounded">
          {exportMutation.error instanceof Error
            ? exportMutation.error.message
            : 'Export failed'}
        </div>
      )}

      {result && <ReconcileResults result={result} />}
    </div>
  )
}

function CsvUploadSection({
  uploadFile,
  uploadFrameName,
  setUploadFrameName,
  onFileChange,
  onDrop,
  onClearFile,
  onUpload,
  isUploading,
  uploadError,
}: {
  uploadFile: File | null
  uploadFrameName: string
  setUploadFrameName: (v: string) => void
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onDrop: (e: React.DragEvent) => void
  onClearFile: () => void
  onUpload: () => void
  isUploading: boolean
  uploadError: Error | null
}) {
  return (
    <div className="p-3 bg-mf-panel rounded border border-mf-border space-y-2">
      <div className="text-xs font-medium text-mf-text flex items-center gap-2">
        <FileSpreadsheet size={14} />
        Upload CSV
      </div>

      <div
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-mf-border rounded p-3 text-center"
      >
        {uploadFile ? (
          <div className="flex items-center justify-between">
            <span className="text-xs text-mf-text truncate">{uploadFile.name}</span>
            <button onClick={onClearFile} className="text-mf-muted hover:text-mf-text">
              <X size={14} />
            </button>
          </div>
        ) : (
          <label className="cursor-pointer">
            <div className="text-xs text-mf-muted">
              Drop CSV here or{' '}
              <span className="text-mf-accent underline">browse</span>
            </div>
            <input
              type="file"
              accept=".csv"
              onChange={onFileChange}
              className="hidden"
            />
          </label>
        )}
      </div>

      {uploadFile && (
        <>
          <input
            type="text"
            value={uploadFrameName}
            onChange={(e) => setUploadFrameName(e.target.value)}
            placeholder="Frame name"
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          />
          <button
            onClick={onUpload}
            disabled={isUploading}
            className="w-full flex items-center justify-center gap-2 px-2 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded disabled:opacity-50"
          >
            {isUploading ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Upload size={12} />
            )}
            Upload
          </button>
        </>
      )}

      {uploadError && (
        <div className="text-xs text-red-400">
          {uploadError instanceof Error ? uploadError.message : 'Upload failed'}
        </div>
      )}
    </div>
  )
}

function ReconcileForm({
  allFrames,
  csvFrames,
  sourceFrame,
  setSourceFrame,
  targetFrame,
  setTargetFrame,
  sourceGroupBy,
  setSourceGroupBy,
  targetGroupBy,
  setTargetGroupBy,
  sourceJoinKeys,
  setSourceJoinKeys,
  targetJoinKeys,
  setTargetJoinKeys,
  joinType,
  setJoinType,
  aggColumn,
  setAggColumn,
  aggFunctions,
  toggleAggFunction,
  sampleLimit,
  setSampleLimit,
}: {
  allFrames: { name: string; type: 'csv' | 'spark' }[]
  csvFrames: string[]
  sourceFrame: string
  setSourceFrame: (v: string) => void
  targetFrame: string
  setTargetFrame: (v: string) => void
  sourceGroupBy: string
  setSourceGroupBy: (v: string) => void
  targetGroupBy: string
  setTargetGroupBy: (v: string) => void
  sourceJoinKeys: string
  setSourceJoinKeys: (v: string) => void
  targetJoinKeys: string
  setTargetJoinKeys: (v: string) => void
  joinType: typeof JOIN_TYPES[number]
  setJoinType: (v: typeof JOIN_TYPES[number]) => void
  aggColumn: string
  setAggColumn: (v: string) => void
  aggFunctions: string[]
  toggleAggFunction: (fn: string) => void
  sampleLimit: number
  setSampleLimit: (v: number) => void
}) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs text-mf-muted mb-1">Source Frame</label>
          <select
            value={sourceFrame}
            onChange={(e) => setSourceFrame(e.target.value)}
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          >
            <option value="">Select...</option>
            {allFrames.map((f) => (
              <option key={`${f.type}-${f.name}`} value={f.name}>
                {csvFrames.includes(f.name) ? `[CSV] ${f.name}` : f.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-mf-muted mb-1">Target Frame</label>
          <select
            value={targetFrame}
            onChange={(e) => setTargetFrame(e.target.value)}
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          >
            <option value="">Select...</option>
            {allFrames.map((f) => (
              <option key={`${f.type}-${f.name}`} value={f.name}>
                {csvFrames.includes(f.name) ? `[CSV] ${f.name}` : f.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs text-mf-muted mb-1">Source Group By</label>
          <input
            type="text"
            value={sourceGroupBy}
            onChange={(e) => setSourceGroupBy(e.target.value)}
            placeholder="col1, col2"
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          />
        </div>
        <div>
          <label className="block text-xs text-mf-muted mb-1">Target Group By</label>
          <input
            type="text"
            value={targetGroupBy}
            onChange={(e) => setTargetGroupBy(e.target.value)}
            placeholder="col1, col2"
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs text-mf-muted mb-1">Source Join Keys</label>
          <input
            type="text"
            value={sourceJoinKeys}
            onChange={(e) => setSourceJoinKeys(e.target.value)}
            placeholder="key1, key2"
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          />
        </div>
        <div>
          <label className="block text-xs text-mf-muted mb-1">Target Join Keys</label>
          <input
            type="text"
            value={targetJoinKeys}
            onChange={(e) => setTargetJoinKeys(e.target.value)}
            placeholder="key1, key2"
            className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs text-mf-muted mb-1">Join Type</label>
        <div className="flex gap-1">
          {JOIN_TYPES.map((jt) => (
            <button
              key={jt}
              onClick={() => setJoinType(jt)}
              className={`px-2 py-1 text-xs rounded ${
                joinType === jt
                  ? 'bg-mf-accent text-white'
                  : 'bg-mf-bg border border-mf-border text-mf-text'
              }`}
            >
              {jt}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-xs text-mf-muted mb-1">Aggregation Column</label>
        <input
          type="text"
          value={aggColumn}
          onChange={(e) => setAggColumn(e.target.value)}
          placeholder="amount"
          className="w-full px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text"
        />
      </div>

      <div>
        <label className="block text-xs text-mf-muted mb-1">Aggregation Functions</label>
        <div className="flex gap-1 flex-wrap">
          {AGG_FUNCTIONS.map((fn) => (
            <button
              key={fn}
              onClick={() => toggleAggFunction(fn)}
              className={`px-2 py-1 text-xs rounded ${
                aggFunctions.includes(fn)
                  ? 'bg-mf-accent text-white'
                  : 'bg-mf-bg border border-mf-border text-mf-text'
              }`}
            >
              {fn.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-xs text-mf-muted mb-1">
          Sample Limit: {sampleLimit}
        </label>
        <input
          type="range"
          min={10}
          max={500}
          step={10}
          value={sampleLimit}
          onChange={(e) => setSampleLimit(Number(e.target.value))}
          className="w-full"
        />
      </div>
    </div>
  )
}

function ReconcileResults({ result }: { result: ReconcileResponse }) {
  const { statistics, column_totals, source_only, target_only, matched_rows, mismatched_rows } = result
  const keyMatchPct = (statistics.key_match_rate * 100).toFixed(1)
  const valueMatchPct = (statistics.value_match_rate * 100).toFixed(1)

  return (
    <div className="mt-4 space-y-4">
      <div className="p-3 bg-mf-panel rounded border border-mf-border">
        <div className="text-xs font-medium text-mf-text mb-3">Statistics</div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <StatRow label="Key Match Rate" value={`${keyMatchPct}%`} color="text-green-400" />
          <StatRow
            label="Value Match Rate"
            value={`${valueMatchPct}%`}
            color={statistics.value_match_rate >= 0.99 ? 'text-green-400' : 'text-red-400'}
          />
          <StatRow label="Key Matched" value={statistics.key_matched_groups} />
          <StatRow label="Value Matched" value={statistics.value_matched_groups} />
          <StatRow
            label="Value Mismatched"
            value={statistics.value_mismatched_groups}
            color={statistics.value_mismatched_groups > 0 ? 'text-red-400' : 'text-green-400'}
          />
          <StatRow label="Source Groups" value={statistics.source_groups} />
          <StatRow label="Target Groups" value={statistics.target_groups} />
          <StatRow
            label="Source Only"
            value={statistics.source_only_groups}
            color="text-yellow-400"
          />
          <StatRow
            label="Target Only"
            value={statistics.target_only_groups}
            color="text-yellow-400"
          />
        </div>
      </div>

      {column_totals.length > 0 && (
        <div className="p-3 bg-mf-panel rounded border border-mf-border">
          <div className="text-xs font-medium text-mf-text mb-3">Column Totals</div>
          <div className="space-y-2">
            {column_totals.map((ct, i) => (
              <div key={i} className="text-xs p-2 bg-mf-bg rounded">
                <div className="font-medium text-mf-text mb-1">
                  {ct.column} ({ct.aggregation})
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>Source: {formatNum(ct.source_total)}</div>
                  <div>Target: {formatNum(ct.target_total)}</div>
                  <div
                    className={ct.difference !== 0 ? 'text-red-400' : 'text-green-400'}
                  >
                    Diff: {formatNum(ct.difference)}
                  </div>
                  <div className="text-mf-muted">{ct.percent_diff.toFixed(2)}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {mismatched_rows.rows.length > 0 && (
        <RowSection
          title="Value Mismatches"
          total={mismatched_rows.total}
          rows={mismatched_rows.rows}
          highlight="error"
        />
      )}
      <RowSection title="Source Only" total={source_only.total} rows={source_only.rows} />
      <RowSection title="Target Only" total={target_only.total} rows={target_only.rows} />
      <RowSection title="Value Matched Rows" rows={matched_rows.rows} />
    </div>
  )
}

function StatRow({
  label,
  value,
  color,
}: {
  label: string
  value: string | number
  color?: string
}) {
  return (
    <div className="flex justify-between">
      <span className="text-mf-muted">{label}:</span>
      <span className={color || 'text-mf-text'}>{value}</span>
    </div>
  )
}

function RowSection({
  title,
  total,
  rows,
  highlight,
}: {
  title: string
  total?: number
  rows: Record<string, unknown>[]
  highlight?: 'error' | 'warn'
}) {
  if (rows.length === 0) return null

  const borderClass = highlight === 'error'
    ? 'border-red-500/50'
    : highlight === 'warn'
    ? 'border-yellow-500/50'
    : 'border-mf-border'

  return (
    <div className={`p-3 bg-mf-panel rounded border ${borderClass}`}>
      <div className={`text-xs font-medium mb-2 ${highlight === 'error' ? 'text-red-400' : 'text-mf-text'}`}>
        {title}
        {total !== undefined && ` (${total} total)`}
      </div>
      <div className="max-h-40 overflow-y-auto space-y-1">
        {rows.slice(0, 10).map((row, i) => (
          <div key={i} className="text-xs p-2 bg-mf-bg rounded text-mf-muted">
            {JSON.stringify(row)}
          </div>
        ))}
        {rows.length > 10 && (
          <div className="text-xs text-mf-muted text-center">
            ...and {rows.length - 10} more
          </div>
        )}
      </div>
    </div>
  )
}

function parseList(str: string): string[] {
  return str
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

function formatNum(n: number): string {
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 })
}
