import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { Key, Link } from 'lucide-react'
import type { ERDColumn } from '@/stores/erdStore'

export interface TableNodeData {
  frameName: string
  columns: ERDColumn[]
}

interface TableNodeProps {
  data: TableNodeData
  selected?: boolean
}

function TableNodeComponent({ data, selected }: TableNodeProps) {
  const { frameName, columns } = data

  return (
    <div
      className={`bg-mf-panel border rounded shadow-lg min-w-[180px] ${
        selected ? 'border-mf-accent' : 'border-mf-border'
      }`}
    >
      <div className="px-3 py-2 bg-mf-accent/10 border-b border-mf-border font-medium text-sm truncate">
        {frameName}
      </div>
      <div className="divide-y divide-mf-border/50">
        {columns.map((col) => (
          <div key={col.name} className="relative px-3 py-1.5 text-xs flex items-center gap-2">
            <Handle
              type="target"
              position={Position.Left}
              id={col.name}
              className="!w-2 !h-2 !bg-mf-muted !border-mf-border"
            />
            <div className="flex items-center gap-1 flex-1 min-w-0">
              {col.isPK && <Key className="w-3 h-3 text-yellow-500 shrink-0" />}
              {col.isFK && <Link className="w-3 h-3 text-blue-500 shrink-0" />}
              <span className="truncate">{col.name}</span>
            </div>
            <span className="text-mf-muted text-[10px] shrink-0">{col.type}</span>
            <Handle
              type="source"
              position={Position.Right}
              id={col.name}
              className="!w-2 !h-2 !bg-mf-muted !border-mf-border"
            />
          </div>
        ))}
      </div>
    </div>
  )
}

export const TableNode = memo(TableNodeComponent)
