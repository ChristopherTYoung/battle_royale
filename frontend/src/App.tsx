import { useState, useEffect, useMemo, useRef } from 'react'
import { useGameClient } from './utils/useGameClient'
import {  createInputHandler } from './utils/input'
import { GameCanvas } from './components/GameCanvas'
import './App.css'

function App() {
  // Generate client ID once per session and keep it stable
  const clientId = useMemo(() => {
    // Try to get from sessionStorage, create if not exists
    let id = sessionStorage.getItem('gameClientId')
    if (!id) {
      id = `client-${Math.random().toString(36).slice(2, 11)}`
      sessionStorage.setItem('gameClientId', id)
    }
    return id
  }, [])

  const { gameState, isConnected, isLoading, error, sendInput } = useGameClient({
    serverUrl: 'ws://localhost:8000',
    clientId,
    autoConnect: true,
  })

  const [inputHandler] = useState(() => createInputHandler())
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  const canvasRef = useRef<HTMLCanvasElement>(null)

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

    // Send input at regular intervals (e.g., 120 times per second for snappy aiming)
    const interval = setInterval(() => {
      // Get canvas bounding rect for accurate coordinate conversion
      const canvas = canvasRef.current
      if (!canvas) return
      
      const rect = canvas.getBoundingClientRect()
      const canvasWidth = rect.width
      const canvasHeight = rect.height
      
      // Convert screen coordinates to canvas coordinates
      const canvasX = mousePos.x - rect.left
      const canvasY = mousePos.y - rect.top
      
      const gameMouseX = (canvasX / canvasWidth) * 1920 - 960
      const gameMouseY = (canvasY / canvasHeight) * 1080 - 540
      
      // Calculate direction from player to mouse in game coordinate space
      const dx = gameMouseX - gameState.player.pos[0]
      const dy = gameMouseY - gameState.player.pos[1]
      const dirLength = Math.sqrt(dx * dx + dy * dy)
      
      const direction_x = dirLength > 0 ? dx / dirLength : 0
      const direction_y = dirLength > 0 ? dy / dirLength : 0
      
      // Get movement input
      const movement = inputHandler.getInput(gameState.player.pos)
      
      // Combine with direction override
      const input = {
        ...movement,
        direction_x,
        direction_y,
      }
      sendInput(input)
    }, 1000 / 120) // 120 Hz for snappy aiming

    return () => clearInterval(interval)
  }, [isConnected, gameState, inputHandler, sendInput, mousePos])

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
          <GameCanvas ref={canvasRef} gameState={gameState} mousePos={mousePos} width={1920} height={1080} />
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
