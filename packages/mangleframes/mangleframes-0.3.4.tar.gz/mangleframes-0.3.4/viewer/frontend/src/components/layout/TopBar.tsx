import { X, Plus, Settings, RefreshCw, Zap } from 'lucide-react'
import { useDataStore } from '@/stores/dataStore'
import { useUIStore } from '@/stores/uiStore'

export function TopBar() {
  const { openTabs, activeFrame, setActiveFrame, closeFrame } = useDataStore()
  const connected = useUIStore((s) => s.connected)

  return (
    <div className="flex items-center h-10 bg-mf-panel border-b border-mf-border px-2">
      <div className="flex items-center gap-2 mr-4">
        <span className="text-mf-accent font-semibold text-sm">MangleFrames</span>
      </div>

      <div className="flex items-center flex-1 gap-1 overflow-x-auto">
        {openTabs.map((tab) => (
          <button
            key={tab.name}
            onClick={() => setActiveFrame(tab.name)}
            className={`flex items-center gap-2 px-3 py-1 text-xs rounded transition-colors ${
              activeFrame === tab.name
                ? 'bg-mf-hover text-mf-text'
                : 'text-mf-muted hover:text-mf-text hover:bg-mf-hover'
            }`}
          >
            <span className="truncate max-w-[120px]">{tab.name}</span>
            <X
              size={12}
              className="opacity-50 hover:opacity-100"
              onClick={(e) => {
                e.stopPropagation()
                closeFrame(tab.name)
              }}
            />
          </button>
        ))}
        {openTabs.length > 0 && (
          <button className="p-1 text-mf-muted hover:text-mf-text rounded hover:bg-mf-hover">
            <Plus size={14} />
          </button>
        )}
      </div>

      <div className="flex items-center gap-2">
        {connected && (
          <span title="Connected">
            <Zap size={14} className="text-green-500" />
          </span>
        )}
        <button className="p-1 text-mf-muted hover:text-mf-text rounded hover:bg-mf-hover">
          <RefreshCw size={14} />
        </button>
        <button className="p-1 text-mf-muted hover:text-mf-text rounded hover:bg-mf-hover">
          <Settings size={14} />
        </button>
      </div>
    </div>
  )
}
