import { useRef, useState } from 'react'
import { Download, Upload, Trash2, Settings } from 'lucide-react'
import { useERDStore } from '@/stores/erdStore'
import { ERDConfigModal } from './ERDConfigModal'

export function ERDToolbar() {
  const exportToJson = useERDStore((s) => s.exportToJson)
  const importFromJson = useERDStore((s) => s.importFromJson)
  const clearCanvas = useERDStore((s) => s.clearCanvas)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [configOpen, setConfigOpen] = useState(false)

  const handleExport = () => {
    const json = exportToJson()
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'erd-diagram.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const json = event.target?.result as string
      importFromJson(json)
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  const handleClear = () => {
    if (confirm('Clear all tables and relationships from the canvas?')) {
      clearCanvas()
    }
  }

  return (
    <>
      <div className="flex items-center gap-1 p-2 border-b border-mf-border bg-mf-panel">
        <button
          onClick={handleExport}
          className="p-1.5 rounded hover:bg-mf-border text-mf-muted hover:text-mf-text transition-colors"
          title="Export diagram"
        >
          <Download className="w-4 h-4" />
        </button>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="p-1.5 rounded hover:bg-mf-border text-mf-muted hover:text-mf-text transition-colors"
          title="Import diagram"
        >
          <Upload className="w-4 h-4" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleImport}
          className="hidden"
        />
        <div className="w-px h-4 bg-mf-border mx-1" />
        <button
          onClick={() => setConfigOpen(true)}
          className="p-1.5 rounded hover:bg-mf-border text-mf-muted hover:text-mf-text transition-colors"
          title="Validation settings"
        >
          <Settings className="w-4 h-4" />
        </button>
        <div className="flex-1" />
        <button
          onClick={handleClear}
          className="p-1.5 rounded hover:bg-red-500/20 text-mf-muted hover:text-red-400 transition-colors"
          title="Clear canvas"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
      {configOpen && <ERDConfigModal onClose={() => setConfigOpen(false)} />}
    </>
  )
}
