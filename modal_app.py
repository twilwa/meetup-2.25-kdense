"""
Modal ComfyUI + Seedance Anime Studio
Deploy this to Modal and you'll have a cloud ComfyUI instance
"""
import modal
import os

COMFYUI_DIR = "/comfyui"

# Create the Modal image with ComfyUI dependencies
image = (
    modal.Image.from_registry("pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime")
    .apt_install("git", "wget", "libgl1-mesa-glx", "libglib2.0-0", "libsm6", "libxext6", "libxrender-dev", "libgomp1", env={"DEBIAN_FRONTEND": "noninteractive"})
    .pip_install("numpy", "opencv-python", "pillow", "scipy", "torchsde", "einops", "safetensors", "aiohttp")
    .run_commands(
        f"export DEBIAN_FRONTEND=noninteractive && git clone https://github.com/comfyanonymous/ComfyUI.git {COMFYUI_DIR}",
        f"cd {COMFYUI_DIR} && pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu121",
    )
)

app = modal.App("anime-studio")

@app.function(
    image=image,
    gpu="A100",
    memory=32000,
    timeout=3600,
)
def run_comfyui():
    """Start ComfyUI server"""
    import subprocess
    import time
    
    cmd = f"cd {COMFYUI_DIR} && python main.py --listen 0.0.0.0 --port 8000"
    process = subprocess.Popen(cmd, shell=True)
    time.sleep(30)
    
    return {"status": "ComfyUI started", "port": 8000}


@app.function(
    image=image,
    gpu="A100",
    memory=32000,
    timeout=1800,
)
def generate_video(prompt: str, duration: int = 6, seed: int = 0):
    """Generate video using Seedance (placeholder)"""
    result = {
        "prompt": prompt,
        "duration": duration,
        "seed": seed,
        "status": "placeholder - Seedance workflow not yet implemented",
    }
    return result


@app.function(
    image=image,
    gpu="A100",
    memory=32000,
    timeout=600,
)
def generate_image(prompt: str, negative: str = "", seed: int = 0, steps: int = 30):
    """Generate image using SDXL (placeholder)"""
    result = {
        "prompt": prompt,
        "negative": negative,
        "seed": seed,
        "steps": steps,
        "status": "placeholder - SD workflow not yet implemented",
    }
    return result
