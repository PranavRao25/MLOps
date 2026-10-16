### TRAIN-TEST SPLIT AND RESIZING

import torch
import numpy as np
from torchvision import datasets, transforms
from torch.utils.data import Subset, DataLoader
import torchvision.utils as vutils
from sklearn.model_selection import train_test_split
from collections import Counter
import yaml
import logging
from pathlib import Path
import json

# TODO: AI-GENERATED! FOR REFERENCE ONLY!
# Assisted by [Gemini]
def save_dataset_split(dataset_subset, output_dir, class_names):
    """
    Materializes a PyTorch Subset to disk in an ImageFolder-compatible structure.
    Saves transformed tensors as physical image files.
    """
    output_dir = Path(output_dir)
    
    # Pre-create class directories 
    for cow_class in class_names:
        (output_dir / cow_class).mkdir(parents=True, exist_ok=True)
    
    logging.debug(f"Materializing {len(dataset_subset)} samples to {output_dir}...")
    
    # Iterate over the subset to extract the transformed tensor and label
    meta_data = dict()
    for i in range(len(dataset_subset)):
        img_tensor, label_idx = dataset_subset[i]
        class_name = class_names[label_idx]
        
        # Construct a deterministic file name using the subset index
        filename = f"{class_name}_{i:05d}.png"
        filepath = output_dir / filename
        
        # Save the CHW tensor back to a standard image format
        vutils.save_image(img_tensor, filepath)

        if class_name not in meta_data:
            meta_data[class_name] = []
        meta_data[class_name].append(filename)
    
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(meta_data, f)

# TODO: AI-GENERATED! FOR REFERENCE ONLY!
# Assisted by [Gemini 3 Pro]
def get_stratified_split(root_dir, test_size=0.1, batch_size=32):
    """
    Creates stratified Train/Val (90%) and Test (10%) DataLoaders.
    """
    
    # 1. Define Transforms (Basic resize for validation/metrics)
    # Note: You usually apply heavy augmentation ONLY to the training subset.
    # We will handle that by using a custom Subset wrapper if needed, 
    # but for splitting logic, standard transforms suffice.
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])

    # 2. Load the entire dataset
    # ImageFolder expects: root/class_x/xxx.png
    full_dataset = datasets.ImageFolder(root=root_dir, transform=transform)
    
    # 3. Extract Targets for Stratification
    # ImageFolder.targets contains the list of class indices for every image
    targets = full_dataset.targets
    
    # 4. Generate Stratified Split Indices
    # We split the INDICES, not the data itself.
    # Stratify=targets ensures class distribution remains consistent.
    train_idx, test_idx = train_test_split(
        np.arange(len(targets)),
        test_size=test_size,
        shuffle=True,
        stratify=targets,
        random_state=42 # Seed for reproducibility
    )
    
    # 5. Create Subset Objects
    train_val_dataset = Subset(full_dataset, train_idx)
    test_dataset = Subset(full_dataset, test_idx)
    
    # Verification (Optional but recommended for research)
    logger.debug(f"Total Samples: {len(full_dataset)}")
    logger.debug(f"Train/Val Size: {len(train_val_dataset)} ({len(train_val_dataset)/len(full_dataset):.2%})")
    logger.debug(f"Test Size: {len(test_dataset)} ({len(test_dataset)/len(full_dataset):.2%})")
    
    # 6. Create DataLoaders
    train_loader = DataLoader(train_val_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, test_loader, full_dataset.classes, train_val_dataset, test_dataset

if __name__ == "__main__":
    parent = Path(__file__).resolve().parent.parent

    logging.basicConfig(filename = parent / "prog_log.log",
                        format = "%(levelname)s: %(message)s",
                        filemode = "a")
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    logger.debug("V1 DATA")

    with open(parent / "config.yaml", "r") as f:
        config = yaml.full_load(f)
    
    path = parent / config["data"]["raw_path"]
    logger.debug(path)
    train_loader, test_loader, classes, train_dataset, test_dataset = get_stratified_split(path)

    processed_dir = parent / config["data"]["processed_dir"] / config["data"]["current_version"]
    save_dataset_split(train_dataset, processed_dir / "train", classes)
    save_dataset_split(test_dataset, processed_dir / "test", classes)
    
    logger.debug(f"Dataset successfully materialized to {processed_dir}")
