import { TopBar } from './TopBar'
import { Sidebar } from './Sidebar'
import { StatusBar } from './StatusBar'
import { ContextPanel } from './ContextPanel'
import { MainContent } from './MainContent'
import { useUIStore } from '@/stores/uiStore'

export function Layout() {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed)
  const contextPanelVisible = useUIStore((s) => s.contextPanelVisible)

  return (
    <div className="flex flex-col h-screen bg-mf-bg">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar collapsed={sidebarCollapsed} />
        <MainContent />
        {contextPanelVisible && <ContextPanel />}
      </div>
      <StatusBar />
    </div>
  )
}
