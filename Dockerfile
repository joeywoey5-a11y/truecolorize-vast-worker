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
      git ca-certificates curl libgomp1 && \
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
    fastapi==0.115.0 \
    uvicorn==0.30.6 \
    "aiohttp>=3.9,<4" \
    vastai

RUN git clone --depth 1 https://github.com/jantic/DeOldify.git /app/DeOldify && \
    rm -rf /app/DeOldify/.git

RUN sed -i \
    -e '/^import ffmpeg$/d' \
    -e '/^import yt_dlp as youtube_dl$/d' \
    -e '/^from IPython import display as ipythondisplay$/d' \
    -e '/^from IPython.display import HTML$/d' \
    -e '/^from IPython.display import Image as ipythonimage$/d' \
    /app/DeOldify/deoldify/visualize.py

# Artistic model only.
RUN mkdir -p /app/DeOldify/models && \
    python -c "import urllib.request; n='ColorizeArtistic_gen.pth'; urllib.request.urlretrieve('https://huggingface.co/spensercai/DeOldify/resolve/main/'+n,'/app/DeOldify/models/'+n)"

# Artistic DeOldify uses ResNet34; cache only that encoder.
RUN python -c "from torchvision import models; print('Caching ResNet34'); models.resnet34(weights=models.ResNet34_Weights.DEFAULT)"

RUN rm -rf /root/.cache/pip && \
    find /usr/local/lib/python3.10/site-packages -type d -name '__pycache__' -prune -exec rm -rf '{}' + || true && \
    find /app/DeOldify -type d -name '__pycache__' -prune -exec rm -rf '{}' + || true && \
    mkdir -p /workspace /var/log/truecolorize && \
    chmod 777 /workspace /var/log/truecolorize

CMD ["sh","-c","echo 'TrueColorize Vast Lite container ready'; exec tail -f /dev/null"]
