import { useUIStore } from '@/stores/uiStore'
import { useDataStore } from '@/stores/dataStore'
import { Circle } from 'lucide-react'

export function StatusBar() {
  const connected = useUIStore((s) => s.connected)
  const activeFrame = useDataStore((s) => s.activeFrame)
  const openTabs = useDataStore((s) => s.openTabs)

  const activeTab = openTabs.find((t) => t.name === activeFrame)

  return (
    <div className="flex items-center justify-between h-6 px-3 bg-mf-panel border-t border-mf-border text-xs">
      <div className="flex items-center gap-4 text-mf-muted">
        {activeTab && (
          <>
            <span>Offset: {activeTab.offset}</span>
            <span>Limit: {activeTab.limit}</span>
          </>
        )}
      </div>

      <div className="flex items-center gap-4 text-mf-muted">
        <div className="flex items-center gap-1">
          <Circle
            size={8}
            className={connected ? 'fill-green-500 text-green-500' : 'fill-red-500 text-red-500'}
          />
          <span>{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>
    </div>
  )
}
