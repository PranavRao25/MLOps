import streamlit as st
import logging
from pathlib import Path
import yaml
from uuid import uuid4
import requests
import json
import numpy as np
import torchvision.transforms as T
from PIL import Image
from inference import ImageClassifier

parent = Path(__file__).resolve().parent.parent

with open(parent / "config.yaml", "r") as f:
    configs = yaml.full_load(f)

st.title("Image Classification : Cats vs Dogs vs Digits")

serve_port = configs["port"]["serve"]
MLFLOW_URI = f"http://127.0.0.1:{serve_port}/invocations"

def preprocess_image(img):
    """
        Preprocess the uploaded image into correct format for the model
    """

    target_size = st.session_state["configs"]["data"]["size"]

    transform = T.Compose([
        T.Resize((target_size, target_size)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    input_tensor = transform(img).unsqueeze(0)

    return input_tensor.numpy().astype(np.float32).tolist()

@st.cache_resource
def init_model(path):
    classifier = ImageClassifier(path)
    return classifier

if "configs" not in st.session_state:
    parent = Path(__file__).resolve().parent.parent
    with open(parent / "config.yaml", "r") as f:
        configs = yaml.full_load(f)
    st.session_state["configs"] = configs

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid4())
session_id = st.session_state["session_id"]

model_name = st.session_state["configs"]["model"]["name"]
model_path = st.session_state["configs"]["model"]["path"]
# classifier = init_model(parent / model_path)

mapping = {10: "Cat", 11: "Dog"}

st.write(f"Model used - {model_name}")
uploaded_file = st.file_uploader("Choose a file", type=["jpg", "png", "jpeg", "zip"])
if uploaded_file is not None:
    try:
        img = Image.open(uploaded_file).convert("RGB")
        st.image(uploaded_file, caption="Uploaded Image")

        with st.spinner("MLFlow Serving"):
            input = preprocess_image(img)
            payload = {"inputs": input}

            response = requests.post(
                MLFLOW_URI,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
            )

            if response.status_code == 200:
                prediction_data = response.json()

                logits = np.array(prediction_data["predictions"])
                predicted_class = np.argmax(logits, axis=1)[0]

                if predicted_class not in mapping:
                    label = "Digit"
                else:
                    label = mapping[predicted_class]

                st.write(label)
            else:
                st.error(f"MLflow Server Error {response.status_code}: {response.text}")                
    except Exception as e:
        st.error(f"Error in processing : {type(e).__name__}")
