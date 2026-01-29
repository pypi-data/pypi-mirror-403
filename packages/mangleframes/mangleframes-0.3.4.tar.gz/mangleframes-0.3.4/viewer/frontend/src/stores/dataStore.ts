import { create } from 'zustand'

export interface FrameTab {
  name: string
  offset: number
  limit: number
  columnOrder: string[] | null  // null = schema order
  hiddenColumns: Set<string>    // empty = all visible
  columnWidths: Record<string, number> | null  // null = default 150px
}

interface DataState {
  frames: string[]
  openTabs: FrameTab[]
  activeFrame: string | null
  recentQueries: string[]

  setFrames: (frames: string[]) => void
  openFrame: (name: string) => void
  closeFrame: (name: string) => void
  setActiveFrame: (name: string | null) => void
  updateFrameOffset: (name: string, offset: number) => void
  addRecentQuery: (query: string) => void
  setColumnOrder: (frame: string, order: string[]) => void
  toggleColumnVisibility: (frame: string, column: string) => void
  showAllColumns: (frame: string) => void
  hideAllColumns: (frame: string, keepFirst: string) => void
  resetColumnOrder: (frame: string) => void
  setColumnWidth: (frame: string, column: string, width: number) => void
}

export const useDataStore = create<DataState>((set, get) => ({
  frames: [],
  openTabs: [],
  activeFrame: null,
  recentQueries: [],

  setFrames: (frames) => set({ frames }),

  openFrame: (name) => {
    const { openTabs } = get()
    if (!openTabs.find((t) => t.name === name)) {
      set({
        openTabs: [
          ...openTabs,
          { name, offset: 0, limit: 100, columnOrder: null, hiddenColumns: new Set(), columnWidths: null },
        ],
        activeFrame: name,
      })
    } else {
      set({ activeFrame: name })
    }
  },

  closeFrame: (name) => {
    const { openTabs, activeFrame } = get()
    const newTabs = openTabs.filter((t) => t.name !== name)
    const newActive = activeFrame === name
      ? newTabs.length > 0 ? newTabs[newTabs.length - 1].name : null
      : activeFrame
    set({ openTabs: newTabs, activeFrame: newActive })
  },

  setActiveFrame: (name) => set({ activeFrame: name }),

  updateFrameOffset: (name, offset) => {
    const { openTabs } = get()
    set({
      openTabs: openTabs.map((t) =>
        t.name === name ? { ...t, offset } : t
      ),
    })
  },

  addRecentQuery: (query) => {
    const { recentQueries } = get()
    const filtered = recentQueries.filter((q) => q !== query)
    set({ recentQueries: [query, ...filtered].slice(0, 20) })
  },

  setColumnOrder: (frame, order) => {
    const { openTabs } = get()
    set({
      openTabs: openTabs.map((t) =>
        t.name === frame ? { ...t, columnOrder: order } : t
      ),
    })
  },

  toggleColumnVisibility: (frame, column) => {
    const { openTabs } = get()
    set({
      openTabs: openTabs.map((t) => {
        if (t.name !== frame) return t
        const newHidden = new Set(t.hiddenColumns)
        if (newHidden.has(column)) {
          newHidden.delete(column)
        } else {
          newHidden.add(column)
        }
        return { ...t, hiddenColumns: newHidden }
      }),
    })
  },

  showAllColumns: (frame) => {
    const { openTabs } = get()
    set({
      openTabs: openTabs.map((t) =>
        t.name === frame ? { ...t, hiddenColumns: new Set() } : t
      ),
    })
  },

  hideAllColumns: (frame, keepFirst) => {
    const { openTabs } = get()
    const tab = openTabs.find((t) => t.name === frame)
    if (!tab) return
    const order = tab.columnOrder ?? []
    const toHide = order.filter((c) => c !== keepFirst)
    set({
      openTabs: openTabs.map((t) =>
        t.name === frame ? { ...t, hiddenColumns: new Set(toHide) } : t
      ),
    })
  },

  resetColumnOrder: (frame) => {
    const { openTabs } = get()
    set({
      openTabs: openTabs.map((t) =>
        t.name === frame
          ? { ...t, columnOrder: null, hiddenColumns: new Set(), columnWidths: null }
          : t
      ),
    })
  },

  setColumnWidth: (frame, column, width) => {
    const { openTabs } = get()
    set({
      openTabs: openTabs.map((t) => {
        if (t.name !== frame) return t
        const newWidths = { ...(t.columnWidths ?? {}), [column]: width }
        return { ...t, columnWidths: newWidths }
      }),
    })
  },
}))
