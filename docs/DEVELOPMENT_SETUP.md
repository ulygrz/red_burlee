# BALA2 Fire — Developer environment setup

Prepared 2026-10-09 against the supplied technical architecture, revision 0.1.

## 1. Recommended split

Use one repository with several environment profiles. The two simulators need
separate dependency environments and separate robot-model adapters.

| Environment | Runs where | Purpose | Hardware access |
| --- | --- | --- | --- |
| Local development devcontainer | Docker Desktop on Apple Silicon; Linux ARM64 | Protocol work, C++/Python tools, firmware builds, headless simulation, CPU PPO | No direct Mac USB; no Apple MPS GPU |
| Native Mac virtual environment | macOS ARM64 | MuJoCo viewer, local training, serial tools, firmware upload | Mac USB and native MPS where supported |
| Isaac Lab cloud devcontainer | Remote Linux x86_64 with supported NVIDIA RTX GPU | Batched headless simulation/training | NVIDIA GPU through Container Toolkit |
| Firmware build/release profile | Mac Docker or Linux CI | Repeatable ESP32 builds and firmware packaging | Upload runs on the host initially |
| Deployed robot | Fire ESP32 + camera ESP32-S3 + STM32 base | Estimation, balancing/inference, gateway and video | Firmware, no Docker runtime |

This refines the proposed development/deployment split: the second small image is
a release toolchain. A container is not deployed onto the ESP32. Browser assets
are served by the camera board and execute in the browser. The laptop and cloud
are not required while the deployed robot drives.

Prefer native MuJoCo for daily interactive simulation. The headless devcontainer
is useful for consistent checks and CPU jobs; it is not required for every
training run. If maintaining two local environments feels costly, keep native
MuJoCo plus a firmware/protocol container and defer the heavier local profile.

## 2. Assessment of the inspiration repository

Repository: https://github.com/ShawnHymel/reinforcement-learning-for-robotics

The current `Dockerfile.cpu` uses LinuxServer WebTop/XFCE, installs VS Code inside
the desktop, and installs CPU PyTorch, TensorFlow, MuJoCo, Gymnasium, Jupyter,
TensorBoard, and ONNX tooling. Its architecture check explicitly accepts `amd64`
and `arm64`. `Dockerfile.bare` is a smaller WebTop/Python starting point, not a
configured BALA2 firmware or Isaac Lab environment.

It is useful for running the course examples and inspecting the balance-bot
environment. It does not inherently fail because your Mac uses Apple Silicon.
Actual availability of its pinned image and binary packages still needs a build.
No build of the reference image was performed here.

For this project, reuse the ideas and inspect the model/environment code. Use a
smaller VS Code Dev Containers image for normal development; a browser desktop
duplicates the editor already running on your Mac and adds dependencies. Keep
TensorFlow, Jupyter, and ONNX out until a chosen workflow needs them. The supplied
image does not provide an Isaac Lab/CUDA environment or native Mac USB access.
The example robot's mass, geometry, actuator model, observations, and control
period must be adapted to the BALA2 Fire rather than assumed equivalent. Retain
upstream attribution/license requirements if copying code.

## 3. Install tools on the Mac

Install Docker Desktop **for Apple Silicon**, native VS Code, and these VS Code
extensions:

- Dev Containers: `ms-vscode-remote.remote-containers`
- Remote SSH: `ms-vscode-remote.remote-ssh` for the cloud workflow
- Python and C/C++ as desired on the native host

Install a native ARM64 Python 3.12 through your preferred manager. If you already
use Homebrew, this is one option:

```bash
brew install python@3.12
xcode-select --install
```

Run the Xcode installation command only if the command-line tools are absent.
Do not run the host terminal under Rosetta for this workflow.

From a **Mac terminal**, verify:

```bash
uname -m
python3.12 -c 'import platform; print(platform.machine(), platform.python_version())'
docker info
docker run --rm alpine uname -m
```

