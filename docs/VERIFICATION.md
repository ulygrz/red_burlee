# Starter environment verification

Date: 2026-10-09. Executor: Linux x86_64, Python 3.12.14.

| Check | Result | Scope |
| --- | --- | --- |
| Devcontainer JSON parsing and relative build paths | Passed | All three profiles; not a Docker build |
| Python syntax and Ruff | Passed | Both smoke scripts |
| Isolated install of direct pinned development requirements | Passed | 62 resolved packages; Linux x86_64 CPU PyTorch |
| Dependency compatibility (`uv pip check`) | Passed | No incompatible installed dependencies |
| macOS ARM64 / Python 3.12 wheel-only dependency resolution | Passed | Resolver check only; no Mac execution |
| Linux ARM64 / Python 3.12 wheel-only dependency resolution | Passed | Resolver check only; no ARM execution |
| MuJoCo physics smoke check | Passed | MuJoCo 3.7.0; 1000 steps, 5 simulated seconds; finite state |
| PPO train/save/load smoke check | Passed | SB3 2.9.0, Gymnasium 1.2.3, Torch 2.11.0+cpu; 512 Pendulum steps; finite valid action |
| PlatformIO CLI startup | Passed | Core 6.1.18 |
| OSMesa offscreen render in this executor | Blocked | OSMesa system library absent; backend import cannot initialize GL |
| Dockerfile build on either architecture | Not run | No Docker executable/daemon available here |
| Native Mac viewer and MPS execution/performance | Not run | Requires the user's Mac |
| Upstream Fire/camera firmware builds and serial upload | Not run | Firmware projects and hardware revision verification required |
| Isaac Lab image pull, GPU startup and examples | Not run | Requires a compatible cloud host |
| BALA2 simulation, policy export, embedded inference and balance | Not implemented/tested | Outside environment scaffolding scope |

The Dockerfile installs `libosmesa6` and other graphics runtime libraries. That
declaration does not count as a successful renderer check; rerun
`python tools/check_sim.py --render` after the actual container build.

These smoke tests demonstrate working host libraries. They do not measure BALA2
training throughput, validate a robot physics model, or establish firmware control
timing. The direct pins are not a complete transitive or image lock. Record
platform-specific dependencies/image digests after the target checks pass.
