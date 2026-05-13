import { useState, useEffect } from 'react'
import { useGameClient, createInputHandler } from './utils'
import { GameCanvas } from './components/GameCanvas'
import './App.css'

function App() {
  const { gameState, isConnected, isLoading, error, sendInput } = useGameClient({
    serverUrl: 'ws://localhost:8000',
    clientId: `client-${Date.now()}`,
    autoConnect: true,
  })

  const [inputHandler] = useState(() => createInputHandler())
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })

  // Track mouse position
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY })
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  useEffect(() => {
    if (!isConnected || !gameState) return

    // Send input at regular intervals (e.g., 60 times per second)
    const interval = setInterval(() => {
      const input = inputHandler.getInput(gameState.player.pos)
      sendInput(input)
    }, 1000 / 60) // 60 Hz

    return () => clearInterval(interval)
  }, [isConnected, gameState, inputHandler, sendInput])

  return (
    <div style={{ width: '100vw', height: '100vh', margin: 0, padding: 0, overflow: 'hidden', backgroundColor: '#000' }}>
      {/* Status overlay */}
      <div style={{ position: 'absolute', top: 10, left: 10, zIndex: 100, color: '#fff', fontSize: '14px' }}>
        {isLoading && <p style={{ color: '#ff0' }}>🔄 Connecting...</p>}
        {error && <p style={{ color: '#f00' }}>❌ Error: {error.message}</p>}
        {isConnected && <p style={{ color: '#0f0' }}>✓ Connected</p>}
      </div>

      {/* Game Canvas */}
      {gameState ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', height: '100%' }}>
          <GameCanvas gameState={gameState} mousePos={mousePos} width={1920} height={1080} />
        </div>
      ) : (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', height: '100%', color: '#fff', fontSize: '24px' }}>
          {isLoading ? '🎮 Loading game...' : '⏳ Waiting for game state...'}
        </div>
      )}
    </div>
  )
}

export default App
