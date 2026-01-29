import { useCallback, useRef, useMemo, useState, useEffect } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Node,
  Edge,
  NodeChange,
  EdgeChange,
  ReactFlowInstance,
  NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useERDStore, ERDTable, ERDRelationship } from '@/stores/erdStore'
import { api } from '@/lib/api'
import { TableNode } from './TableNode'
import { runValidation } from '@/lib/erdValidation'

const nodeTypes: NodeTypes = { tableNode: TableNode as NodeTypes[string] }

function tablesToNodes(tables: ERDTable[]): Node[] {
  return tables.map((t) => ({
    id: t.id,
    type: 'tableNode',
    position: t.position,
    data: { frameName: t.frameName, columns: t.columns },
  }))
}

function relationshipsToEdges(relationships: ERDRelationship[]): Edge[] {
  return relationships.map((r) => ({
    id: r.id,
    source: r.source,
    sourceHandle: r.sourceHandle,
    target: r.target,
    targetHandle: r.targetHandle,
    label: r.cardinality,
    labelStyle: { fontSize: 10 },
    style: { stroke: '#6366f1' },
    animated: r.cardinality === 'many-to-many',
  }))
}

export function ERDCanvas() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const reactFlowInstance = useRef<ReactFlowInstance | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)

  // Detect external drag start/end at document level
  useEffect(() => {
    const handleDragStart = () => setIsDragging(true)
    const handleDragEnd = () => {
      setIsDragging(false)
      setIsDragOver(false)
    }

    document.addEventListener('dragstart', handleDragStart)
    document.addEventListener('dragend', handleDragEnd)
    document.addEventListener('drop', handleDragEnd)

    return () => {
      document.removeEventListener('dragstart', handleDragStart)
      document.removeEventListener('dragend', handleDragEnd)
      document.removeEventListener('drop', handleDragEnd)
    }
  }, [])

  const tables = useERDStore((s) => s.tables)
  const relationships = useERDStore((s) => s.relationships)
  const validationConfig = useERDStore((s) => s.validationConfig)
  const addTable = useERDStore((s) => s.addTable)
  const updatePosition = useERDStore((s) => s.updatePosition)
  const addRelationship = useERDStore((s) => s.addRelationship)
  const removeRelationship = useERDStore((s) => s.removeRelationship)
  const setValidationIssues = useERDStore((s) => s.setValidationIssues)
  const setSelectedTable = useERDStore((s) => s.setSelectedTable)

  const initialNodes = useMemo(() => tablesToNodes(tables), [tables])
  const initialEdges = useMemo(() => relationshipsToEdges(relationships), [relationships])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      onNodesChange(changes)
      changes.forEach((change) => {
        if (change.type === 'position' && change.position && !change.dragging) {
          updatePosition(change.id, change.position)
        }
      })
    },
    [onNodesChange, updatePosition]
  )

  const handleEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      onEdgesChange(changes)
      changes.forEach((change) => {
        if (change.type === 'remove') {
          removeRelationship(change.id)
        }
      })
    },
    [onEdgesChange, removeRelationship]
  )

  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return
      if (!connection.sourceHandle || !connection.targetHandle) return

      addRelationship({
        source: connection.source,
        sourceHandle: connection.sourceHandle,
        target: connection.target,
        targetHandle: connection.targetHandle,
        cardinality: 'one-to-many',
      })

      setEdges((eds) => addEdge({ ...connection, style: { stroke: '#6366f1' } }, eds))

      const newRels = [
        ...relationships,
        {
          id: 'temp',
          source: connection.source,
          sourceHandle: connection.sourceHandle,
          target: connection.target,
          targetHandle: connection.targetHandle,
          cardinality: 'one-to-many' as const,
        },
      ]
      const issues = runValidation(tables, newRels, validationConfig)
      setValidationIssues(issues)
    },
    [addRelationship, relationships, tables, validationConfig, setEdges, setValidationIssues]
  )

  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes }: { nodes: Node[] }) => {
      setSelectedTable(selectedNodes.length === 1 ? selectedNodes[0].id : null)
    },
    [setSelectedTable]
  )

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDragEnter = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(true)
  }, [])

  const onDragLeave = useCallback((event: React.DragEvent) => {
    if (!event.currentTarget.contains(event.relatedTarget as globalThis.Node)) {
      setIsDragOver(false)
    }
  }, [])

  const onDrop = useCallback(
    async (event: React.DragEvent) => {
      event.preventDefault()
      setIsDragOver(false)
      const frameName = event.dataTransfer.getData('application/erd-frame')
      if (!frameName) return
      if (!reactFlowInstance.current) return

      const position = reactFlowInstance.current.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })

      try {
        const schema = await api.getSchema(frameName)
        const columns = schema.columns.map((col, idx) => ({
          name: col.name,
          type: col.type,
          isPK: idx === 0 && (col.name === 'id' || col.name.endsWith('_id')),
          isFK: idx !== 0 && col.name.endsWith('_id'),
        }))

        const tableId = `table-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
        const newTable: ERDTable = { id: tableId, frameName, position, columns }

        addTable(newTable)
        setNodes((nds) => [
          ...nds,
          {
            id: tableId,
            type: 'tableNode',
            position,
            data: { frameName, columns },
          },
        ])

        const issues = runValidation([...tables, newTable], relationships, validationConfig)
        setValidationIssues(issues)
      } catch (err) {
        console.error('Failed to fetch schema:', err)
      }
    },
    [addTable, tables, relationships, validationConfig, setNodes, setValidationIssues]
  )

  const onInit = useCallback((instance: ReactFlowInstance) => {
    reactFlowInstance.current = instance
  }, [])

  return (
    <div ref={reactFlowWrapper} className="flex-1 relative">
      {/* Drop zone overlay - captures events during drag */}
      <div
        className={`absolute inset-0 z-40 ${
          isDragOver ? 'bg-mf-accent/10 border-2 border-dashed border-mf-accent' : ''
        }`}
        style={{ pointerEvents: isDragging ? 'auto' : 'none' }}
        onDragEnter={onDragEnter}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      />
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onSelectionChange={onSelectionChange}
        onInit={onInit}
        nodeTypes={nodeTypes}
        fitView
        snapToGrid
        snapGrid={[15, 15]}
        panOnDrag={[1, 2]}
        selectionOnDrag={false}
        className="bg-mf-bg"
      >
        <Background color="#374151" gap={15} />
        <Controls className="!bg-mf-panel !border-mf-border" />
        <MiniMap
          nodeColor="#6366f1"
          maskColor="rgba(0, 0, 0, 0.8)"
          className="!bg-mf-panel !border-mf-border"
        />
      </ReactFlow>
    </div>
  )
}