Expected: `arm64` on the Mac and `aarch64` in Linux. Do not add
`--platform linux/amd64` to the local build. An ARM64 Linux container is still
Linux: its libraries and virtual environments cannot be reused on macOS.

Start Docker with a modest CPU/RAM allocation and increase it if measurements
justify it. Reserve enough RAM for macOS and VS Code; the right allocation depends
on the Mac's installed memory, which has not been supplied.

## 4. Add the starter files to your repository

Copy the bundle contents to the existing repository root. Preserve any existing
`README.md`, `requirements`, `tools`, `.dockerignore`, and `.devcontainer` files;
merge or rename the starter entries where necessary. Merge
`gitignore-additions.txt` into the existing `.gitignore`, then discard that helper
file if desired.

Included paths:

```text
.devcontainer/local/devcontainer.json
.devcontainer/firmware/devcontainer.json
.devcontainer/isaac-cloud/devcontainer.json
containers/Dockerfile
requirements/{dev,sim,firmware}.txt
tools/check_sim.py
tools/check_rl.py
docs/DEVELOPMENT_SETUP.md
```

Keep the project architecture in `docs/TECHNICAL_ARCHITECTURE.md`. The starter does
not overwrite or revise the supplied architecture.

## 5. Start local container development

Open the **repository root** in VS Code. Run **Dev Containers: Reopen in
Container** and choose **BALA2 — Local development (CPU, headless)**. Opening the
repository root ensures the Docker build context and workspace mount are correct.
The first build installs the tools; later builds reuse layers.

The editor runs on the Mac; its language servers, terminal, and Python tools run
in the container. The Python interpreter is `/opt/venv/bin/python`. This keeps it
separate from native Mac virtual environments. PlatformIO uses the pinned CLI
directly; an extension-managed second PlatformIO installation is unnecessary.

In the **container terminal**:

```bash
uname -m
python -m pip check
pio --version
python tools/check_sim.py
python tools/check_sim.py --render
python tools/check_rl.py
```

The physics check uses a falling sphere; the PPO check uses Pendulum-v1. These
prove only that the toolchain can step physics and train/save/load a small policy.
They are not a BALA2 model, meaningful balance training, or robot acceptance tests.
The optional renderer uses Mesa/OSMesa software rendering. A renderer failure can
be investigated independently of non-rendering physics/training.

For TensorBoard, when a training script starts writing logs:

```bash
tensorboard --logdir runs --host 0.0.0.0 --port 6006
```

VS Code forwards port 6006 to your local browser. Port 8000 is reserved for a future
mock gateway/server; this bundle does not start one. Use localhost-only forwards.

Equivalent **Mac terminal** build, without VS Code:

```bash
docker build --target development -f containers/Dockerfile -t bala2-dev .
docker run --rm -it --shm-size=2g \
  -v "$PWD:/workspaces/bala2-rl" bala2-dev bash
```

## 6. Set up native MuJoCo on the Mac

Run these in a **Mac terminal**, from the repository root, not in the container:

```bash
python3.12 -m venv .venv-macos
source .venv-macos/bin/activate
python -m pip install -r requirements/dev.txt
python -m pip check
python tools/check_sim.py
python tools/check_rl.py
mjpython tools/check_sim.py --viewer
```

The passive MuJoCo viewer requires `mjpython` on macOS. Exit by closing the window.
Do not export the container's `MUJOCO_GL=osmesa` or `PYOPENGL_PLATFORM=osmesa` on
macOS; native rendering uses its own backend. If previously set, unset them in
the host shell before using the viewer.

For a separate host VS Code window, use **Python: Select Interpreter** to choose
`.venv-macos/bin/python`. Keep the container window on `/opt/venv/bin/python`.

Start state-based PPO with `device="cpu"`. A small MLP does not necessarily train
faster on the GPU, and ordinary MuJoCo physics stepping is separate from PyTorch
neural-network execution. Native PyTorch can use MPS, but this does not move the
MuJoCo solver to the Apple GPU. Benchmark MPS only after the CPU baseline works:

