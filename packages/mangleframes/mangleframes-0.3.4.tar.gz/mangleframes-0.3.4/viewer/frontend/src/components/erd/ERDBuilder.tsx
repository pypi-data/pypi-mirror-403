import { ReactFlowProvider } from '@xyflow/react'
import { ERDCanvas } from './ERDCanvas'
import { ERDToolbar } from './ERDToolbar'
import { ERDTableList } from './ERDTableList'
import { ERDValidationPanel } from './ERDValidationPanel'

export function ERDBuilder() {
  return (
    <ReactFlowProvider>
      <div className="h-full flex flex-col overflow-hidden">
        <ERDToolbar />
        <div className="flex-1 flex overflow-hidden">
          <ERDTableList />
          <ERDCanvas />
          <ERDValidationPanel />
        </div>
      </div>
    </ReactFlowProvider>
  )
}
