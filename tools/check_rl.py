"""Short PPO check on Pendulum-v1, NOT robot training or an exported policy."""

from pathlib import Path

import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO


def main():
    out = Path("artifacts/toolchain-smoke")
    out.mkdir(parents=True, exist_ok=True)
    env = gym.make("Pendulum-v1")
    try:
        model = PPO(
            "MlpPolicy", env, device="cpu", seed=42,
            n_steps=128, batch_size=64, n_epochs=2,
            policy_kwargs={"net_arch": [32, 32]}, verbose=1,
        )
        model.learn(total_timesteps=512)
        model.save(out / "pendulum")
        loaded = PPO.load(out / "pendulum", device="cpu")
        obs, _ = env.reset(seed=42)
        action, _ = loaded.predict(obs, deterministic=True)
        assert np.isfinite(action).all()
        assert env.action_space.contains(action)
        print("PPO train/save/load passed. This policy is NOT deployable on BALA2.")
    finally:
        env.close()


if __name__ == "__main__":
    main()
