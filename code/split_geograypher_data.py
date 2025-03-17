import os
import numpy as np
from pathlib import Path
from tqdm import tqdm
import shutil
import random
import cv2

BASE_DIR = Path("/ofo-share/repos-david/UCNRS-experiments/data/labels/geograypher_rendered_fixed")
OUTPUT_DIR = Path("/ofo-share/scratch-amritha/NRS-data/geograypher_rendered/split_data")
IMG_DIR = OUTPUT_DIR / "img_dir"
ANN_DIR = OUTPUT_DIR / "ann_dir"

TRAIN_DIR = "train"
VAL_DIR = "val"
VAL_FRAC = 0.2

# Make the output dirs
for d in [IMG_DIR / TRAIN_DIR, IMG_DIR / VAL_DIR, ANN_DIR / TRAIN_DIR, ANN_DIR / VAL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Get all folders inside the base dir (27 folders)
all_folders = sorted([f for f in BASE_DIR.iterdir() if f.is_dir()])

# Collect all image-label pairs
image_label_pairs = []
for folder in all_folders:
    image_folder = folder / "images"
    label_folder = folder / "renders"

    for subfolder in image_folder.iterdir():

        label_subdir = label_folder / subfolder.name
        # Skip if corresponding label subfolder does not exist
        if not label_subdir.exists():
            continue

        for sub_subfolder in subfolder.iterdir():
            if not sub_subfolder.is_dir():
                continue  # Skip non-folder files
            
            label_sub_subfolder = label_subdir / sub_subfolder.name
            # Skip if labels are missing for this sub-subfolder
            if not label_sub_subfolder.exists():
                continue

            for img_path in sub_subfolder.iterdir():
                label_path = label_sub_subfolder / (img_path.stem + ".png")
                if label_path.exists():
                    image_label_pairs.append((img_path, label_path))

# Shuffle dataset
random.shuffle(image_label_pairs)

# Filter out null images
valid_pairs = []
for img_path, label_path in tqdm(image_label_pairs, desc="Filtering null images"):
    label_img = cv2.imread(str(label_path), cv2.IMREAD_GRAYSCALE)
    if np.any(label_img != 255):
        valid_pairs.append((img_path, label_path))

# Determine split size
num_total = len(valid_pairs)
num_val = int(num_total * VAL_FRAC)

# Split data
val_pairs = valid_pairs[:num_val]
train_pairs = valid_pairs[num_val:]

# Create symlinks for train and val sets
for img_path, label_path in tqdm(train_pairs, desc="Linking train set"):
    os.symlink(img_path, IMG_DIR / TRAIN_DIR / img_path.name)
    os.symlink(label_path, ANN_DIR / TRAIN_DIR / label_path.name)

for img_path, label_path in tqdm(val_pairs, desc="Linking val set"):
    os.symlink(img_path, IMG_DIR / VAL_DIR / img_path.name)
    os.symlink(label_path, ANN_DIR / VAL_DIR / label_path.name)

print(f"Completed. Train: {len(train_pairs)}, Val: {len(val_pairs)}")