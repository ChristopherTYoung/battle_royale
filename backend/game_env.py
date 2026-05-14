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
            low=np.array([-1.0, -1.0, -1.0, -1.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32),
        )
        max_distance = np.sqrt((2 * 960)**2 + (2 * 540)**2)
        self.observation_space = spaces.Dict({
            'agent': spaces.Box(low=-1, high=1, shape=(2,), dtype=np.int32),
            'target': spaces.Box(low=-1, high=1, shape=(2,), dtype=np.int32),
            'agent_health': spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
            'target_health': spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
            'distance_to_player': spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
            'previous_distance': spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
            'aim_accuracy': spaces.Box(low=-1, high=1, shape=(1,), dtype=np.float32),
        })
        self.last_aim_direction = np.array([0, 0], dtype=np.float32)
        
    def _game_loop(self):
        pass
        
    def _get_obs(self):
        agent = self.enemies[self.id]
        agent_x, agent_y = agent.position
        target_x, target_y = self.player.position
        
        # Calculate aim accuracy from last action
        aim_dir = self.last_aim_direction
        player_dir = np.array([target_x - agent_x, target_y - agent_y], dtype=np.float32)
        aim_len = np.linalg.norm(aim_dir)
        player_len = np.linalg.norm(player_dir)
        if aim_len > 0 and player_len > 0:
            aim_accuracy = np.dot(aim_dir / aim_len, player_dir / player_len)
        else:
            aim_accuracy = 0.0
        
        return {
            'agent': np.array([agent_x / 960, agent_y / 540], dtype=np.float32), 
            'target': np.array([target_x / 960, target_y / 540], dtype=np.float32), 
            'agent_health': np.array([agent.health / 100], dtype=np.float32),
            'target_health': np.array([self.player.health / 100], dtype=np.float32),
            'distance_to_player': np.array([np.linalg.norm(np.array([target_x, target_y]) - np.array([agent_x, agent_y])) / self.max_distance], dtype=np.float32),
            'previous_distance': np.array([self.previous_distance / self.max_distance], dtype=np.float32),
            'aim_accuracy': np.array([aim_accuracy], dtype=np.float32),
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
        self.last_aim_direction = np.array([direction_x, direction_y], dtype=np.float32)
        self.update_enemy(self.id,
                          move_x, 
                          move_y, 
                          direction_x, 
                          direction_y, 
                          shoot = shoot > 0.5)
        enemy = self.enemies[self.id]
        current_distance = np.linalg.norm(np.array(self.player.position) - np.array(enemy.position))
        enemy = self.enemies[self.id]
        reward = 0

        # encourage survival
        reward += 0.01
        
        # Calculate dot product between aimed direction and player direction
        enemy_x, enemy_y = enemy.position
        player_x, player_y = self.player.position
        aim_direction = np.array([direction_x, direction_y])
        player_direction = np.array([player_x - enemy_x, player_y - enemy_y])

        aim_len = np.linalg.norm(aim_direction)
        player_len = np.linalg.norm(player_direction)
        
        if aim_len > 0 and player_len > 0:
            aim_direction /= aim_len
            player_direction /= player_len
            aim_accuracy = np.dot(aim_direction, player_direction)  # -1 to 1
        else:
            aim_accuracy = 0
            
        # Small penalty for complete inactivity
        if move_x == 0 and move_y == 0:
            reward -= 0.01  # Slight nudge to explore

        # Penalty for poor aim when NOT shooting
        if shoot <= 0.5 and aim_accuracy < 0.3:
            reward -= 0.02  # Encourage tracking target even when not engaged
            
        if current_distance < 100:
            reward += 0.1

        if shoot > 0.5:
            if aim_accuracy < 0.5:
                reward -= 0.15  # Penalty for wasting ammo
            elif aim_accuracy < 0.75:
                reward += 0.1  # Medium aim
            else:
                reward += 0.25  # Good aim (up to +0.25)
                
        # reward hits
        reward += 50 if self.player.health < self.previous_player_health else 0
        
        # reward kill
        reward += 200 if self.player.health == 0 else 0
        
        # punish death
        reward -= 100 if enemy.health == 0 else 0
        
        observation = self._get_obs()
        
        terminated = (
            self.player.health <= 0 or
            enemy.health <= 0
        )
        
        return observation, reward, terminated, False, {}
