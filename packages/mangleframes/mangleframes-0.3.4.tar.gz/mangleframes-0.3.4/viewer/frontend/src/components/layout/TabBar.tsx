import { useUIStore, TabView } from '@/stores/uiStore'

const tabs: { id: TabView; label: string }[] = [
  { id: 'data', label: 'Data' },
  { id: 'schema', label: 'Schema' },
  { id: 'stats', label: 'Stats' },
  { id: 'sql', label: 'SQL' },
  { id: 'quality', label: 'Quality' },
  { id: 'erd', label: 'ERD' },
]

export function TabBar() {
  const activeTab = useUIStore((s) => s.activeTab)
  const setActiveTab = useUIStore((s) => s.setActiveTab)

  return (
    <div className="flex items-center h-8 border-b border-mf-border bg-mf-panel px-2">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={`px-3 py-1 text-xs transition-colors ${
            activeTab === tab.id
              ? 'text-mf-accent border-b-2 border-mf-accent'
              : 'text-mf-muted hover:text-mf-text'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
