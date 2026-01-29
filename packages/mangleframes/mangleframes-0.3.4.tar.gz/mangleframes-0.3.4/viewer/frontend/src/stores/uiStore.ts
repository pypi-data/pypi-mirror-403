import { create } from 'zustand'

export type TabView = 'data' | 'schema' | 'stats' | 'sql' | 'quality' | 'erd'
export type ToolPanel = 'join' | 'reconcile' | 'alerts' | null

interface UIState {
  sidebarCollapsed: boolean
  contextPanelVisible: boolean
  activeTab: TabView
  activeTool: ToolPanel
  connected: boolean
  selectedColumn: string | null

  toggleSidebar: () => void
  toggleContextPanel: () => void
  setActiveTab: (tab: TabView) => void
  setActiveTool: (tool: ToolPanel) => void
  setConnected: (connected: boolean) => void
  setSelectedColumn: (column: string | null) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  contextPanelVisible: true,
  activeTab: 'data',
  activeTool: null,
  connected: false,
  selectedColumn: null,

  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  toggleContextPanel: () => set((s) => ({ contextPanelVisible: !s.contextPanelVisible })),
  setActiveTab: (tab) => set({ activeTab: tab, activeTool: null }),
  setActiveTool: (tool) => set({ activeTool: tool }),
  setConnected: (connected) => set({ connected }),
  setSelectedColumn: (column) => set({ selectedColumn: column }),
}))
