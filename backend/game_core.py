import time
import threading

import numpy as np

from actor import Actor

class GameCore:
    def __init__(self, tick_rate = 60):
        self.player = Actor()
        self.enemies = []
        self.projectiles = []
        self.tick_rate = tick_rate
        self.dt = 1 / tick_rate
        
        # Input buffer (updated by WebSocket, read by game loop)
        self.player_input = {'move_x': 0, 'move_y': 0, 'direction_x': 0, 'direction_y': 0, 'shooting': False}
        
        # Start game loop on separate thread
        self.running = True
        self.last_time = time.time()
        self.game_thread = threading.Thread(target=self._game_loop, daemon=True)
        self.game_thread.start()     
    
    def add_enemy(self, position, health = 100):
        next_id = len(self.enemies)
        enemy = Actor(id=next_id, position=position, health=health)
        
        self.enemies.append(enemy)
        return next_id
           
    def _update_player(self, move, direction, dt):     
        self.player.last_direction = direction
        self.player.position += move * self.player.speed * dt
        self.clamp_position(self.player)
        
    def update_enemy(self, id, move_x, move_y, direction_x, direction_y, shoot=False):
        direction = np.array(direction_x, direction_y)
        self.enemies[id].last_direction = direction
        self.enemies[id].position += np.array([move_x, move_y]) * self.enemies[id].speed
        self.clamp_position(self.enemies[id])
        
        if shoot:
            self.spawn_projectile(self.enemies[id], direction)
            
    def _player_shoot(self):
        if hasattr(self.player, 'last_direction'):
            self.spawn_projectile(self.player, self.player.last_direction)
            
    def spawn_projectile(self, actor, direction):
        projectile = {
            'position': actor.position.copy(),
            'direction': direction,
            'owner': actor,
            'speed': 500,
            'lifetime': 5,
            'age': 0
        }
        self.projectiles.append(projectile)
        
    def _update_projectiles(self, dt):
        for proj in self.projectiles[:]:
            proj['position'] += proj['direction'] * proj['speed'] * dt
            proj['age'] += dt
            if proj['age'] > proj['lifetime']:
                self.projectiles.remove(proj)
        
    def get_info(self):
        return { "player": self.player, "enemies": self.enemies }
    
    def _check_collisions(self):
        for proj in self.projectiles[:]:
            for enemy in self.enemies:
                dist = np.linalg.norm(proj['position'] - enemy.position)
                if dist < 10:
                    enemy.health -= 10
                    if proj in self.projectiles:
                        self.projectiles.remove(proj)
                    break
    
    def clamp_position(self, actor):
        actor.position[0] = np.clip(actor.position[0], -960, 960)
        actor.position[1] = np.clip(actor.position[1], -540, 540)
    
    def get_info(self):
        return {
            "player": {"position": self.player.position.tolist(), "health": self.player.health},
            "enemies": [enemy.position.tolist() for enemy in self.enemies],
            "projectiles": self.projectiles
        }
