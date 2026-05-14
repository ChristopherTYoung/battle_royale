import threading
import time
import numpy as np
from stable_baselines3 import PPO


class Enemy:
    def __init__(self, id, game):
        self.game = game
        self.model = PPO.load("ppo_enemy")
        self.id = id
        self.running = True
        enemy = self.game.enemies[self.id]
        enemy_x, enemy_y = enemy.position
        player_x, player_y = self.game.player.position
        self.previous_distance = np.linalg.norm(np.array([player_x, player_y]) - np.array([enemy_x, enemy_y]))
        self.max_distance = np.sqrt((2 * 960)**2 + (2 * 540)**2)
        self.last_tick = 0
        self.decision_frequency = 6 
        self.last_aim_direction = np.array([0, 0], dtype=np.float32)
        self.loop_thread = threading.Thread(target=self.loop, daemon=True)
        self.loop_thread.start()
    
    def loop(self):
        """Main loop for enemy AI decision making"""
        time.sleep(2)
        while self.running:
            try:
                if self.game.tick_count - self.last_tick >= self.decision_frequency:
                    # Get current game state
                    if len(self.game.enemies) <= self.id:
                        self.stop()
                        break
                    enemy = self.game.enemies[self.id]
                    enemy_x, enemy_y = enemy.position
                    player_x, player_y = self.game.player.position

                    # Calculate current distance
                    current_distance = np.linalg.norm(np.array([player_x, player_y]) - np.array([enemy_x, enemy_y]))

                    # Calculate aim accuracy from last aim direction
                    aim_direction = self.last_aim_direction
                    player_direction = np.array([player_x - enemy_x, player_y - enemy_y], dtype=np.float32)
                    aim_len = np.linalg.norm(aim_direction)
                    player_len = np.linalg.norm(player_direction)
                    if aim_len > 0 and player_len > 0:
                        aim_accuracy = np.dot(aim_direction / aim_len, player_direction / player_len)
                    else:
                        aim_accuracy = 0.0

                    # Build normalized observation matching GameEnv format exactly
                    obs_dict = {
                        'agent': np.array([enemy_x / 960, enemy_y / 540], dtype=np.float32),
                        'target': np.array([player_x / 960, player_y / 540], dtype=np.float32),
                        'agent_health': np.array([enemy.health / 100], dtype=np.float32),
                        'target_health': np.array([self.game.player.health / 100], dtype=np.float32),
                        'distance_to_player': np.array([current_distance / self.max_distance], dtype=np.float32),
                        'previous_distance': np.array([self.previous_distance / self.max_distance], dtype=np.float32),
                        'aim_accuracy': np.array([aim_accuracy], dtype=np.float32),
                    }

                    # Get AI action from model
                    action, _states = self.model.predict(obs_dict, deterministic=True)

                    # Store aim direction for next observation calculation
                    self.last_aim_direction = np.array([action[2], action[3]], dtype=np.float32)

                    # Execute action in game
                    self.game.step(self.id, action)

                    # Update previous distance
                    self.previous_distance = current_distance
                    self.last_tick = self.game.tick_count
                
                time.sleep(0.001)
                
            except Exception as e:
                import traceback
                print(f"Error in enemy loop: {e}")
                traceback.print_exc()
                time.sleep(0.001)
    
    def stop(self):
        """Stop the enemy loop"""
        self.running = False