```bash
python -c 'import torch; print(torch.backends.mps.is_available())'
```

An `is_available()` result is not a performance test or proof that all policy
operations work on MPS. Record throughput and numerical behavior for your actual
environment/model before changing the training device.

## 7. Firmware builds and USB upload

Use PlatformIO + Arduino as the first **candidate**, consistent with spike SP-02.
Do not adopt it permanently until the upstream BALA2 baseline and the actual
camera example both build and boot. Native ESP-IDF remains an alternative if that
spike finds concrete framework incompatibilities.

Start with two independent firmware projects:

- `firmware/bala2/` for Fire control and the existing STM32-base interface
- `firmware/camera/` for the selected camera gateway

Candidate PlatformIO board IDs are `m5stack-fire` and, if you buy the proposed
XIAO ESP32-S3 Sense, `seeed_xiao_esp32s3`. The base XIAO board ID alone does not
configure the camera, PSRAM mode, sensor pins, partition layout, or USB console.
Verify these against the purchased revision. Pin the tested Espressif platform,
framework, and library revisions in each `platformio.ini`; pinning PlatformIO
Core by itself does not freeze the firmware toolchain.

This bundle intentionally supplies no guessed production `platformio.ini` or
motor-control firmware. First reproduce the upstream build using SP-01/SP-02.
Once those projects exist, build in either local profile:

```bash
pio run -d firmware/bala2
pio run -d firmware/camera
```

For the small build profile without RL packages:

```bash
docker build --target firmware -f containers/Dockerfile -t bala2-firmware-tools .
docker run --rm -it -v "$PWD:/workspaces/bala2-rl" \
  bala2-firmware-tools pio run -d firmware/bala2
```

Docker Desktop does not support direct USB passthrough. Do not mount a Mac
`/dev/cu.*` path into Linux and expect it to become a usable serial device.
Initially use the native Mac environment to build/upload together:

```bash
source .venv-macos/bin/activate
pio device list
pio run -d firmware/bala2 -t upload --upload-port /dev/cu.YOUR_ACTUAL_FIRE_PORT
pio device monitor --port /dev/cu.YOUR_ACTUAL_FIRE_PORT --baud 115200
```

Replace the placeholder port with the detected port. This standard PlatformIO
upload command may rebuild natively; it does **not** promise to flash the exact
binary built in Linux. Avoid concurrent native/container builds into the same
`.pio` directory. For later exact-artifact releases, package the container-built
bootloader, partitions, application and recorded flash offsets, then use the
matching host upload tool. Do not guess offsets or copy only an application binary
and assume a complete flash image. USB/IP can be explored later if needed.

Policy export is a separate step before firmware packaging. Include observation
order/units/normalization/clipping, deterministic action mapping, control period,
calibration compatibility, checksums and fixed numerical test vectors. An SB3 ZIP
or desktop ONNX file is not automatically an ESP32 inference implementation.
Choose and benchmark the embedded format/runtime in SP-11 before adding exporter
dependencies. Do not change STM32 firmware as part of container setup.

## 8. Isaac Lab cloud setup

Use an **x86_64 Linux host with a supported RTX GPU**, Docker Engine, Docker
Compose and NVIDIA Container Toolkit. Choose the cloud hardware only after
checking the pinned Isaac Sim requirements. A GPU with CUDA support alone is not
enough: the standard Isaac Sim 5.1 stack does not support GPUs without RT cores,
including A100/H100. Use the compatibility checker before a long paid run. Plan
around at least 32 GB RAM and 16 GB VRAM as the documented baseline, with extra
headroom for training, parallel environments and cameras. Exact instance sizing
needs a benchmark; no provider or instance was selected here.

