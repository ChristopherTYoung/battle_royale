import gymnasium as gym

from stable_baselines3 import PPO
from game_env import GameEnv

game = GameEnv()

model = PPO("MlpPolicy", game, verbose=1)
model.learn(total_timesteps=100_000)
model.save("ppo_enemy")

obs, info = game.reset()
while True:
    action, _states = model.predict(obs)
    obs, rewards, terminated, truncated, info = game.step(action)