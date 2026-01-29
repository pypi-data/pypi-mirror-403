import { useUIStore } from '@/stores/uiStore'
import { useDataStore } from '@/stores/dataStore'
import { TabBar } from './TabBar'
import { DataGrid } from '@/components/data/DataGrid'
import { SchemaView } from '@/components/data/SchemaView'
import { ColumnStats } from '@/components/data/ColumnStats'
import { SQLEditor } from '@/components/analysis/SQLEditor'
import { QualityDashboard } from '@/components/quality/QualityDashboard'
import { JoinAnalyzer } from '@/components/analysis/JoinAnalyzer'
import { Reconciliation } from '@/components/analysis/Reconciliation'
import { AlertBuilder } from '@/components/quality/AlertBuilder'
import { ERDBuilder } from '@/components/erd'

export function MainContent() {
  const activeTab = useUIStore((s) => s.activeTab)
  const activeTool = useUIStore((s) => s.activeTool)
  const activeFrame = useDataStore((s) => s.activeFrame)

  const renderToolPanel = () => {
    switch (activeTool) {
      case 'join':
        return <JoinAnalyzer />
      case 'reconcile':
        return <Reconciliation />
      case 'alerts':
        return <AlertBuilder />
      default:
        return null
    }
  }

  const renderMainPanel = () => {
    if (!activeFrame && activeTab !== 'sql' && activeTab !== 'erd') {
      return (
        <div className="flex-1 flex items-center justify-center text-mf-muted">
          <div className="text-center">
            <div className="text-lg mb-2">No table selected</div>
            <div className="text-sm">Select a table from the sidebar to view data</div>
          </div>
        </div>
      )
    }

    switch (activeTab) {
      case 'data':
        return <DataGrid />
      case 'schema':
        return <SchemaView />
      case 'stats':
        return <ColumnStats />
      case 'sql':
        return <SQLEditor />
      case 'quality':
        return <QualityDashboard />
      case 'erd':
        return <ERDBuilder />
      default:
        return null
    }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-mf-bg">
      <TabBar />
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-hidden">{renderMainPanel()}</div>
        {activeTool && (
          <div className="w-80 border-l border-mf-border overflow-y-auto">
            {renderToolPanel()}
          </div>
        )}
      </div>
    </div>
  )
}
