import type { ERDTable, ERDRelationship, ValidationIssue, ValidationConfig } from '@/stores/erdStore'

export function runValidation(
  tables: ERDTable[],
  relationships: ERDRelationship[],
  config: ValidationConfig
): ValidationIssue[] {
  const issues: ValidationIssue[] = []

  if (config.manyToMany) {
    issues.push(...validateManyToMany(relationships))
  }
  if (config.orphanTable) {
    issues.push(...validateOrphanTables(tables, relationships))
  }
  if (config.circularRef) {
    issues.push(...validateCircularRefs(tables, relationships))
  }
  if (config.naming) {
    issues.push(...validateNaming(tables, config.namingPattern))
  }
  if (config.normalization) {
    issues.push(...validateNormalization(tables))
  }
  if (config.missingFK) {
    issues.push(...validateMissingFK(tables, relationships))
  }

  return issues
}

function validateManyToMany(relationships: ERDRelationship[]): ValidationIssue[] {
  return relationships
    .filter((r) => r.cardinality === 'many-to-many')
    .map((r) => ({
      id: `m2m-${r.id}`,
      type: 'many-to-many' as const,
      severity: 'warning' as const,
      message: `Many-to-many relationship detected. Consider adding a junction table.`,
      nodeIds: [r.source, r.target],
    }))
}

function validateOrphanTables(tables: ERDTable[], relationships: ERDRelationship[]): ValidationIssue[] {
  const connectedIds = new Set<string>()
  relationships.forEach((r) => {
    connectedIds.add(r.source)
    connectedIds.add(r.target)
  })

  return tables
    .filter((t) => !connectedIds.has(t.id))
    .map((t) => ({
      id: `orphan-${t.id}`,
      type: 'orphan-table' as const,
      severity: 'info' as const,
      message: `Table "${t.frameName}" has no relationships.`,
      nodeIds: [t.id],
    }))
}

function validateCircularRefs(tables: ERDTable[], relationships: ERDRelationship[]): ValidationIssue[] {
  const issues: ValidationIssue[] = []
  const graph = new Map<string, string[]>()

  tables.forEach((t) => graph.set(t.id, []))
  relationships.forEach((r) => {
    graph.get(r.source)?.push(r.target)
  })

  const visited = new Set<string>()
  const recursionStack = new Set<string>()

  function dfs(nodeId: string, path: string[]): string[] | null {
    visited.add(nodeId)
    recursionStack.add(nodeId)

    for (const neighbor of graph.get(nodeId) || []) {
      if (!visited.has(neighbor)) {
        const cycle = dfs(neighbor, [...path, nodeId])
        if (cycle) return cycle
      } else if (recursionStack.has(neighbor)) {
        return [...path, nodeId, neighbor]
      }
    }

    recursionStack.delete(nodeId)
    return null
  }

  for (const table of tables) {
    if (!visited.has(table.id)) {
      const cycle = dfs(table.id, [])
      if (cycle) {
        const cycleStart = cycle.indexOf(cycle[cycle.length - 1])
        const cycleNodes = cycle.slice(cycleStart, -1)
        const tableNames = cycleNodes
          .map((id) => tables.find((t) => t.id === id)?.frameName)
          .filter(Boolean)
          .join(' -> ')

        issues.push({
          id: `circular-${cycleNodes.join('-')}`,
          type: 'circular-ref',
          severity: 'error',
          message: `Circular reference detected: ${tableNames}`,
          nodeIds: cycleNodes,
        })
        break
      }
    }
  }

  return issues
}

function validateNaming(tables: ERDTable[], pattern: string): ValidationIssue[] {
  const issues: ValidationIssue[] = []
  let regex: RegExp

  try {
    regex = new RegExp(pattern)
  } catch {
    return []
  }

  for (const table of tables) {
    for (const col of table.columns) {
      if (!regex.test(col.name)) {
        issues.push({
          id: `naming-${table.id}-${col.name}`,
          type: 'naming',
          severity: 'info',
          message: `Column "${col.name}" in "${table.frameName}" doesn't match pattern.`,
          nodeIds: [table.id],
        })
      }
    }
  }

  return issues
}

function validateNormalization(tables: ERDTable[]): ValidationIssue[] {
  const issues: ValidationIssue[] = []
  const numberedPattern = /^(.+?)(\d+)$/

  for (const table of tables) {
    const baseNames = new Map<string, string[]>()

    for (const col of table.columns) {
      const match = col.name.match(numberedPattern)
      if (match) {
        const base = match[1]
        if (!baseNames.has(base)) baseNames.set(base, [])
        baseNames.get(base)!.push(col.name)
      }
    }

    for (const [base, cols] of baseNames) {
      if (cols.length >= 2) {
        issues.push({
          id: `norm-${table.id}-${base}`,
          type: 'normalization',
          severity: 'warning',
          message: `Repeated columns "${cols.join(', ')}" in "${table.frameName}" suggest denormalization.`,
          nodeIds: [table.id],
        })
      }
    }
  }

  return issues
}

function validateMissingFK(tables: ERDTable[], relationships: ERDRelationship[]): ValidationIssue[] {
  const issues: ValidationIssue[] = []

  for (const rel of relationships) {
    const sourceTable = tables.find((t) => t.id === rel.source)
    const targetTable = tables.find((t) => t.id === rel.target)
    if (!sourceTable || !targetTable) continue

    const sourceCol = sourceTable.columns.find((c) => c.name === rel.sourceHandle)
    const targetCol = targetTable.columns.find((c) => c.name === rel.targetHandle)

    if (sourceCol && !sourceCol.isPK && !sourceCol.isFK) {
      issues.push({
        id: `fk-${rel.id}-source`,
        type: 'missing-fk',
        severity: 'info',
        message: `Column "${sourceCol.name}" in "${sourceTable.frameName}" is used in relationship but not marked as FK.`,
        nodeIds: [rel.source],
      })
    }

    if (targetCol && !targetCol.isPK && !targetCol.isFK) {
      issues.push({
        id: `fk-${rel.id}-target`,
        type: 'missing-fk',
        severity: 'info',
        message: `Column "${targetCol.name}" in "${targetTable.frameName}" is used in relationship but not marked as FK.`,
        nodeIds: [rel.target],
      })
    }
  }

  return issues
}
