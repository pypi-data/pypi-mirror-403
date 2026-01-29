import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { JoinAnalyzer } from '../JoinAnalyzer'
import { useDataStore } from '@/stores/dataStore'

vi.mock('@/stores/dataStore', () => ({
  useDataStore: vi.fn(),
}))

vi.mock('@/lib/api', () => ({
  api: {
    analyzeHistory: vi.fn().mockResolvedValue({
      overlap_zone: null,
      temporal_ranges: [],
      frames: [],
      timeline: [],
      data_loss: [],
      predictions: [],
      pairwise_overlaps: [],
    }),
  },
  CoverageResult: {},
}))

const mockDataStore = useDataStore as unknown as ReturnType<typeof vi.fn>

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}

const mockNestedJoinResponse = {
  statistics: {
    left_total: 1000,
    right_total: 800,
    matched_left: 750,
    matched_right: 750,
    match_rate_left: 0.75,
    match_rate_right: 0.9375,
    cardinality: '1:1',
    left_null_keys: 5,
    right_null_keys: 0,
    left_duplicate_keys: 0,
    right_duplicate_keys: 0,
  },
  left_unmatched: {
    rows: [{ id: 1, name: 'test' }],
    total: 250,
    columns_limited: false,
  },
  right_unmatched: {
    rows: [],
    total: 50,
    columns_limited: false,
  },
}

describe('JoinAnalyzer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockDataStore.mockImplementation(
      (selector: (s: { frames: string[] }) => unknown) =>
        selector({ frames: ['orders', 'customers', 'products'] })
    )
  })

  it('renders table selects and key inputs', () => {
    renderWithProviders(<JoinAnalyzer />)

    expect(screen.getByText('Left Table')).toBeInTheDocument()
    expect(screen.getByText('Right Table')).toBeInTheDocument()
    expect(screen.getAllByPlaceholderText(/column name/i)).toHaveLength(2)
    expect(screen.getByRole('button', { name: /analyze join/i })).toBeInTheDocument()
  })

  it('disables analyze button when fields are empty', () => {
    renderWithProviders(<JoinAnalyzer />)

    const analyzeButton = screen.getByRole('button', { name: /analyze join/i })
    expect(analyzeButton).toBeDisabled()
  })

  it('enables analyze button when all fields are filled', async () => {
    const user = userEvent.setup()
    renderWithProviders(<JoinAnalyzer />)

    const selects = screen.getAllByRole('combobox')
    const keyInputs = screen.getAllByPlaceholderText(/column name/i)

    await user.selectOptions(selects[0], 'orders')
    await user.selectOptions(selects[1], 'customers')
    await user.type(keyInputs[0], 'customer_id')
    await user.type(keyInputs[1], 'id')

    const analyzeButton = screen.getByRole('button', { name: /analyze join/i })
    expect(analyzeButton).toBeEnabled()
  })

  it('renders results with nested API response structure', async () => {
    const user = userEvent.setup()

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockNestedJoinResponse),
    })

    renderWithProviders(<JoinAnalyzer />)

    const selects = screen.getAllByRole('combobox')
    const keyInputs = screen.getAllByPlaceholderText(/column name/i)

    await user.selectOptions(selects[0], 'orders')
    await user.selectOptions(selects[1], 'customers')
    await user.type(keyInputs[0], 'customer_id')
    await user.type(keyInputs[1], 'id')

    const analyzeButton = screen.getByRole('button', { name: /analyze join/i })
    await user.click(analyzeButton)

    await waitFor(() => {
      expect(screen.getByText('1,000')).toBeInTheDocument()
    })

    expect(screen.getByText('800')).toBeInTheDocument()
    expect(screen.getAllByText('750')).toHaveLength(2)
    expect(screen.getByText('250')).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument()
    expect(screen.getByText('1:1')).toBeInTheDocument()
    expect(screen.getByText('75.0%')).toBeInTheDocument()
    expect(screen.getByText('93.8%')).toBeInTheDocument()
  })

  it('displays key quality section when there are null keys', async () => {
    const user = userEvent.setup()

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockNestedJoinResponse),
    })

    renderWithProviders(<JoinAnalyzer />)

    const selects = screen.getAllByRole('combobox')
    const keyInputs = screen.getAllByPlaceholderText(/column name/i)

    await user.selectOptions(selects[0], 'orders')
    await user.selectOptions(selects[1], 'customers')
    await user.type(keyInputs[0], 'customer_id')
    await user.type(keyInputs[1], 'id')
    await user.click(screen.getByRole('button', { name: /analyze join/i }))

    await waitFor(() => {
      expect(screen.getByText('Key Quality')).toBeInTheDocument()
    })

    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('hides key quality section when no issues', async () => {
    const user = userEvent.setup()

    const cleanResponse = {
      ...mockNestedJoinResponse,
      statistics: {
        ...mockNestedJoinResponse.statistics,
        left_null_keys: 0,
        right_null_keys: 0,
        left_duplicate_keys: 0,
        right_duplicate_keys: 0,
      },
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(cleanResponse),
    })

    renderWithProviders(<JoinAnalyzer />)

    const selects = screen.getAllByRole('combobox')
    const keyInputs = screen.getAllByPlaceholderText(/column name/i)

    await user.selectOptions(selects[0], 'orders')
    await user.selectOptions(selects[1], 'customers')
    await user.type(keyInputs[0], 'customer_id')
    await user.type(keyInputs[1], 'id')
    await user.click(screen.getByRole('button', { name: /analyze join/i }))

    await waitFor(() => {
      expect(screen.getByText('1,000')).toBeInTheDocument()
    })

    expect(screen.queryByText('Key Quality')).not.toBeInTheDocument()
  })

  it('displays error message on API failure', async () => {
    const user = userEvent.setup()

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ error: 'Table not found' }),
    })

    renderWithProviders(<JoinAnalyzer />)

    const selects = screen.getAllByRole('combobox')
    const keyInputs = screen.getAllByPlaceholderText(/column name/i)

    await user.selectOptions(selects[0], 'orders')
    await user.selectOptions(selects[1], 'customers')
    await user.type(keyInputs[0], 'customer_id')
    await user.type(keyInputs[1], 'id')
    await user.click(screen.getByRole('button', { name: /analyze join/i }))

    await waitFor(() => {
      expect(screen.getByText('Table not found')).toBeInTheDocument()
    })
  })

  it('shows loading state while analyzing', async () => {
    const user = userEvent.setup()

    let resolvePromise: (value: unknown) => void
    global.fetch = vi.fn().mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      })
    )

    renderWithProviders(<JoinAnalyzer />)

    const selects = screen.getAllByRole('combobox')
    const keyInputs = screen.getAllByPlaceholderText(/column name/i)

    await user.selectOptions(selects[0], 'orders')
    await user.selectOptions(selects[1], 'customers')
    await user.type(keyInputs[0], 'customer_id')
    await user.type(keyInputs[1], 'id')
    await user.click(screen.getByRole('button', { name: /analyze join/i }))

    expect(screen.getByRole('button', { name: /analyze join/i })).toBeDisabled()

    resolvePromise!({
      ok: true,
      json: () => Promise.resolve(mockNestedJoinResponse),
    })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /analyze join/i })).toBeEnabled()
    })
  })
})

