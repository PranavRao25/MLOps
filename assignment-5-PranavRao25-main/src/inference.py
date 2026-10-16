from PIL import Image
import numpy as np
import yaml
import json
from transformers import pipeline
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import torch
from pathlib import Path

parent = Path(__file__).resolve().parent.parent
with open(parent / "config.yaml", "r") as f:
    configs = yaml.full_load(f)

class ImageCaptioner:
    """
        Wrapper Class for the HuggingFace model
    """

    def __init__(self, model_name):
        self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
        self.feature_extractor = ViTImageProcessor.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device) # type: ignore

    def caption(self, images, max_length=16):
        num_beams = 4
        gen_kwargs = {"max_length": max_length, "num_beams": num_beams}

        pixel_values = self.feature_extractor(images=images, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(self.device)

        output_ids = self.model.generate(pixel_values, **gen_kwargs) # type: ignore

        preds = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        preds = [pred.strip() for pred in preds]
        return preds
