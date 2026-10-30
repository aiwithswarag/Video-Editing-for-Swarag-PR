# Swarag Video Director — pre-provisioned 42-effect rendering environment
#
# Build this on a machine/CI runner WITH network access. A runtime with blocked
# package downloads cannot bootstrap MediaPipe or the model/font dependencies.
# Only repository CODE and pinned public licensed assets go inside the image.
# Personal media, scripts and finished exports must never be baked into it.
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    OMP_NUM_THREADS=2 \
    OPENBLAS_NUM_THREADS=2

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates libgl1 libglib2.0-0 libegl1 libgles2 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/swarag-video-editor

# Image build includes full repo (filtered through .dockerignore); no GitHub
# checkout, pip or asset downloads are needed when the renderer starts.
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python tools/download_assets.py \
    && python -c "import cv2,mediapipe,numpy,PIL; print('MediaPipe/OpenCV available')" \
    && python scripts/produce_video.py catalog > /tmp/swarag-catalog.json \
    && python -c "import json; d=json.load(open('/tmp/swarag-catalog.json')); assert d['count']==42, d['count']"

# Production media is mounted at /workspace from the host or secure worker.
# Run as an unprivileged user; provisioning creates only the executable image.
RUN useradd --system --uid 10001 --create-home editor \
    && mkdir -p /workspace \
    && chown -R editor:editor /workspace /opt/swarag-video-editor

USER editor
VOLUME ["/workspace"]
CMD ["python", "scripts/produce_video.py", "catalog"]
