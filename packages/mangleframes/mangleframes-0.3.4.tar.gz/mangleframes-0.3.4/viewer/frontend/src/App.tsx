import { Layout } from '@/components/layout/Layout'
import { useUIStore } from '@/stores/uiStore'
import { useEffect } from 'react'

function App() {
  const setConnected = useUIStore((s) => s.setConnected)

  useEffect(() => {
    console.log('[MangleFrames] Frontend initialized')
    setConnected(true)
  }, [setConnected])

  return <Layout />
}

export default App
