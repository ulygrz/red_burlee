FROM python:3.12-slim-bookworm AS firmware

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=$VIRTUAL_ENV/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 --shell /bin/bash developer \
    && python -m venv /opt/venv
COPY requirements/ /opt/requirements/
RUN python -m pip install -r /opt/requirements/firmware.txt \
&& chown -R developer:developer /opt/venv

USER developer
WORKDIR /workspaces/bala2-rl
CMD ["bash"]

FROM firmware AS development
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    bosmesa6 libgl1 libegl1 lubflfw3 libglib2.0-0  libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN if [ "$(uname -m)" = "x86_64" ]; then \
        python -m pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu; \
    fi \
    && python -m pip install -r /opt/requirements/dev.txt \
    && chown -R developer:developer /opt/venv

ENV MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa
USER developer