import { X } from 'lucide-react'
import { useERDStore } from '@/stores/erdStore'
import { runValidation } from '@/lib/erdValidation'

interface Props {
  onClose: () => void
}

export function ERDConfigModal({ onClose }: Props) {
  const config = useERDStore((s) => s.validationConfig)
  const setConfig = useERDStore((s) => s.setValidationConfig)
  const tables = useERDStore((s) => s.tables)
  const relationships = useERDStore((s) => s.relationships)
  const setValidationIssues = useERDStore((s) => s.setValidationIssues)

  const handleToggle = (key: keyof typeof config) => {
    if (key === 'namingPattern') return
    const newConfig = { ...config, [key]: !config[key] }
    setConfig(newConfig)
    const issues = runValidation(tables, relationships, newConfig)
    setValidationIssues(issues)
  }

  const handlePatternChange = (pattern: string) => {
    const newConfig = { ...config, namingPattern: pattern }
    setConfig(newConfig)
    const issues = runValidation(tables, relationships, newConfig)
    setValidationIssues(issues)
  }

  const rules = [
    { key: 'manyToMany', label: 'Many-to-Many', desc: 'Flag direct many-to-many relationships' },
    { key: 'orphanTable', label: 'Orphan Tables', desc: 'Tables without relationships' },
    { key: 'circularRef', label: 'Circular References', desc: 'Detect circular FK chains' },
    { key: 'naming', label: 'Naming Convention', desc: 'Check column naming patterns' },
    { key: 'normalization', label: 'Normalization', desc: 'Detect repeated column patterns' },
    { key: 'missingFK', label: 'Missing FK Markers', desc: 'Columns in relationships not marked FK' },
  ] as const

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-mf-panel border border-mf-border rounded-lg shadow-xl w-96 max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-3 border-b border-mf-border">
          <span className="font-medium text-sm">Validation Settings</span>
          <button onClick={onClose} className="p-1 hover:bg-mf-border rounded">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {rules.map(({ key, label, desc }) => (
            <label key={key} className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={config[key] as boolean}
                onChange={() => handleToggle(key)}
                className="mt-0.5 accent-mf-accent"
              />
              <div>
                <div className="text-sm text-mf-text">{label}</div>
                <div className="text-xs text-mf-muted">{desc}</div>
              </div>
            </label>
          ))}
          <div className="pt-2 border-t border-mf-border">
            <label className="text-xs text-mf-muted">Naming Pattern (regex)</label>
            <input
              type="text"
              value={config.namingPattern}
              onChange={(e) => handlePatternChange(e.target.value)}
              className="w-full mt-1 px-2 py-1 text-xs bg-mf-bg border border-mf-border rounded focus:outline-none focus:border-mf-accent"
              placeholder="^[a-z][a-z0-9_]*$"
            />
          </div>
        </div>
        <div className="p-3 border-t border-mf-border">
          <button
            onClick={onClose}
            className="w-full py-1.5 text-xs bg-mf-accent text-white rounded hover:bg-mf-accent/80"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
