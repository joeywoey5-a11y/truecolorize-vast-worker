from __future__ import annotations
import base64, io, os, sys, tempfile, time
from pathlib import Path
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image, ImageEnhance, ImageOps

ROOT = Path("/app/DeOldify")
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from deoldify import device
from deoldify.device_id import DeviceId
device.set(device=DeviceId.GPU0 if torch.cuda.is_available() else DeviceId.CPU)

from deoldify.visualize import get_artistic_image_colorizer

app = FastAPI(title="TrueColorize Vast Lite Model Server")
ARTISTIC = None
QUALITY = {"fast":25, "balanced":35, "quality":45}
VALID_FILTERS = {"natural","historical","warm","faded","vivid","cool","sepia"}

class Req(BaseModel):
    image_base64: str
    model: str = "artistic"
    quality: str = "balanced"
    strength: float = 0.80
    filter: str = "natural"

def get_colorizer():
    global ARTISTIC
    if ARTISTIC is None:
        print("TRUECOLORIZE_INFO Loading Artistic model", flush=True)
        t0 = time.perf_counter()
        ARTISTIC = get_artistic_image_colorizer(
            root_folder=ROOT, render_factor=35, results_dir="result_images"
        )
        print(f"TRUECOLORIZE_INFO Artistic model loaded in {time.perf_counter()-t0:.2f}s", flush=True)
    return ARTISTIC

def decode_image(value):
    if value.lstrip().startswith("data:") and "," in value:
        value = value.split(",",1)[1]
    raw = base64.b64decode(value, validate=True)
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("Image exceeds 8 MB worker limit")
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    if img.width * img.height > 18_000_000:
        scale = (18_000_000 / float(img.width * img.height)) ** 0.5
        img = img.resize(
            (max(1,int(img.width*scale)), max(1,int(img.height*scale))),
            Image.Resampling.LANCZOS
        )
    if max(img.size) > 5000:
        img.thumbnail((5000,5000), Image.Resampling.LANCZOS)
    return img

def warm(img, amount=.08):
    r,g,b = img.split()
    r = r.point(lambda x: min(255,int(x*(1+amount))))
    b = b.point(lambda x: max(0,int(x*(1-amount))))
    return Image.merge("RGB",(r,g,b))

def cool(img, amount=.07):
    r,g,b = img.split()
    r = r.point(lambda x: max(0,int(x*(1-amount))))
    b = b.point(lambda x: min(255,int(x*(1+amount))))
    return Image.merge("RGB",(r,g,b))

def finish(img, style):
    if style == "historical":
        return ImageEnhance.Brightness(
            ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(.82)).enhance(.96)
        ).enhance(1.01)
    if style == "warm":
        return warm(ImageEnhance.Color(img).enhance(.92))
    if style == "faded":
        return ImageEnhance.Brightness(
            ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(.72)).enhance(.84)
        ).enhance(1.04)
    if style == "vivid":
        return ImageEnhance.Sharpness(
            ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(1.22)).enhance(1.08)
        ).enhance(1.05)
    if style == "cool":
        return cool(ImageEnhance.Color(img).enhance(.92))
    if style == "sepia":
        g = ImageOps.grayscale(img)
        s = ImageOps.colorize(g, "#3a2517", "#e6c79c").convert("RGB")
        return Image.blend(img, s, .30)
    return img.copy()

@app.get("/health")
def health():
    return {"ok":True, "cuda":torch.cuda.is_available(), "model":"artistic"}

@app.post("/colorize")
def colorize(req: Req):
    started = time.perf_counter()
    if req.model.lower() != "artistic":
        raise HTTPException(400, "Vast Lite worker supports artistic model only")
    quality = req.quality.lower()
    style = req.filter.lower()
    if quality not in QUALITY:
        raise HTTPException(400, "invalid quality")
    if style not in VALID_FILTERS:
        raise HTTPException(400, "invalid filter")

    try:
        img = decode_image(req.image_base64)
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "input.jpg"
            img.save(src, "JPEG", quality=95)
            result = get_colorizer().get_transformed_image(
                path=src,
                render_factor=QUALITY[quality],
                post_process=True,
                watermarked=False
            )
            result = ImageEnhance.Color(result).enhance(max(0,min(2,float(req.strength))))
            styled = finish(result, style)

            out = io.BytesIO()
            styled.save(out, "JPEG", quality=92, optimize=True)
            payload = {
                "image_base64":base64.b64encode(out.getvalue()).decode("ascii"),
                "mime_type":"image/jpeg",
                "model":"artistic",
                "quality":quality,
                "render_factor":QUALITY[quality],
                "filter":style,
                "strength":req.strength,
                "width":styled.width,
                "height":styled.height,
                "worker_request_seconds":round(time.perf_counter()-started,3)
            }
            styled.close()
            result.close()
            img.close()
            return payload
    except HTTPException:
        raise
    except Exception as exc:
        print("TRUECOLORIZE_ERROR", repr(exc), flush=True)
        raise HTTPException(500, str(exc))

@app.on_event("startup")
def preload():
    print("TRUECOLORIZE_INFO Lite model server starting", flush=True)
    if torch.cuda.is_available():
        print("TRUECOLORIZE_INFO GPU " + torch.cuda.get_device_name(0), flush=True)
    get_colorizer()
    print("TRUECOLORIZE_MODEL_READY", flush=True)
