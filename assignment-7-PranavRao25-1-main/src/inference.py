import torch
from typing import Any
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as T
from torchvision.models import ResNet50_Weights, resnet50
from PIL import Image
import yaml
from pathlib import Path

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

parent = Path(__file__).resolve().parent.parent

with open(parent / "config.yaml", "r") as f:
    configs = yaml.full_load(f)

img_size = configs["data"]["size"]

class ImageClassifier:
    def __init__(self, path) -> None:
        self.model = resnet50()

        state_dict = torch.load(path, weights_only=True)
        self.model.load_state_dict(state_dict)

        self.model.to(device)
        self.model.eval()

        self.transform = T.Compose([
            T.Resize(img_size, interpolation=T.InterpolationMode.BILINEAR),
            T.ToTensor()
        ])

        self.cat_dog_class = {10: "Cat", 11: "Dog"}
    
    def classify(self, image: Image.Image):
        input = self.transform(image).to("cuda") # type: ignore
        outputs = self.model(input)
        _, preds = torch.max(outputs, 1)
        label = int(torch.argmax(preds).item())
        return "Digit" if label < 10 else self.cat_dog_class[label]
