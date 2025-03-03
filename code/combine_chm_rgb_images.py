import numpy as np
import cv2
import os
from glob import glob
from tqdm import tqdm
from pathlib import Path
import matplotlib.pyplot as plt

def compute_global_chm_min_max(chm_dir):
    """Compute the minimum and maximum CHM value across the dataset"""
    chm_files = glob(os.path.join(chm_dir, "*.npy"))

    chm_min = np.inf
    chm_max = -np.inf

    for chm_path in chm_files:
        chm = np.load(chm_path)
        chm_min = min(chm_min, np.nanmin(chm))
        chm_max = max(chm_max, np.nanmax(chm))

    return chm_min, chm_max


def sqrt_rescale(chm):
    """non-linear rescaling of CHM"""
    chm_rescaled = np.sqrt(chm) * np.sqrt(255)
    return chm_rescaled.astype(np.uint8)


def merge_chm_rgb(chm_path, rgb_path, global_min, global_max):
    chm = np.load(chm_path)
    rgb = cv2.imread(rgb_path, cv2.IMREAD_UNCHANGED)

    # cv2 reads images in BGR, so convert it to RGB
    rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)

    # Replace NaN values with 0
    chm = np.nan_to_num(chm, nan=0.0)

    # Upsample CHM to RGB's size
    chm_resized = cv2.resize(chm, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)

    # Apply square root rescaling for non-linear transformation
    chm_scaled = sqrt_rescale(chm_resized)

    # Normalize CHM to 0-255 range
    chm_normalized = (chm_scaled - sqrt_rescale(global_min)) / (sqrt_rescale(global_max) - sqrt_rescale(global_min)) * 255
    chm_normalized = chm_normalized.astype(np.uint8)

    # Replace the blue channel with the CHM
    rgb[:,:,2] = chm_normalized
    return rgb


# Set the input and output directories
CHM_FOLDER_PATH = "/ofo-share/scratch-ciro/ucnrs-exp/2023-ucnrs/000610/000610-01/00/"
RGB_FOLDER_PATH = "/ofo-share/drone-imagery-organization/3_sorted-notcleaned-combined/2023-ucnrs/000610/000610-01/00/"

SAVE_PATH = "/ofo-share/repos-amritha/extras/ucnrs/rgb_chm"

chm_files = sorted(glob(CHM_FOLDER_PATH + "*.npy"))
rgb_files = sorted(glob(RGB_FOLDER_PATH + "*.JPG"))

global_min, global_max = compute_global_chm_min_max(CHM_FOLDER_PATH)

# Process and save images
for chm, rgb in zip(chm_files, rgb_files):
    rgb_chm = merge_chm_rgb(chm, rgb, float(global_min), float(global_max))

    # Get filename without extension
    base_name = os.path.splitext(os.path.basename(rgb))[0]
    output_path = os.path.join(SAVE_PATH, f"{base_name}_rgb_chm.jpg")

    # Convert RGB to BGR and save the image
    cv2.imwrite(output_path, cv2.cvtColor(rgb_chm, cv2.COLOR_RGB2BGR))

print("Processing complete. Images saved to:", SAVE_PATH)