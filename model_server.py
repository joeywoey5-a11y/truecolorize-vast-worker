from __future__ import annotations
import base64, io, os, sys, tempfile, time
from pathlib import Path
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image, ImageEnhance, ImageOps

ROOT=Path("/app/DeOldify"); sys.path.insert(0,str(ROOT)); os.chdir(ROOT)
from deoldify import device
from deoldify.device_id import DeviceId
device.set(device=DeviceId.GPU0 if torch.cuda.is_available() else DeviceId.CPU)
from deoldify.visualize import get_artistic_image_colorizer,get_stable_image_colorizer

app=FastAPI(title="TrueColorize Model Server")
ARTISTIC=None; STABLE=None
QUALITY={"fast":25,"balanced":35,"quality":45}

class Req(BaseModel):
    image_base64:str
    model:str="artistic"
    quality:str="balanced"
    strength:float=.8
    filter:str="natural"

def get_colorizer(model):
    global ARTISTIC,STABLE
    if model=="stable":
        if STABLE is None:
            print("TRUECOLORIZE_INFO Loading Stable model",flush=True)
            STABLE=get_stable_image_colorizer(root_folder=ROOT,render_factor=35,results_dir="result_images")
        return STABLE
    if ARTISTIC is None:
        print("TRUECOLORIZE_INFO Loading Artistic model",flush=True)
        ARTISTIC=get_artistic_image_colorizer(root_folder=ROOT,render_factor=35,results_dir="result_images")
    return ARTISTIC

def decode(v):
    if v.lstrip().startswith("data:") and "," in v: v=v.split(",",1)[1]
    raw=base64.b64decode(v,validate=True)
    if len(raw)>8*1024*1024: raise ValueError("Image exceeds 8 MB worker limit")
    return ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")

def finish(img,style):
    if style=="historical": return ImageEnhance.Brightness(ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(.82)).enhance(.96)).enhance(1.01)
    if style=="faded": return ImageEnhance.Brightness(ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(.72)).enhance(.84)).enhance(1.04)
    if style=="vivid": return ImageEnhance.Sharpness(ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(1.22)).enhance(1.08)).enhance(1.05)
    if style=="sepia":
        g=ImageOps.grayscale(img); s=ImageOps.colorize(g,"#3a2517","#e6c79c").convert("RGB"); return Image.blend(img,s,.30)
    return img.copy()

@app.get("/health")
def health(): return {"ok":True,"cuda":torch.cuda.is_available()}

@app.post("/colorize")
def colorize(req:Req):
    t=time.perf_counter()
    try:
        img=decode(req.image_base64)
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/"input.jpg"; img.save(src,"JPEG",quality=95)
            out=get_colorizer(req.model).get_transformed_image(path=src,render_factor=QUALITY[req.quality],post_process=True,watermarked=False)
            out=ImageEnhance.Color(out).enhance(max(0,min(2,float(req.strength))))
            out=finish(out,req.filter)
            b=io.BytesIO(); out.save(b,"JPEG",quality=92,optimize=True)
            payload={"image_base64":base64.b64encode(b.getvalue()).decode(),"mime_type":"image/jpeg","model":req.model,"quality":req.quality,"render_factor":QUALITY[req.quality],"filter":req.filter,"strength":req.strength,"width":out.width,"height":out.height,"worker_request_seconds":round(time.perf_counter()-t,3)}
            out.close(); img.close(); return payload
    except Exception as e:
        print("TRUECOLORIZE_ERROR",repr(e),flush=True)
        raise HTTPException(500,str(e))

@app.on_event("startup")
def preload():
    print("TRUECOLORIZE_INFO Model server starting",flush=True)
    get_colorizer("artistic")
    if torch.cuda.is_available(): print("TRUECOLORIZE_INFO GPU "+torch.cuda.get_device_name(0),flush=True)
    print("TRUECOLORIZE_MODEL_READY",flush=True)
