import { useEffect, useRef, forwardRef } from 'react'
import type { GameState } from '../utils/websocket'

interface GameCanvasProps {
  gameState: GameState | null
  mousePos: { x: number; y: number }
  width?: number
  height?: number
}

// Direction constants
type Direction = 'north' | 'south' | 'side' | 'diagup' | 'diagdown'

function getDirection(dx: number, dy: number): Direction {
  const length = Math.sqrt(dx * dx + dy * dy)
  if (length === 0) return 'south' 

  const nx = dx / length
  const ny = dy / length
  
  const angle = Math.atan2(ny, nx)
  const degrees = (angle * 180) / Math.PI

  const normalizedDegrees = (degrees + 360) % 360

  if (normalizedDegrees < 22.5 || normalizedDegrees >= 337.5) {
    return 'side' // Right
  } else if (normalizedDegrees < 67.5) {
    return 'diagdown' // Down-right or up-right
  } else if (normalizedDegrees < 112.5) {
    return 'south' // Down
  } else if (normalizedDegrees < 157.5) {
    return 'diagdown' // Down-left
  } else if (normalizedDegrees < 202.5) {
    return 'side' // Left
  } else if (normalizedDegrees < 247.5) {
    return 'diagup' // Up-left
  } else if (normalizedDegrees < 292.5) {
    return 'north' // Up
  } else {
    return 'diagup' // Up-right
  }
}