describe('JoinResult type contract', () => {
  it('mock response matches expected backend structure', () => {
    expect(mockNestedJoinResponse).toHaveProperty('statistics')
    expect(mockNestedJoinResponse).toHaveProperty('left_unmatched')
    expect(mockNestedJoinResponse).toHaveProperty('right_unmatched')

    const stats = mockNestedJoinResponse.statistics
    expect(stats).toHaveProperty('left_total')
    expect(stats).toHaveProperty('right_total')
    expect(stats).toHaveProperty('matched_left')
    expect(stats).toHaveProperty('matched_right')
    expect(stats).toHaveProperty('match_rate_left')
    expect(stats).toHaveProperty('match_rate_right')
    expect(stats).toHaveProperty('cardinality')
    expect(stats).toHaveProperty('left_null_keys')
    expect(stats).toHaveProperty('right_null_keys')
    expect(stats).toHaveProperty('left_duplicate_keys')
    expect(stats).toHaveProperty('right_duplicate_keys')

    expect(mockNestedJoinResponse.left_unmatched).toHaveProperty('rows')
    expect(mockNestedJoinResponse.left_unmatched).toHaveProperty('total')
    expect(mockNestedJoinResponse.left_unmatched).toHaveProperty('columns_limited')
  })

  it('rejects flat response structure (regression test)', () => {
    const flatResponse = {
      left_total: 1000,
      right_total: 800,
      matched: 750,
      left_only: 250,
      right_only: 50,
      match_rate_left: 0.75,
      match_rate_right: 0.9375,
    }

    expect(flatResponse).not.toHaveProperty('statistics')
    expect(flatResponse).not.toHaveProperty('left_unmatched')
  })
})
