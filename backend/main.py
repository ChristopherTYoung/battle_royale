import asyncio

from fastapi import FastAPI, WebSocket

from backend.game import Game

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
        ]
    }
    return state

@app.websocket("/game/{client_id}")
async def game_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    
    game = Game()
    game.add_enemies(count=5)  # Add enemies
    games[client_id] = game
    
    # Send state at 30 Hz (every 33ms)
    STATE_SEND_RATE = 1 / 30  # seconds
    last_send = asyncio.get_event_loop().time()
    
    async def send_state_loop():
        nonlocal last_send
        while client_id in games:
            now = asyncio.get_event_loop().time()
            if now - last_send >= STATE_SEND_RATE:
                state = build_state(game)
                await websocket.send_json(state)
                last_send = now
            await asyncio.sleep(0.001)
    
    try:            
        # Run both input receiving and state sending concurrently
        send_task = asyncio.create_task(send_state_loop())
        while True:
            # Receive player input
            data = await websocket.receive_json()
            game.action(data["move_x"], data["move_y"], 
                       data["direction_x"], data["direction_y"], 
                       data["shooting"])
    finally:
        send_task.cancel()
        del games[client_id]