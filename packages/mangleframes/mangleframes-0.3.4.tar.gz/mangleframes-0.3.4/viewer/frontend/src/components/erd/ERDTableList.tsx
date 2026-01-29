import { Table2 } from 'lucide-react'
import { useDataStore } from '@/stores/dataStore'
import { useERDStore } from '@/stores/erdStore'

export function ERDTableList() {
  const frames = useDataStore((s) => s.frames)
  const tables = useERDStore((s) => s.tables)
  const addedFrames = new Set(tables.map((t) => t.frameName))

  const handleDragStart = (e: React.DragEvent, frameName: string) => {
    e.dataTransfer.setData('application/erd-frame', frameName)
    e.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div className="w-48 border-r border-mf-border bg-mf-panel flex flex-col">
      <div className="p-2 border-b border-mf-border text-xs font-medium text-mf-muted">
        Drag tables to canvas
      </div>
      <div className="flex-1 overflow-y-auto">
        {frames.map((frame) => {
          const isAdded = addedFrames.has(frame)
          return (
            <div
              key={frame}
              draggable={!isAdded}
              onDragStart={(e) => handleDragStart(e, frame)}
              className={`flex items-center gap-2 px-2 py-1.5 text-xs border-b border-mf-border/50 ${
                isAdded
                  ? 'text-mf-muted/50 cursor-not-allowed'
                  : 'text-mf-text cursor-grab hover:bg-mf-border/50 active:cursor-grabbing'
              }`}
            >
              <Table2 className="w-3 h-3 shrink-0" />
              <span className="truncate">{frame}</span>
              {isAdded && <span className="text-[10px] text-mf-accent ml-auto">added</span>}
            </div>
          )
        })}
        {frames.length === 0 && (
          <div className="p-3 text-xs text-mf-muted text-center">No tables available</div>
        )}
      </div>
    </div>
  )
}
