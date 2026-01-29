import { useQuery } from '@tanstack/react-query'
import {
  Table,
  Code,
  GitCompare,
  FileCheck,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { api } from '@/lib/api'
import { useDataStore } from '@/stores/dataStore'
import { useUIStore } from '@/stores/uiStore'

interface SidebarProps {
  collapsed: boolean
}

export function Sidebar({ collapsed }: SidebarProps) {
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)
  const setActiveTool = useUIStore((s) => s.setActiveTool)
  const activeTool = useUIStore((s) => s.activeTool)
  const { openFrame, setFrames, frames } = useDataStore()

  const { data, isLoading } = useQuery({
    queryKey: ['frames'],
    queryFn: api.listFrames,
    refetchInterval: 10000,
  })

  if (data?.frames && data.frames !== frames) {
    setFrames(data.frames)
  }

  const tools = [
    { id: 'join' as const, icon: GitCompare, label: 'Join Analysis' },
    { id: 'reconcile' as const, icon: FileCheck, label: 'Reconciliation' },
    { id: 'alerts' as const, icon: AlertTriangle, label: 'Alerts' },
  ]

  if (collapsed) {
    return (
      <div className="flex flex-col w-10 bg-mf-panel border-r border-mf-border">
        <button
          onClick={toggleSidebar}
          className="p-2 text-mf-muted hover:text-mf-text"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col w-48 bg-mf-panel border-r border-mf-border">
      <div className="flex items-center justify-between p-2 border-b border-mf-border">
        <span className="text-xs text-mf-muted font-semibold uppercase">Tables</span>
        <button
          onClick={toggleSidebar}
          className="p-1 text-mf-muted hover:text-mf-text rounded hover:bg-mf-hover"
        >
          <ChevronLeft size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="text-xs text-mf-muted p-2">Loading...</div>
        ) : (
          <div className="space-y-1">
            {frames.map((frame) => (
              <button
                key={frame}
                onClick={() => openFrame(frame)}
                className="flex items-center gap-2 w-full px-2 py-1 text-xs text-left rounded hover:bg-mf-hover text-mf-text"
              >
                <Table size={12} className="text-mf-muted shrink-0" />
                <span className="truncate">{frame}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-mf-border p-2">
        <span className="text-xs text-mf-muted font-semibold uppercase block mb-2">SQL</span>
        <button
          onClick={() => useUIStore.getState().setActiveTab('sql')}
          className="flex items-center gap-2 w-full px-2 py-1 text-xs rounded hover:bg-mf-hover text-mf-muted hover:text-mf-text"
        >
          <Code size={12} />
          <span>Query Editor</span>
        </button>
      </div>

      <div className="border-t border-mf-border p-2">
        <span className="text-xs text-mf-muted font-semibold uppercase block mb-2">Tools</span>
        <div className="space-y-1">
          {tools.map((tool) => (
            <button
              key={tool.id}
              onClick={() => setActiveTool(activeTool === tool.id ? null : tool.id)}
              className={`flex items-center gap-2 w-full px-2 py-1 text-xs rounded ${
                activeTool === tool.id
                  ? 'bg-mf-accent/20 text-mf-accent'
                  : 'hover:bg-mf-hover text-mf-muted hover:text-mf-text'
              }`}
            >
              <tool.icon size={12} />
              <span>{tool.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
