# red_burlee
Reinforcement learning for the M5Stack BALA2 Fire self-balancing robot, with browser-based driving controls and live video streaming from an ESP32-S3 camera.


Profiles:

- `.devcontainer/local/`: Python/C++/PlatformIO and headless MuJoCo/PPO on CPU.
- `.devcontainer/firmware/`: smaller firmware build/release toolchain.
- `.devcontainer/isaac-cloud/`: NVIDIA Isaac Lab 2.3.2, headless, remote Linux GPU only.

## MacOS development
I use a separate native .venv-macos for interactive MuJoCo and USB flashing.