This starter pins `nvcr.io/nvidia/isaac-lab:2.3.2`, paired with Isaac Sim 5.1/Python
3.11. It is a documented release baseline, not a claim to be the latest release.
Development-branch documentation now describes a different Sim/Python stack;
do not mix those instructions or copy its dependencies into this image. The
prebuilt image is intended for **headless** use. For GUI/remote visualization,
build the full upstream image for the same tagged release instead.

Connect with **Remote SSH** from Mac VS Code. Clone your project onto the **remote
host** and open that remote repository root. Docker must run on the cloud host;
do not start the cloud profile against the Mac's Docker daemon. On the remote host:

```bash
uname -m
nvidia-smi
docker info
docker compose version
docker pull nvcr.io/nvidia/isaac-lab:2.3.2
```

Install/configure the host NVIDIA driver and Container Toolkit using their
official documentation; a Dockerfile cannot install a usable host GPU driver.
Follow registry login instructions if your account requires authentication.

Review NVIDIA's license and privacy settings before launch. The cloud profile
reads `ACCEPT_EULA` and `PRIVACY_CONSENT` from the remote VS Code environment.
After accepting the license, make `ACCEPT_EULA=Y` available there, or change that
profile's `ACCEPT_EULA` value to the literal `Y`. Set `PRIVACY_CONSENT` according
to your choice and the release's documented behavior. These are intentionally
not preaccepted in the starter. Shell exports in an unrelated terminal may not
reach an already-running VS Code remote server; setting the values explicitly in
the remote profile avoids that ambiguity.

In the remote window, run **Dev Containers: Reopen in Container**, select
**BALA2 — Isaac Lab cloud GPU (headless only)**. In its terminal:

```bash
nvidia-smi
cd /workspace/IsaacLab
./isaaclab.sh -p scripts/tutorials/00_sim/log_time.py --headless
./isaaclab.sh -p scripts/environments/zero_agent.py \
  --task Isaac-Cartpole-Direct-v0 --num_envs 16 --headless
```

Stop the interactive zero-agent example after confirming that physics advances
without GPU errors. The bundled image's documented upstream checkout is
`/workspace/IsaacLab`; a locally built upstream image may use
`/workspace/isaaclab`. Use the release's `isaaclab.sh -p` interpreter for project
scripts, not a newly created local Python 3.12 environment.

Do **not** install `requirements/dev.txt` into Isaac Lab. Its PyTorch, CUDA,
Gymnasium, NumPy and simulator versions are coupled to that release. When project
code exists, install only the project-specific additions through its interpreter
with constraints that preserve the image's supplied dependency versions.

The project is mounted at `/workspaces/bala2-rl`. Write logs/checkpoints there on
the remote host's durable data disk, or use another explicit persistent mount.
Named volumes in the profile preserve shader caches only; they do not back up
checkpoints or survive deletion of the cloud VM/disk. Copy completed artifacts to
durable storage before terminating an instance. Start with the upstream example,
then an external BALA2 task; do not modify upstream Isaac Lab just to hold project
code. Pin the upstream tag/commit if building a custom image.

## 9. Keep the simulation contract consistent

MuJoCo MJCF and Isaac USD/PhysX assets are separate implementations. Sharing a
repository or training library does not make their dynamics equivalent. Use a
common specification for measured dimensions, inertia, wheel spacing/radius,
motor dead zone/saturation, battery effects, sensor filtering and delays.

Share the ordered observation/action contract, reference commands, SI units,
normalization, deterministic actor semantics, termination criteria, and the
policy interface. Keep simulator-specific imports/models under separate adapters.
Start with the architecture's proposed 5 ms control interval, validate it in
SP-05, and choose a physics timestep that is an integer subdivision. Match action
holding/decimation and sensor timing across both simulators and the Fire.

First get the conventional controller and actuator identification working, then
implement the BALA2 MuJoCo environment and one small policy. Add Isaac Lab after
the contract stabilizes and a throughput/experiment requirement justifies it.
Treat sim-to-sim transfer as an evaluation task: compare fixed initial states,
controller responses and exported-policy rollouts. Do not expect to resume an SB3
training ZIP in another RL framework automatically. An exported deterministic
actor can be shared only with its normalization and action postprocessing intact.

