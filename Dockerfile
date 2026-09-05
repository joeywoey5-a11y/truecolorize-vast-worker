FROM python:3.10-slim-bookworm
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NUMEXPR_MAX_THREADS=16 PYTHONPATH=/app/DeOldify TORCH_HOME=/app/torch-cache SERVERLESS=true
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates curl wget libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN python -m pip install --no-cache-dir --upgrade pip==23.3.2 wheel==0.41.3 setuptools==70.3.0
RUN pip install --no-cache-dir torch==2.0.1+cu118 torchvision==0.15.2+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
RUN pip install --no-cache-dir numpy==1.23.5 fastai==1.0.60 Pillow==9.3.0 tensorboardX>=1.6 opencv-python-headless==4.8.1.78 requests>=2.28,<3 fastapi==0.115.0 uvicorn==0.30.6 aiohttp>=3.9,<4 vastai
RUN git clone --depth 1 https://github.com/jantic/DeOldify.git /app/DeOldify && rm -rf /app/DeOldify/.git
RUN python - <<'PY'\nfrom pathlib import Path\np=Path('/app/DeOldify/deoldify/visualize.py'); s=p.read_text()\nfor line in ['import ffmpeg\\n','import yt_dlp as youtube_dl\\n','from IPython import display as ipythondisplay\\n','from IPython.display import HTML\\n','from IPython.display import Image as ipythonimage\\n']: s=s.replace(line,'')\np.write_text(s)\nPY
RUN mkdir -p /app/DeOldify/models && python - <<'PY'\nimport urllib.request\nfor n in ['ColorizeArtistic_gen.pth','ColorizeStable_gen.pth']:\n u=f'https://huggingface.co/spensercai/DeOldify/resolve/main/{n}'; d=f'/app/DeOldify/models/{n}'; urllib.request.urlretrieve(u,d)\nPY
RUN python - <<'PY'\nfrom torchvision import models\nmodels.resnet34(weights=models.ResNet34_Weights.DEFAULT)\nmodels.resnet101(weights=models.ResNet101_Weights.DEFAULT)\nPY
RUN mkdir -p /workspace /var/log/truecolorize && chmod 777 /workspace /var/log/truecolorize
CMD ["sh","-c","echo 'TrueColorize Vast container ready'; exec tail -f /dev/null"]
