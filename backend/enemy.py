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
        self.loop_thread = threading.Thread(target=self.loop, daemon=True)
        self.loop_thread.start()
    
    def loop(self):
        """Main loop for enemy AI decision making"""
        time.sleep(5)
        while self.running:
            try:
                if self.game.tick_count - self.last_tick >= self.decision_frequency:
                    # Get current game state
                    enemy = self.game.enemies[self.id]
                    if enemy.health <= 0:
                        self.stop()
                        break
                    enemy_x, enemy_y = enemy.position
                    player_x, player_y = self.game.player.position

                    # Calculate current distance
                    current_distance = np.linalg.norm(np.array([player_x, player_y]) - np.array([enemy_x, enemy_y]))

                    # Build normalized observation matching GameEnv format exactly
                    obs_dict = {
                        'agent': np.array([enemy_x / 960, enemy_y / 540], dtype=np.float32),
                        'target': np.array([player_x / 960, player_y / 540], dtype=np.float32),
                        'agent_health': np.array([enemy.health / 100], dtype=np.float32),
                        'target_health': np.array([self.game.player.health / 100], dtype=np.float32),
                        'distance_to_player': np.array([current_distance / self.max_distance], dtype=np.float32),
                        'previous_distance': np.array([self.previous_distance / self.max_distance], dtype=np.float32),
                    }

                    # Get AI action from model
                    action, _states = self.model.predict(obs_dict, deterministic=True)

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