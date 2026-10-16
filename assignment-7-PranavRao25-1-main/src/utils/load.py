import logging
import os
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import torch
import torchvision
import torchvision.transforms as T
from torchvision.transforms.v2 import PILToTensor
import yaml
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import ConcatDataset, Dataset, Subset

parent = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(
    filename=parent / "prog_log.log",
    format="%(levelname)s: %(message)s", filemode="a"
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.info("DATA PREP")

with open(parent / "config.yaml", "r") as f:
    configs = yaml.full_load(f)

class MNISTTransform:
    def __init__(self, target_size=128, digit_size=28, noise_std=0.2) -> None:
        self.pad = (target_size - digit_size) // 2
        self.digit_size = digit_size
        self.noise_std = noise_std

        self.to_tensor = T.ToTensor()
        self.pad_op = T.Pad(self.pad, fill=0)  # PAD 28 * 28 * 1 INTO 128 * 128 * 3
        self.normalize = T.Normalize(
            mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
        )

    def __call__(self, img) -> Any:
        x = self.pad_op(self.to_tensor(img))
        x = x.repeat(3, 1, 1)

        mask = torch.ones_like(x, dtype=torch.bool)
        mask[
            :,
            self.pad : self.pad + self.digit_size,
            self.pad : self.pad + self.digit_size,
        ] = False

        noise = torch.rand_like(x) * self.noise_std
        x = torch.where(mask, torch.clamp(x + noise, 0.0, 1.0), x)

        return self.normalize(x)

class CatsAndDogsImageDataset(Dataset):
    def __init__(
        self, annotations_file, img_dir, transform=None, target_transform=None
    ) -> None:
        super().__init__()
        self.labels = pd.read_csv(annotations_file)
        self.img_dir = img_dir
        self.transform = transform
        self.target_transform = target_transform
        self.image_paths = []
        self.targets = []

        labels = {"Cat": 0, "Dog": 1}
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        for class_name in ["Cat", "Dog"]:
            class_dir = os.path.join(self.img_dir, class_name)
            for img_name in os.listdir(class_dir):
                img_path = os.path.join(class_dir, img_name)
                if os.path.getsize(img_path) == 0:  # EMPTY FILE
                    logger.debug(f"0 byte {img_name}")
                    print(f"{img_name} 0 byte")
                    continue

                ext = os.path.splitext(img_name)[1].lower()
                if ext in valid_extensions:
                    self.image_paths.append(img_path)
                    label = labels[class_name]
                    self.targets.append(label)
                else:
                    logger.debug(f"Invalid file extension {ext} {img_name}")
                    print(f"Invalid file extension {ext} {img_name}")
                    continue
    
    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, index) -> Any:
        img_path = self.image_paths[index]
        label = self.targets[index]

        im = Image.open(img_path).convert("RGB")
        tensor = PILToTensor()(im)
        if self.transform:
            image = self.transform(tensor)
        if self.target_transform:
            label = self.target_transform(label)
        return image, label

def load_cats_dogs():
    # GET ANNOTATIONS FILE
    annotations = []
    directory = "./data/production/cats_dogs/Cat/"
    for filename in os.listdir(directory):
        annotations.append({"label": 0, "name": "Cat_" + filename.split(".")[0]})
    directory = "./data/production/cats_dogs/Dog/"
    for filename in os.listdir(directory):
        annotations.append({"label": 1, "name": "Dog_" + filename.split(".")[0]})

    df = pd.DataFrame(annotations)
    file_path = configs["data"]["production"] + "/cats_dogs/annotations.csv"
    df.to_csv(parent / file_path, index=False)

def get_balanced_subset(dataset, samples_per_class=500):
    """
        FOR EACH CLASS IN THE DATASET, FETCH A FIXED NO OF SAMPLES FROM EACH
    """

    if hasattr(dataset, "targets"):
        labels = dataset.targets
        if isinstance(labels, torch.Tensor):
            labels = labels.numpy()
        else:
            labels = np.array(labels)
    else:
        labels = np.array([sample[1] for sample in dataset])

    indices = []
    classes = np.unique(labels)

    for c in classes:
        class_indices = np.where(labels == c)[0]
        n_samples = min(samples_per_class, len(class_indices))
        sampled_indices = np.random.choice(class_indices, size=n_samples, replace=False)
        indices.extend(sampled_indices)

    return Subset(dataset, indices)

def extract_targets(dataset):
    """
        GET THE TARGET LABELS FROM THE DATASET
    """

    if isinstance(dataset, ConcatDataset):
        return np.concatenate([extract_targets(d) for d in dataset.datasets])
    elif isinstance(dataset, Subset):
        base_targets = extract_targets(dataset.dataset)
        return np.array(base_targets)[dataset.indices]
    elif hasattr(dataset, "targets"):
        targets = dataset.targets
        if isinstance(targets, torch.Tensor):
            return targets.numpy()
        return np.array(targets)
    else:
        raise AttributeError(
            f"Fatal: Dataset of type {type(dataset)} does not expose a `.targets` attribute. "
            "Ensure all base Datasets construct `self.targets` during __init__."
        )

def split(dataset, train_ratio=0.75, val_ratio=0.15, test_ratio=0.10):
    """
        TRAIN VALID TEST SPLIT
    """

    targets = extract_targets(dataset)
    indices = np.arange(len(dataset))

    train_val_idx, test_idx, train_val_targets, _ = train_test_split(
        indices, targets, test_size=test_ratio, stratify=targets, random_state=42
    )

    relative_val_ratio = val_ratio / (train_ratio + val_ratio)

    train_idx, val_idx = train_test_split(
        train_val_idx,
        test_size=relative_val_ratio,
        stratify=train_val_targets,
        random_state=42,
    )

    return (
        Subset(dataset, train_idx),
        Subset(dataset, val_idx),
        Subset(dataset, test_idx),
    )

img_size = configs["data"]["size"]

cat_dog_image_transform = T.Compose(
    [
        T.ConvertImageDtype(torch.float32),
        T.Resize((img_size, img_size), interpolation=T.InterpolationMode.BILINEAR),
        T.RandomHorizontalFlip(p=0.5),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)
cat_dog_target_transform = lambda x: x + 10

if __name__ == "__main__":
    load_cats_dogs()

    mnist_dir = parent / configs["data"]["mnist"]["folder"]
    mnist_data = torchvision.datasets.MNIST(
        root=mnist_dir,
        train=True,
        download=True,
        transform=MNISTTransform(
            target_size=configs["data"]["size"],
            digit_size=configs["data"]["mnist"]["size"],
        ),
    )
