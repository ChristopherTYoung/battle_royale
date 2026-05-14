import threading
import time

from actor import Actor
from game_core import GameCore
import gymnasium as gym
from gymnasium import spaces

import numpy as np

class GameEnv(GameCore, gym.Env):
    def __init__(self, tick_rate=60):
        super().__init__(tick_rate)
        self.previous_distance = 100
        self.position = [0, 100]
        self.previous_player_health = self.player.health
        self.max_distance = np.sqrt((2 * 960)**2 + (2 * 540)**2)
        self.previous_health = 100
        self.id = self.add_enemy(self.position, self.previous_health)
        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(5,),
            dtype=np.float32
        )
        max_distance = np.sqrt((2 * 960)**2 + (2 * 540)**2)
        self.observation_space = spaces.Dict({
            'agent': spaces.Box(low=-1, high=1, shape=(2,), dtype=np.int32),
            'target': spaces.Box(low=-1, high=1, shape=(2,), dtype=np.int32),
            'agent_health': spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
            'target_health': spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
            'distance_to_player': spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
            'previous_distance': spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
        })
        
    def _game_loop(self):
        pass
        
    def _get_obs(self):
        agent = self.enemies[self.id]
        agent_x, agent_y = agent.position
        target_x, target_y = self.player.position
        
        return {
            'agent': np.array([agent_x / 960, agent_y / 540], dtype=np.float32), 
            'target': np.array([target_x / 960, target_y / 540], dtype=np.float32), 
            'agent_health': np.array([agent.health / 100], dtype=np.float32),
            'target_health': np.array([self.player.health / 100], dtype=np.float32),
            'distance_to_player': np.array([np.linalg.norm(np.array([target_x, target_y]) - np.array([agent_x, agent_y])) / self.max_distance], dtype=np.float32),
            'previous_distance': np.array([self.previous_distance / self.max_distance], dtype=np.float32),
            }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.player = Actor()
        self.enemies = []
        self.projectiles = []
        
        # Input buffer (updated by WebSocket, read by game loop)
        self.player_input = {'move_x': 0, 'move_y': 0, 'direction_x': 0, 'direction_y': 0, 'shooting': False}
        self.position = self.np_random.integers(-960, 960, size=2, dtype=int)
        self.previous_distance = np.linalg.norm(np.array(self.player.position) - np.array(self.position))
        self.previous_health = 100
        self.previous_player_health = self.player.health
        self.id = self.add_enemy(self.position, self.previous_health)
        
        # Start game loop on separate thread
        self.running = True
        self.last_time = time.time()
        self.game_thread = threading.Thread(target=self._game_loop, daemon=True)
        self.game_thread.start()
        
        return self._get_obs(), {}     
        
    def step(self, action):
        move_x, move_y, direction_x, direction_y, shoot = action
        self.update_enemy(self.id,
                          move_x, 
                          move_y, 
                          direction_x, 
                          direction_y, 
                          shoot = 1 if shoot > 0.5 else 0)
        enemy = self.enemies[self.id]
        current_distance = np.linalg.norm(np.array(self.player.position) - np.array(enemy.position))
        enemy = self.enemies[self.id]
        reward = 0

        # encourage survival
        reward += 0.01
        
        # encourage approaching player
        reward += (self.previous_distance - current_distance) / self.max_distance
        
        # reward hits
        reward += 10 if self.player.health < self.previous_player_health else 0
        
        # reward kill
        reward += 100 if self.player.health == 0 else 0
        
        # punish death
        reward -= 100 if enemy.health == 0 else 0
        
        observation = self._get_obs()
        
        terminated = (
            self.player.health <= 0 or
            enemy.health <= 0
        )
        
        return observation, reward, terminated, False, {}
