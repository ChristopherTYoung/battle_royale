import asyncio

from fastapi import FastAPI, WebSocket

from game import Game

app = FastAPI()

games = {}

def build_state(game):
    state = {
        "player": {"pos": game.player.position.tolist(), 
                  "health": game.player.health},
        "enemies": [
            {"id": e.id, "pos": e.position.tolist(), 
             "health": e.health}
            for e in game.enemies
        ],
        "projectiles": [
            {"pos": proj.position.tolist(), 
             "direction": proj.direction.tolist()}
            for proj in game.projectiles
        ]
    }
    return state

@app.websocket("/game/{client_id}")
async def game_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    
    # Create game for this client if it doesn't exist
    if client_id not in games:
        game = Game()
        game.add_enemies(count=1)
        games[client_id] = game
    else:
        game = games[client_id]
    
    # Send state at 30 Hz (every 33ms)
    STATE_SEND_RATE = 1 / 30  # seconds
    last_send = asyncio.get_event_loop().time()
    
    async def send_state_loop():
        nonlocal last_send
        try:
            while client_id in games:
                now = asyncio.get_event_loop().time()
                if now - last_send >= STATE_SEND_RATE:
                    state = build_state(game)
                    await websocket.send_json(state)
                    last_send = now
                await asyncio.sleep(0.001)
        except Exception as e:
            print(f"Send loop error: {e}")
    
    try:            
        # Run both input receiving and state sending concurrently
        send_task = asyncio.create_task(send_state_loop())
        while True:
            try:
                # Receive player input
                data = await websocket.receive_json()
                game.action(data.get("move_x", 0), data.get("move_y", 0), 
                           data.get("direction_x", 0), data.get("direction_y", 0), 
                           data.get("shooting", False))
            except Exception as e:
                print(f"Input handling error: {e}")
                break
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        send_task.cancel()
        if client_id in games:
            del games[client_id]