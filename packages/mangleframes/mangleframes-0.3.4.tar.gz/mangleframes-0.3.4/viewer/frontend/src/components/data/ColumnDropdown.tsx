import { useState, useRef, useEffect, useCallback } from 'react'
import { ChevronDown, GripVertical, Search } from 'lucide-react'

interface Column {
  name: string
  type: string
}

interface ColumnDropdownProps {
  columns: Column[]
  columnOrder: string[] | null
  hiddenColumns: Set<string>
  onReorder: (order: string[]) => void
  onToggle: (column: string) => void
  onShowAll: () => void
  onHideAll: (keepFirst: string) => void
  onReset: () => void
}

export function ColumnDropdown({
  columns,
  columnOrder,
  hiddenColumns,
  onReorder,
  onToggle,
  onShowAll,
  onHideAll,
  onReset,
}: ColumnDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const order = columnOrder ?? columns.map((c) => c.name)
  const visibleCount = order.filter((n) => !hiddenColumns.has(n)).length
  const totalCount = columns.length

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  const filteredOrder = search
    ? order.filter((name) => name.toLowerCase().includes(search.toLowerCase()))
    : order

  const handleDragStart = useCallback((index: number) => {
    setDraggedIndex(index)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault()
    if (draggedIndex === null || draggedIndex === index) return
    const newOrder = [...order]
    const [dragged] = newOrder.splice(draggedIndex, 1)
    newOrder.splice(index, 0, dragged)
    onReorder(newOrder)
    setDraggedIndex(index)
  }, [draggedIndex, order, onReorder])

  const handleDragEnd = useCallback(() => {
    setDraggedIndex(null)
  }, [])

  const handleHideAll = useCallback(() => {
    const firstVisible = order.find((n) => !hiddenColumns.has(n)) ?? order[0]
    onHideAll(firstVisible)
  }, [order, hiddenColumns, onHideAll])

  const getTypeLabel = useCallback((type: string): string => {
    const lower = type.toLowerCase()
    if (lower.includes('string') || lower.includes('varchar')) return 'str'
    if (lower.includes('int')) return 'int'
    if (lower.includes('double') || lower.includes('float')) return 'dbl'
    if (lower.includes('boolean') || lower.includes('bool')) return 'bool'
    if (lower.includes('date') && !lower.includes('timestamp')) return 'date'
    if (lower.includes('timestamp')) return 'ts'
    if (lower.includes('decimal')) return 'dec'
    if (lower.includes('binary')) return 'bin'
    if (lower.includes('array')) return 'arr'
    if (lower.includes('map')) return 'map'
    if (lower.includes('struct')) return 'obj'
    return type.slice(0, 4)
  }, [])

  return (
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1 px-2 py-1 text-xs bg-mf-hover hover:bg-mf-border rounded text-mf-muted hover:text-mf-text"
      >
        Columns ({visibleCount}/{totalCount})
        <ChevronDown size={12} className={isOpen ? 'rotate-180' : ''} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 z-50 w-64 bg-mf-panel border border-mf-border rounded shadow-lg">
          <div className="p-2 border-b border-mf-border">
            <div className="relative">
              <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-mf-muted" />
              <input
                type="text"
                placeholder="Search columns..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-7 pr-2 py-1 text-xs bg-mf-bg border border-mf-border rounded text-mf-text placeholder:text-mf-muted focus:outline-none focus:border-mf-accent"
              />
            </div>
          </div>

          <div className="max-h-64 overflow-y-auto">
            {filteredOrder.map((name, index) => {
              const col = columns.find((c) => c.name === name)
              if (!col) return null
              const isVisible = !hiddenColumns.has(name)
              return (
                <div
                  key={name}
                  draggable={!search}
                  onDragStart={() => handleDragStart(index)}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDragEnd={handleDragEnd}
                  className={`flex items-center gap-2 px-2 py-1.5 text-xs hover:bg-mf-hover cursor-pointer ${
                    draggedIndex === index ? 'opacity-50 bg-mf-hover' : ''
                  }`}
                >
                  {!search && (
                    <GripVertical size={12} className="text-mf-muted cursor-grab flex-shrink-0" />
                  )}
                  <input
                    type="checkbox"
                    checked={isVisible}
                    onChange={() => onToggle(name)}
                    className="w-3 h-3 accent-mf-accent flex-shrink-0"
                  />
                  <span className="text-mf-text truncate flex-1">{name}</span>
                  <span className="text-mf-accent font-mono text-xs flex-shrink-0">
                    {getTypeLabel(col.type)}
                  </span>
                </div>
              )
            })}
            {filteredOrder.length === 0 && (
              <div className="px-2 py-4 text-xs text-mf-muted text-center">
                No columns match
              </div>
            )}
          </div>

          <div className="flex items-center gap-1 p-2 border-t border-mf-border">
            <button
              onClick={onShowAll}
              className="flex-1 px-2 py-1 text-xs bg-mf-hover hover:bg-mf-border rounded text-mf-muted hover:text-mf-text"
            >
              All
            </button>
            <button
              onClick={handleHideAll}
              className="flex-1 px-2 py-1 text-xs bg-mf-hover hover:bg-mf-border rounded text-mf-muted hover:text-mf-text"
            >
              None
            </button>
            <button
              onClick={onReset}
              className="flex-1 px-2 py-1 text-xs bg-mf-hover hover:bg-mf-border rounded text-mf-muted hover:text-mf-text"
            >
              Reset
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