export const GameCanvas = forwardRef<HTMLCanvasElement, GameCanvasProps>(function GameCanvas({
  gameState,
  mousePos,
  width = 1920,
  height = 1080,
}, ref) {
  const assetsRef = useRef<{
    player?: HTMLImageElement
    cursor?: HTMLImageElement
    gun?: HTMLImageElement
    bullet?: HTMLImageElement
    enemies: Map<string, HTMLImageElement>
  }>({
    enemies: new Map(),
  })

  // Load assets
  useEffect(() => {
    const assets = assetsRef.current

    // Load player sprite
    const playerImg = new Image()
    playerImg.src = '/assets/player/p1.png'
    playerImg.onload = () => {
      assets.player = playerImg
    }

    // Load cursor
    const cursorImg = new Image()
    cursorImg.src = '/assets/player/1crosshair2.png'
    cursorImg.onload = () => {
      assets.cursor = cursorImg
    }

    // Load gun (use first available p* file)
    const gunImg = new Image()
    gunImg.src = '/assets/player/p1.png' // Adjust if guns have different names
    gunImg.onload = () => {
      assets.gun = gunImg
    }

    // Load bullet
    const bulletImg = new Image()
    bulletImg.src = '/assets/player/bulletb.png'
    bulletImg.onload = () => {
      assets.bullet = bulletImg
    }

    // Load directional enemy sprites
    const directions: Direction[] = ['north', 'south', 'side', 'diagup', 'diagdown']
    directions.forEach((dir) => {
      const enemyImg = new Image()
      enemyImg.src = `/assets/enemy/3_${dir}.png`
      enemyImg.onload = () => {
        assets.enemies.set(dir, enemyImg)
      }
    })
  }, [])

  // Render canvas
  useEffect(() => {
    const canvas = ref as any
    if (!canvas?.current || !gameState) return

    const canvasEl = canvas.current
    const ctx = canvasEl.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.fillStyle = '#000'
    ctx.fillRect(0, 0, width, height)

    const assets = assetsRef.current
    const SPRITE_SIZE = 32
    const BULLET_SIZE = 8

    // Draw background grid (optional, for debugging)
    ctx.strokeStyle = '#333'
    ctx.lineWidth = 1
    for (let x = 0; x < width; x += 100) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, height)
      ctx.stroke()
    }
    for (let y = 0; y < height; y += 100) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(width, y)
      ctx.stroke()
    }

    // Convert game coordinates to screen coordinates
    const gameToScreen = (pos: [number, number]): [number, number] => {
      return [
        (pos[0] + 960) * (width / 1920),
        (pos[1] + 540) * (height / 1080),
      ]
    }

    // Draw player
    const [screenX, screenY] = gameToScreen(gameState.player.pos)
    
    if (assets.player) {
      ctx.drawImage(
        assets.player,
        screenX - SPRITE_SIZE / 2,
        screenY - SPRITE_SIZE / 2,
        SPRITE_SIZE,
        SPRITE_SIZE
      )
    } else {
      // Fallback: draw blue circle if image not loaded
      ctx.fillStyle = '#00f'
      ctx.beginPath()
      ctx.arc(screenX, screenY, SPRITE_SIZE / 2, 0, Math.PI * 2)
      ctx.fill()
    }

    // Draw player health bar
    ctx.fillStyle = '#f00'
    ctx.fillRect(screenX - 20, screenY - 30, 40, 5)
    ctx.fillStyle = '#0f0'
    const healthPercent = gameState.player.health / 100
    ctx.fillRect(screenX - 20, screenY - 30, 40 * healthPercent, 5)

    // Draw gun pointing towards cursor
    if (assets.gun) {
      const angle = Math.atan2(
        mousePos.y - screenY,
        mousePos.x - screenX
      )
      ctx.save()
      ctx.translate(screenX, screenY)
      ctx.rotate(angle)
      ctx.drawImage(assets.gun, -8, -8, 16, 16)
      ctx.restore()
    }

    // Draw enemies
    gameState.enemies.forEach((enemy) => {
      const [screenX, screenY] = gameToScreen(enemy.pos)
      
      // Determine enemy direction relative to player
      const dx = gameState.player.pos[0] - enemy.pos[0]
      const dy = gameState.player.pos[1] - enemy.pos[1]
      const direction = getDirection(dx, dy)
      
      let enemyImg = assets.enemies.get(direction)

      if (enemyImg) {
        ctx.drawImage(
          enemyImg,
          screenX - SPRITE_SIZE / 2,
          screenY - SPRITE_SIZE / 2,
          SPRITE_SIZE,
          SPRITE_SIZE
        )
      } else {
        // Fallback: draw colored circle
        ctx.fillStyle = '#f00'
        ctx.beginPath()
        ctx.arc(screenX, screenY, SPRITE_SIZE / 2, 0, Math.PI * 2)
        ctx.fill()
      }

      // Draw enemy health bar
      ctx.fillStyle = '#f00'
      ctx.fillRect(screenX - 20, screenY - 30, 40, 5)
      ctx.fillStyle = '#0f0'
      const healthPercent = enemy.health / 100
      ctx.fillRect(screenX - 20, screenY - 30, 40 * healthPercent, 5)
    })

    // Draw projectiles
    gameState.projectiles.forEach((projectile) => {
      const [screenX, screenY] = gameToScreen(projectile.pos)

      if (assets.bullet) {
        ctx.drawImage(
          assets.bullet,
          screenX - BULLET_SIZE / 2,
          screenY - BULLET_SIZE / 2,
          BULLET_SIZE,
          BULLET_SIZE
        )
      } else {
        // Fallback: draw yellow circle
        ctx.fillStyle = '#ff0'
        ctx.beginPath()
        ctx.arc(screenX, screenY, BULLET_SIZE / 2, 0, Math.PI * 2)
        ctx.fill()
      }
    })

    // Draw cursor
    if (assets.cursor) {
      ctx.drawImage(
        assets.cursor,
        mousePos.x - 16,
        mousePos.y - 16,
        32,
        32
      )
    } else {
      // Fallback: draw crosshair
      ctx.strokeStyle = '#0f0'
      ctx.lineWidth = 2
      const size = 10
      ctx.beginPath()
      ctx.moveTo(mousePos.x - size, mousePos.y)
      ctx.lineTo(mousePos.x + size, mousePos.y)
      ctx.moveTo(mousePos.x, mousePos.y - size)
      ctx.lineTo(mousePos.x, mousePos.y + size)
      ctx.stroke()
    }

    // Draw game info
    ctx.fillStyle = '#fff'
    ctx.font = '16px Arial'
    ctx.fillText(`Health: ${gameState.player.health}`, 10, 20)
    ctx.fillText(`Enemies: ${gameState.enemies.length}`, 10, 40)
    ctx.fillText(`Bullets: ${gameState.projectiles.length}`, 10, 60)
  }, [gameState, mousePos, width, height, ref])

  return (
    <canvas
      ref={ref}
      width={width}
      height={height}
      style={{
        border: '2px solid #fff',
        cursor: 'none',
        display: 'block',
      }}
    />
  )
})
