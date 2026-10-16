import streamlit as st
import yaml
from src.inference import ImageCaptioner
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Info, Summary
import io
import psutil
import os
import zipfile
from PIL import Image
import time
from uuid import uuid4
from pathlib import Path

st.title("Image Captioning")

@st.cache_resource
def init_metrics_server(port=8000):
    start_http_server(port)
    return True

@st.cache_resource
def get_metrics():
    return {
        "images_processed": Counter(
            "app_total_images_processed",
            "Total number of images processed by the model",
            labelnames=["mode", "session_id"]
        ),
        "requests": Counter(
            "app_total_requests",
            "Total number of inference requests made",
            labelnames=["mode"]
        ),
        "errors": Counter(
            "app_total_errors",
            "Total number of exceptions",
            labelnames=["mode", "error_type"]
        ),
        "active_requests": Gauge(
            "app_active_requests_current",
            "Number of images currently being processed",
            labelnames=["session_id"]
        ),
        "model_memory_usage": Gauge(
            "app_model_memory_bytes",
            "Current usage of RSS memory by the app"
        ),
        "inference_latency": Histogram(
            "app_inference_latency_seconds",
            "Latency of image captioning in seconds",
            labelnames=["mode", "model_type"]
        ),
        "payload_size": Summary(
            "app_image_payload_size_bytes",
            "Size of uploaded images being processed",
            labelnames=["mode"]
        )
    }

@st.cache_resource
def init_model():
    captioner = ImageCaptioner(model_name)    
    return captioner

if "configs" not in st.session_state:
    parent = Path(__file__).resolve().parent.parent
    with open(parent / "config.yaml", "r") as f:
        configs = yaml.full_load(f)
    st.session_state["configs"] = configs

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid4())
session_id = st.session_state["session_id"]

init_metrics_server(st.session_state["configs"]["monitoring"]["port"]["model"])
metrics = get_metrics()

process = psutil.Process(os.getpid())
metrics["model_memory_usage"].set(process.memory_info().rss) # type: ignore

model_name = st.session_state["configs"]["model"]["name"]
captioner = init_model()

st.write(f"Model used - {model_name}")
uploaded_file = st.file_uploader("Choose a file", type=["jpg", "png", "jpeg", "zip"])
if uploaded_file is not None:
    file_size = uploaded_file.size
    is_zip = uploaded_file.type == "application/zip"
    mode = "zip" if is_zip else "single"

    metrics["payload_size"].labels(mode=mode).observe(file_size) # type: ignore
    metrics["active_requests"].labels(session_id=session_id).inc() # type: ignore
    metrics["requests"].labels(mode=mode).inc() # type: ignore
    
    try:
        with metrics["inference_latency"].labels(mode=mode, model_type=model_name).time(): # type: ignore
            if is_zip:  # Batch work
                images = []
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    file_names = zip_ref.namelist()
                    for file_name in file_names:
                        with zip_ref.open(file_name) as file_in_zip:
                            content = file_in_zip.read()
                            image = Image.open(io.BytesIO(content)).convert("RGB")
                        images.append(image)
                
                captions = captioner.caption(images)
                for img, caption in zip(images, captions):
                    st.image(img)
                    st.write(caption)
            else:  # Single Image
                img = Image.open(uploaded_file).convert("RGB")
                caption = captioner.caption([img])[0]
                st.image(uploaded_file)
                st.write(caption)

            metrics["images_processed"].labels(mode=mode, session_id=session_id).inc() # type: ignore
    except Exception as e:
        error_name = type(e).__name__
        metrics["errors"].labels(mode=mode, error_type=error_name).inc() # type: ignore
        st.error(f"Error in processing : {error_name}")
    finally:
        metrics["active_requests"].labels(session_id=session_id).dec() # type: ignore
