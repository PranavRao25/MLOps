### IMAGE AUGMENTATION

import shutil
from PIL import Image
import torchvision.transforms as T
import torch
import logging
import numpy as np
from torchvision import datasets, transforms
from torch.utils.data import Subset, DataLoader
import torchvision.utils as vutils
from sklearn.model_selection import train_test_split
from collections import Counter
import yaml
from pathlib import Path
import json

def augment(v1_dir: Path, v2_dir: Path):
    """
    Constructs the v2 dataset by augmenting the training set and 
    directly copying the test set.
    """

    v1_train = v1_dir / "train"
    v1_test = v1_dir / "test"
    v2_train = v2_dir / "train"
    v2_test = v2_dir / "test"
    
    # Define the transformation distribution
    # Induces rotational, translation, and photometric invariance 
    # crucial for capturing cattle muzzle distinctiveness without overfitting.
    augmentation_pipeline = T.Compose([
        T.RandomHorizontalFlip(p=0.5),
        T.RandomRotation(degrees=15),
        T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        T.RandomAffine(degrees=0, translate=(0.1, 0.1))
    ])

    # --- PROCESS TRAINING SET ---
    logger.debug(f"Applying augmentations to training set from {v1_train} -> {v2_train}")
    if v2_train.exists():
        shutil.rmtree(v2_train)
    
    metadata = dict()
    for class_dir in v1_train.iterdir():
        if class_dir.is_dir():
            if class_dir.name not in metadata:
                metadata[class_dir.name] = []
            
            target_class_dir = v2_train / class_dir.name
            target_class_dir.mkdir(parents=True, exist_ok=True)
            
            num_augments = 2
            for img_path in class_dir.glob("*.png"): # Adjust extension if necessary
                img = Image.open(img_path).convert("RGB")
                base_name = img_path.stem
                ext = img_path.suffix
                original_file_name = target_class_dir / f"{base_name}_orig{ext}"
                metadata[class_dir.name].append(original_file_name.name)
                img.save(original_file_name)
                for i in range(num_augments):
                    aug_img = augmentation_pipeline(img)
                    aug_filename = target_class_dir / f"{base_name}_aug{i}{ext}"
                    aug_img.save(aug_filename)
                    metadata[class_dir.name].append(aug_filename.name)

    with open(v2_train / "metadata.json", "w") as f:
        json.dump(metadata, f)

    # --- PROCESS TEST SET ---
    logger.debug(f"Mirroring test set from {v1_test} -> {v2_test} (NO AUGMENTATION)")
    if v2_test.exists():
        shutil.rmtree(v2_test)
    shutil.copytree(v1_test, v2_test)
    
    logger.debug("v2 dataset generation complete.")

if __name__ == "__main__":
    # Dynamically resolve project root
    parent = Path(__file__).resolve().parent.parent

    # Load configuration
    with open(parent / "config.yaml", "r") as f:
        config = yaml.full_load(f)

    logging.basicConfig(filename = parent / "prog_log.log",
                        format = "%(levelname)s: %(message)s",
                        filemode = "a")
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Define paths
    # Assumes v1 is the baseline created in the previous step
    base_processed_dir = parent / config["data"]["processed_dir"]
    v1_path = base_processed_dir / "v1"
    v2_path = base_processed_dir / "v2"
    
    # Execute V2 generation
    augment(v1_path, v2_path)
