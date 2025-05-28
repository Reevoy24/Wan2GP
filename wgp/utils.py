import os
import io
import base64
import zipfile
from tqdm import tqdm
from PIL import Image
import requests
import gradio as gr


def download_ffmpeg():
    if os.name != 'nt':
        return
    exes = ['ffmpeg.exe', 'ffprobe.exe', 'ffplay.exe']
    if all(os.path.exists(e) for e in exes):
        return
    api_url = 'https://api.github.com/repos/GyanD/codexffmpeg/releases/latest'
    r = requests.get(api_url, headers={'Accept': 'application/vnd.github+json'})
    assets = r.json().get('assets', [])
    zip_asset = next((a for a in assets if 'essentials_build.zip' in a['name']), None)
    if not zip_asset:
        return
    zip_url = zip_asset['browser_download_url']
    zip_name = zip_asset['name']
    with requests.get(zip_url, stream=True) as resp:
        total = int(resp.headers.get('Content-Length', 0))
        with open(zip_name, 'wb') as f, tqdm(total=total, unit='B', unit_scale=True) as pbar:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
    with zipfile.ZipFile(zip_name) as z:
        for f in z.namelist():
            if f.endswith(tuple(exes)) and '/bin/' in f:
                z.extract(f)
                os.rename(f, os.path.basename(f))
    os.remove(zip_name)


def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def pil_to_base64_uri(pil_image, format="png", quality=75):
    if pil_image is None:
        return None

    if isinstance(pil_image, str):
        from wan.utils.utils import get_video_frame
        pil_image = get_video_frame(pil_image, 0)

    buffer = io.BytesIO()
    try:
        img_to_save = pil_image
        if format.lower() == 'jpeg' and pil_image.mode == 'RGBA':
            img_to_save = pil_image.convert('RGB')
        elif format.lower() == 'png' and pil_image.mode not in ['RGB', 'RGBA', 'L', 'P']:
            img_to_save = pil_image.convert('RGBA')
        elif pil_image.mode == 'P':
            img_to_save = pil_image.convert('RGBA' if 'transparency' in pil_image.info else 'RGB')
        if format.lower() == 'jpeg':
            img_to_save.save(buffer, format=format, quality=quality)
        else:
            img_to_save.save(buffer, format=format)
        img_bytes = buffer.getvalue()
        encoded_string = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/{format.lower()};base64,{encoded_string}"
    except Exception as e:
        print(f"Error converting PIL to base64: {e}")
        return None


def is_integer(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()


def create_html_progress_bar(percentage=0.0, text="Idle", is_idle=True):
    bar_class = "progress-bar-custom idle" if is_idle else "progress-bar-custom"
    bar_text_html = f'<div class="progress-bar-text">{text}</div>'

    html = f"""
    <div class="progress-container-custom">
        <div class="{bar_class}" style="width: {percentage:.1f}%;" role="progressbar" aria-valuenow="{percentage:.1f}" aria-valuemin="0" aria-valuemax="100">
            {bar_text_html}
        </div>
    </div>
    """
    return html


def update_generation_status(html_content):

    if html_content:
        return gr.update(value=html_content)

__all__ = [
    "download_ffmpeg",
    "format_time",
    "pil_to_base64_uri",
    "is_integer",
    "create_html_progress_bar",
    "update_generation_status",
    "convert_image",
]

def convert_image(image):
    from PIL import ImageOps
    from typing import cast
    image = image.convert('RGB')
    return cast(Image, ImageOps.exif_transpose(image))
