import { useCallback, useRef, useMemo, useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FixedSizeList } from 'react-window'
import { useDataStore } from '@/stores/dataStore'
import { useUIStore } from '@/stores/uiStore'
import { api } from '@/lib/api'
import { ChevronLeft, ChevronRight, Download } from 'lucide-react'
import { ColumnDropdown } from './ColumnDropdown'

export function DataGrid() {
  const activeFrame = useDataStore((s) => s.activeFrame)
  const openTabs = useDataStore((s) => s.openTabs)
  const updateFrameOffset = useDataStore((s) => s.updateFrameOffset)
  const setColumnOrder = useDataStore((s) => s.setColumnOrder)
  const toggleColumnVisibility = useDataStore((s) => s.toggleColumnVisibility)
  const showAllColumns = useDataStore((s) => s.showAllColumns)
  const hideAllColumns = useDataStore((s) => s.hideAllColumns)
  const resetColumnOrder = useDataStore((s) => s.resetColumnOrder)
  const setColumnWidth = useDataStore((s) => s.setColumnWidth)
  const setSelectedColumn = useUIStore((s) => s.setSelectedColumn)

  const [resizing, setResizing] = useState<{
    column: string
    startX: number
    startWidth: number
  } | null>(null)

  const activeTab = openTabs.find((t) => t.name === activeFrame)
  const offset = activeTab?.offset ?? 0
  const limit = activeTab?.limit ?? 100

  const { data: schemaData } = useQuery({
    queryKey: ['schema', activeFrame],
    queryFn: () => api.getSchema(activeFrame!),
    enabled: !!activeFrame,
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['data', activeFrame, offset, limit],
    queryFn: () => api.getData(activeFrame!, offset, limit),
    enabled: !!activeFrame,
  })

  const containerRef = useRef<HTMLDivElement>(null)
  const columns = schemaData?.columns ?? []
  const rows = data?.rows ?? []
  const total = data?.total ?? 0
  const timing = data?.timing

  useEffect(() => {
    if (activeFrame && columns.length > 0 && activeTab?.columnOrder === null) {
      setColumnOrder(activeFrame, columns.map((c) => c.name))
    }
  }, [activeFrame, columns, activeTab?.columnOrder, setColumnOrder])

  const visibleColumns = useMemo(() => {
    const order = activeTab?.columnOrder ?? columns.map((c) => c.name)
    const hidden = activeTab?.hiddenColumns ?? new Set<string>()
    return order
      .filter((name) => !hidden.has(name))
      .map((name) => columns.find((c) => c.name === name))
      .filter((col): col is NonNullable<typeof col> => col !== undefined)
  }, [columns, activeTab])

  const handlePrevPage = useCallback(() => {
    if (activeFrame && offset > 0) {
      updateFrameOffset(activeFrame, Math.max(0, offset - limit))
    }
  }, [activeFrame, offset, limit, updateFrameOffset])

  const handleNextPage = useCallback(() => {
    if (activeFrame && offset + limit < total) {
      updateFrameOffset(activeFrame, offset + limit)
    }
  }, [activeFrame, offset, limit, total, updateFrameOffset])

  const handleExport = async (format: 'csv' | 'json' | 'parquet') => {
    if (!activeFrame) return
    const response = await api.exportFrame(activeFrame, format)
    if (response.ok) {
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${activeFrame}.${format}`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  const getColumnWidth = useCallback((colName: string) => {
    return activeTab?.columnWidths?.[colName] ?? 150
  }, [activeTab?.columnWidths])

  const handleResizeStart = useCallback((e: React.MouseEvent, colName: string) => {
    e.preventDefault()
    e.stopPropagation()
    setResizing({ column: colName, startX: e.clientX, startWidth: getColumnWidth(colName) })
  }, [getColumnWidth])

  useEffect(() => {
    if (!resizing) return

    const handleMouseMove = (e: MouseEvent) => {
      const delta = e.clientX - resizing.startX
      const newWidth = Math.max(50, resizing.startWidth + delta)
      if (activeFrame) {
        setColumnWidth(activeFrame, resizing.column, newWidth)
      }
    }

    const handleMouseUp = () => setResizing(null)

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [resizing, activeFrame, setColumnWidth])

  if (!activeFrame) return null

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-400 text-sm">
        Error: {error instanceof Error ? error.message : 'Failed to load data'}
      </div>
    )
  }

  const rowHeight = 32
  const headerHeight = 32

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-mf-border">
        <div className="flex items-center gap-4 text-xs text-mf-muted">
          <span>{total.toLocaleString()} rows</span>
          {timing && (
            <>
              <span>Spark: {timing.spark_ms}ms</span>
              <span>Total: {timing.total_ms}ms</span>
              {timing.cached && <span className="text-green-500">cached</span>}
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          <ColumnDropdown
            columns={columns}
            columnOrder={activeTab?.columnOrder ?? null}
            hiddenColumns={activeTab?.hiddenColumns ?? new Set()}
            onReorder={(order) => activeFrame && setColumnOrder(activeFrame, order)}
            onToggle={(col) => activeFrame && toggleColumnVisibility(activeFrame, col)}
            onShowAll={() => activeFrame && showAllColumns(activeFrame)}
            onHideAll={(first) => activeFrame && hideAllColumns(activeFrame, first)}
            onReset={() => activeFrame && resetColumnOrder(activeFrame)}
          />
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-mf-hover hover:bg-mf-border rounded text-mf-muted hover:text-mf-text"
          >
            <Download size={12} />
            CSV
          </button>
          <button
            onClick={handlePrevPage}
            disabled={offset === 0}
            className="p-1 text-mf-muted hover:text-mf-text disabled:opacity-30"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-xs text-mf-muted">
            {offset + 1}-{Math.min(offset + limit, total)} of {total}
          </span>
          <button
            onClick={handleNextPage}
            disabled={offset + limit >= total}
            className="p-1 text-mf-muted hover:text-mf-text disabled:opacity-30"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      <div ref={containerRef} className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-mf-muted">
            Loading...
          </div>
        ) : (
          <div style={{ minWidth: visibleColumns.reduce((sum, col) => sum + getColumnWidth(col.name), 0) }}>
            <div
              className="flex bg-mf-panel sticky top-0 z-10 border-b border-mf-border"
              style={{ height: headerHeight }}
            >
              {visibleColumns.map((col) => (
                <div
                  key={col.name}
                  onClick={() => setSelectedColumn(col.name)}
                  className="relative flex items-center px-3 text-xs font-medium text-mf-muted hover:text-mf-text hover:bg-mf-hover border-r border-mf-border truncate cursor-pointer select-text"
                  style={{ width: getColumnWidth(col.name), height: headerHeight }}
                  title={`${col.name} (${col.type})`}
                >
                  <span className="truncate">{col.name}</span>
                  <div
                    onMouseDown={(e) => handleResizeStart(e, col.name)}
                    className={`absolute right-0 top-0 h-full w-1 cursor-col-resize hover:bg-mf-accent ${
                      resizing?.column === col.name ? 'bg-mf-accent' : ''
                    }`}
                  />
                </div>
              ))}
            </div>

            <FixedSizeList
              height={Math.max(200, (containerRef.current?.clientHeight ?? 400) - headerHeight)}
              itemCount={rows.length}
              itemSize={rowHeight}
              width="100%"
            >
              {({ index, style }) => {
                const row = rows[index]
                return (
                  <div
                    style={style}
                    className={`flex border-b border-mf-border ${
                      index % 2 === 0 ? 'bg-mf-bg' : 'bg-mf-panel/30'
                    } hover:bg-mf-hover`}
                  >
                    {visibleColumns.map((col) => (
                      <div
                        key={col.name}
                        className="flex items-center px-3 text-xs text-mf-text border-r border-mf-border truncate"
                        style={{ width: getColumnWidth(col.name), height: rowHeight }}
                        title={String(row[col.name] ?? '')}
                      >
                        {formatCellValue(row[col.name])}
                      </div>
                    ))}
                  </div>
                )
              }}
            </FixedSizeList>
          </div>
        )}
      </div>
    </div>
  )
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
