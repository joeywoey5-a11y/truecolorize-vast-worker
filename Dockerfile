FROM python:3.10-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NUMEXPR_MAX_THREADS=16 \
    PYTHONPATH=/app/DeOldify \
    TORCH_HOME=/app/torch-cache \
    SERVERLESS=true

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git ca-certificates curl wget libgomp1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade \
    pip==23.3.2 wheel==0.41.3 setuptools==70.3.0

RUN pip install --no-cache-dir \
    torch==2.0.1+cu118 \
    torchvision==0.15.2+cu118 \
    --extra-index-url https://download.pytorch.org/whl/cu118

RUN pip install --no-cache-dir \
    numpy==1.23.5 \
    fastai==1.0.60 \
    Pillow==9.3.0 \
    "tensorboardX>=1.6" \
    opencv-python-headless==4.8.1.78 \
    "requests>=2.28,<3" \
    fastapi==0.115.0 \
    uvicorn==0.30.6 \
    "aiohttp>=3.9,<4" \
    vastai

RUN git clone --depth 1 https://github.com/jantic/DeOldify.git /app/DeOldify && \
    rm -rf /app/DeOldify/.git

# Remove video/notebook-only imports from DeOldify's image runtime.
RUN sed -i \
    -e '/^import ffmpeg$/d' \
    -e '/^import yt_dlp as youtube_dl$/d' \
    -e '/^from IPython import display as ipythondisplay$/d' \
    -e '/^from IPython.display import HTML$/d' \
    -e '/^from IPython.display import Image as ipythonimage$/d' \
    /app/DeOldify/deoldify/visualize.py

# Bake DeOldify image model weights into the image.
RUN mkdir -p /app/DeOldify/models && \
    python -c "import urllib.request; names=['ColorizeArtistic_gen.pth','ColorizeStable_gen.pth']; [(print('Downloading',n), urllib.request.urlretrieve('https://huggingface.co/spensercai/DeOldify/resolve/main/'+n,'/app/DeOldify/models/'+n)) for n in names]"

# Cache torchvision backbones so first request does not download them.
RUN python -c "from torchvision import models; print('Caching ResNet34'); models.resnet34(weights=models.ResNet34_Weights.DEFAULT); print('Caching ResNet101'); models.resnet101(weights=models.ResNet101_Weights.DEFAULT)"

RUN mkdir -p /workspace /var/log/truecolorize && \
    chmod 777 /workspace /var/log/truecolorize

CMD ["sh","-c","echo 'TrueColorize Vast container ready'; exec tail -f /dev/null"]
