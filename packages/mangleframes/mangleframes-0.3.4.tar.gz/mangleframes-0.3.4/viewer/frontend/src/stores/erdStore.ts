import { create } from 'zustand'

export interface ERDColumn {
  name: string
  type: string
  isPK: boolean
  isFK: boolean
}

export interface ERDTable {
  id: string
  frameName: string
  position: { x: number; y: number }
  columns: ERDColumn[]
}

export interface ERDRelationship {
  id: string
  source: string
  sourceHandle: string
  target: string
  targetHandle: string
  cardinality: 'one-to-one' | 'one-to-many' | 'many-to-one' | 'many-to-many'
}

export interface ValidationIssue {
  id: string
  type: 'many-to-many' | 'orphan-table' | 'circular-ref' | 'naming' | 'normalization' | 'missing-fk'
  severity: 'error' | 'warning' | 'info'
  message: string
  nodeIds: string[]
}

export interface ValidationConfig {
  manyToMany: boolean
  orphanTable: boolean
  circularRef: boolean
  naming: boolean
  normalization: boolean
  missingFK: boolean
  namingPattern: string
}

interface ERDState {
  tables: ERDTable[]
  relationships: ERDRelationship[]
  validationIssues: ValidationIssue[]
  validationConfig: ValidationConfig
  selectedTableId: string | null

  addTable: (table: ERDTable) => void
  removeTable: (id: string) => void
  updatePosition: (id: string, position: { x: number; y: number }) => void
  addRelationship: (rel: Omit<ERDRelationship, 'id'>) => void
  removeRelationship: (id: string) => void
  updateCardinality: (id: string, cardinality: ERDRelationship['cardinality']) => void
  setValidationConfig: (config: Partial<ValidationConfig>) => void
  setValidationIssues: (issues: ValidationIssue[]) => void
  setSelectedTable: (id: string | null) => void
  exportToJson: () => string
  importFromJson: (json: string) => void
  clearCanvas: () => void
}

const defaultValidationConfig: ValidationConfig = {
  manyToMany: true,
  orphanTable: true,
  circularRef: true,
  naming: true,
  normalization: true,
  missingFK: true,
  namingPattern: '^[a-z][a-z0-9_]*$',
}

export const useERDStore = create<ERDState>((set, get) => ({
  tables: [],
  relationships: [],
  validationIssues: [],
  validationConfig: defaultValidationConfig,
  selectedTableId: null,

  addTable: (table) => {
    const { tables } = get()
    if (tables.find((t) => t.id === table.id)) return
    set({ tables: [...tables, table] })
  },

  removeTable: (id) => {
    const { tables, relationships } = get()
    set({
      tables: tables.filter((t) => t.id !== id),
      relationships: relationships.filter((r) => r.source !== id && r.target !== id),
    })
  },

  updatePosition: (id, position) => {
    const { tables } = get()
    set({
      tables: tables.map((t) => (t.id === id ? { ...t, position } : t)),
    })
  },

  addRelationship: (rel) => {
    const { relationships } = get()
    const existing = relationships.find(
      (r) =>
        (r.source === rel.source && r.sourceHandle === rel.sourceHandle &&
         r.target === rel.target && r.targetHandle === rel.targetHandle) ||
        (r.source === rel.target && r.sourceHandle === rel.targetHandle &&
         r.target === rel.source && r.targetHandle === rel.sourceHandle)
    )
    if (existing) return
    const id = `rel-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
    set({ relationships: [...relationships, { ...rel, id }] })
  },

  removeRelationship: (id) => {
    const { relationships } = get()
    set({ relationships: relationships.filter((r) => r.id !== id) })
  },

  updateCardinality: (id, cardinality) => {
    const { relationships } = get()
    set({
      relationships: relationships.map((r) => (r.id === id ? { ...r, cardinality } : r)),
    })
  },

  setValidationConfig: (config) => {
    const { validationConfig } = get()
    set({ validationConfig: { ...validationConfig, ...config } })
  },

  setValidationIssues: (issues) => set({ validationIssues: issues }),

  setSelectedTable: (id) => set({ selectedTableId: id }),

  exportToJson: () => {
    const { tables, relationships, validationConfig } = get()
    return JSON.stringify(
      { version: '1.0', tables, relationships, validationConfig },
      null,
      2
    )
  },

  importFromJson: (json) => {
    try {
      const data = JSON.parse(json)
      if (data.version !== '1.0') return
      set({
        tables: data.tables || [],
        relationships: data.relationships || [],
        validationConfig: { ...defaultValidationConfig, ...data.validationConfig },
      })
    } catch {
      // Invalid JSON, ignore
    }
  },

  clearCanvas: () => set({ tables: [], relationships: [], validationIssues: [] }),
}))
