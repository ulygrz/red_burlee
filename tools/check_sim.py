"""Check the simulator toolchain; this model is NOT a BALA2 model."""

import argparse
import importlib.metadata
import platform
import time

import mujoco
import numpy as np
import torch

XML = """<mujoco model="toolchain-smoke-only">
  <option timestep="0.005"/>
  <worldbody>
    <light pos="0 0 3"/>
    <geom type="plane" size="2 2 0.1"/>
    <body pos="0 0 1">
      <freejoint/>
      <geom type="sphere" size="0.1" mass="1"/>
    </body>
  </worldbody>
</mujoco>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="Check offscreen rendering")
    parser.add_argument("--viewer", action="store_true", help="Native Mac: use mjpython")
    args = parser.parse_args()
    print("Host:", platform.system(), platform.machine(), platform.python_version())
    for package in ("mujoco", "gymnasium", "torch", "stable-baselines3"):
        print(package, importlib.metadata.version(package))
    print("MPS available:", torch.backends.mps.is_available())
    print("CUDA available:", torch.cuda.is_available())
    assert float((torch.ones(4) * 2).sum()) == 8.0
    model = mujoco.MjModel.from_xml_string(XML)
    data = mujoco.MjData(model)
    start = time.perf_counter()
    for _ in range(1000):
        mujoco.mj_step(model, data)
    elapsed = time.perf_counter() - start
    assert np.isfinite(data.qpos).all()
    assert abs(data.time - 5.0) < 1e-6
    print(f"1000 physics steps: {elapsed:.4f}s; simulated {data.time:.3f}s")
    if args.render:
        with mujoco.Renderer(model, height=120, width=160) as renderer:
            renderer.update_scene(data)
            frame = renderer.render()
            assert frame.shape == (120, 160, 3)
            print("Offscreen frame:", frame.shape)
    if args.viewer:
        from mujoco import viewer as mj_viewer

        mujoco.mj_resetData(model, data)
        with mj_viewer.launch_passive(model, data) as viewer:
            while viewer.is_running():
                step_start = time.perf_counter()
                mujoco.mj_step(model, data)
                viewer.sync()
                time.sleep(max(0.0, model.opt.timestep - (time.perf_counter() - step_start)))
    print("Toolchain smoke check passed. BALA2 model and hardware remain unvalidated.")


if __name__ == "__main__":
    main()
