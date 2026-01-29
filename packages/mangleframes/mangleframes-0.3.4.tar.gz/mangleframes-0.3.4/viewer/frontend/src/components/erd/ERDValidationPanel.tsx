import { useState } from 'react'
import { AlertTriangle, AlertCircle, Info, ChevronDown, ChevronRight } from 'lucide-react'
import { useERDStore, ValidationIssue } from '@/stores/erdStore'

const severityConfig = {
  error: { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/10' },
  warning: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
  info: { icon: Info, color: 'text-blue-400', bg: 'bg-blue-500/10' },
}

function IssueItem({ issue }: { issue: ValidationIssue }) {
  const { icon: Icon, color, bg } = severityConfig[issue.severity]

  return (
    <div className={`flex items-start gap-2 p-2 text-xs ${bg} rounded`}>
      <Icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${color}`} />
      <span className="text-mf-text">{issue.message}</span>
    </div>
  )
}

export function ERDValidationPanel() {
  const [collapsed, setCollapsed] = useState(false)
  const issues = useERDStore((s) => s.validationIssues)

  const errorCount = issues.filter((i) => i.severity === 'error').length
  const warningCount = issues.filter((i) => i.severity === 'warning').length
  const infoCount = issues.filter((i) => i.severity === 'info').length

  return (
    <div className="w-64 border-l border-mf-border bg-mf-panel flex flex-col">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-2 p-2 border-b border-mf-border text-xs font-medium text-mf-muted hover:text-mf-text"
      >
        {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        <span>Validation</span>
        {issues.length > 0 && (
          <span className="ml-auto flex items-center gap-1">
            {errorCount > 0 && <span className="text-red-400">{errorCount}</span>}
            {warningCount > 0 && <span className="text-yellow-400">{warningCount}</span>}
            {infoCount > 0 && <span className="text-blue-400">{infoCount}</span>}
          </span>
        )}
      </button>
      {!collapsed && (
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {issues.length === 0 ? (
            <div className="text-xs text-mf-muted text-center py-4">No validation issues</div>
          ) : (
            issues.map((issue) => <IssueItem key={issue.id} issue={issue} />)
          )}
        </div>
      )}
    </div>
  )
}