## 10. Environment spikes and reproducibility

Extend SP-02 and SP-12 with these checks:

| Check | Evidence | Decision |
| --- | --- | --- |
| Mac ARM64 native MuJoCo + viewer | Versions, physics/viewer results | Native interactive workflow |
| Local ARM64 container | Build log, pip check, physics/PPO result | Container dependency compatibility |
| Local software rendering | Frame result and latency | Whether offscreen container rendering is useful |
| Native CPU vs MPS PPO | Steps/s, update time, numerical behavior | Training device |
| Upstream Fire and camera builds | Exact platform/framework/libs, boot output | Firmware framework |
| Mac serial upload | Detected board/port, upload and monitor logs | Host upload workflow |
| Cloud GPU example | Image digest, driver/GPU IDs, simulation result | Compatible cloud environment |
| BALA2 cross-simulator comparison | Controller response/rollout differences | Transfer readiness |

After each environment passes, capture its resolved dependencies separately:

```bash
mkdir -p docs/environments
python -m pip freeze > docs/environments/REPLACE_WITH_ENVIRONMENT_NAME.txt
```

Use different names for macOS ARM64, Linux ARM64 and cloud CUDA. A freeze from
one environment is not a universal cross-platform lockfile. Add a proper
platform-aware lock workflow when project packaging stabilizes. Record Python,
OS/CPU, code revision, image digest, hardware/calibration revision, simulator
version, seed and policy metadata with runs. Tags and direct pins improve
repeatability but do not freeze base images, apt packages or transitive Python
dependencies; resolve these before claiming a fully reproducible release.

For local image provenance, from the host:

```bash
docker image inspect python:3.12-slim-bookworm --format '{{json .RepoDigests}}'
```

Update the Dockerfile to the validated multi-architecture digest rather than an
architecture-specific digest if you intend to support both Linux CPU types.

## 11. Verification performed for this bundle

See `VERIFICATION.md` beside this document for results. The current executor is
Linux, not your Mac or an NVIDIA cloud host. Docker image builds, native Mac viewer,
USB upload, cloud GPU execution and physical robot checks cannot be claimed from
host-side checks here. Unperformed target checks remain pending.

## 12. Sources checked

- Reference repository: https://github.com/ShawnHymel/reinforcement-learning-for-robotics
- Reference CPU Dockerfile: https://github.com/ShawnHymel/reinforcement-learning-for-robotics/blob/main/Dockerfile.cpu
- MuJoCo Python/viewer: https://mujoco.readthedocs.io/en/stable/python.html
- Apple PyTorch/MPS: https://developer.apple.com/metal/pytorch/
- SB3 PPO CPU guidance: https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html
- Docker Mac install: https://docs.docker.com/desktop/setup/install/mac-install/
- Docker USB limitations: https://docs.docker.com/desktop/troubleshoot-and-support/faqs/general/
- Docker GPU support scope: https://docs.docker.com/desktop/features/gpu/
- VS Code devcontainers: https://code.visualstudio.com/docs/devcontainers/containers
- VS Code remote Docker: https://code.visualstudio.com/remote/advancedcontainers/develop-remote-host
- Isaac Lab pinned Docker guide: https://isaac-sim.github.io/IsaacLab/v2.3.2/source/deployment/docker.html
- Isaac Lab 2.3 installation: https://isaac-sim.github.io/IsaacLab/v2.3.0/source/setup/installation/index.html
- Isaac Sim 5.1 requirements: https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html
- NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
- PlatformIO Fire: https://docs.platformio.org/en/latest/boards/espressif32/m5stack-fire.html
- PlatformIO XIAO S3: https://docs.platformio.org/en/latest/boards/espressif32/seeed_xiao_esp32s3.html

Source facts and proposed project choices are distinguished above. Dependency pins
are an initial candidate rather than a requirement to use the newest release.
