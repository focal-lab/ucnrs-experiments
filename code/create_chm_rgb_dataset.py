import json
import numpy as np
import cv2
import shutil
import os
from tqdm import tqdm

PATH_TO_MAPPING = "/ofo-share/repos-amritha/extras/ucnrs/subset_to_all_images_mapping.json"  # output of find_corresponding_image_for_subset.py
CHM_ROOT_DIR = "/ofo-share/repos-david/UCNRS-experiments/data/geograypher_outputs/CHM_pointcloud_renders/"  # important to include '/' at the end since we do substr replacement
MERGED_DATA_SAVE_DIR = "/ofo-share/scratch-amritha/NRS-data/chm-merged/ptcloud/intensity-modulation/"
MERGE_METHOD = "intensity_modulation"  # choose from: ["intensity_modulation", "replace_blue"]


with open(PATH_TO_MAPPING, "r") as file:
    data_dict = json.load(file)


all_data_image_paths = list(data_dict.values())
all_data_chm_paths = [path.replace("/ofo-share/drone-imagery-organization/3_sorted-notcleaned-combined/", CHM_ROOT_DIR) for path in all_data_image_paths]
all_data_chm_paths = [path.replace(".JPG", ".npy") for path in all_data_chm_paths]
all_data_chm_paths = [path.replace(".jpg", ".npy") for path in all_data_chm_paths]

subset_data_image_paths = list(data_dict.keys())
new_subset_save_paths = [path.replace("/ofo-share/scratch-david/NRS_labeling/", MERGED_DATA_SAVE_DIR) for path in subset_data_image_paths]

if len(new_subset_save_paths) != len(all_data_image_paths):
    raise ValueError("Mismatch in number of images")

def compute_global_chm_min_max(chm_files):
    """Compute the minimum and maximum CHM value across the dataset"""
    chm_min = np.inf
    chm_max = -np.inf
    skipped_files = []

    for chm_path in chm_files:
        if not os.path.exists(chm_path):
            skipped_files.append(chm_path)
            continue

        try:
            chm = np.load(chm_path)
            chm_min = min(chm_min, np.nanmin(chm))
            chm_max = max(chm_max, np.nanmax(chm))
        except Exception as e:
            print(f"Error loading {chm_path}: {e}")
            skipped_files.append(chm_path)

    return chm_min, chm_max, skipped_files

global_min, global_max, skipped = compute_global_chm_min_max(all_data_chm_paths)
print("Skipped: ", skipped)

new_subset_save_paths = [path.replace('.jpg', '.JPG') if path.endswith('.jpg') else path for path in new_subset_save_paths]
# mapping from CHM file path to the new subset dataset path 
chm_to_save_path = dict(zip(all_data_chm_paths, new_subset_save_paths))

print(f"Saving {len(chm_to_save_path)} images")

def sqrt_rescale(chm):
    """non-linear rescaling of CHM"""
    chm_rescaled = np.sqrt(chm) * np.sqrt(255)
    return chm_rescaled.astype(np.uint8)

def merge_rgb_chm(chm_path, rgb_path, global_min, global_max, method):
    
    chm = np.load(chm_path)
    rgb = cv2.imread(rgb_path)

    if method == "replace_blue":
        rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
        
    elif method == "intensity_modulation":
        hsv = cv2.cvtColor(rgb, cv2.COLOR_BGR2HSV)

    # Replace NaN values with 0
    chm = np.nan_to_num(chm, nan=0.0)

    # Invert CHM horizontally and vertically to match the orientation of the RGB images
    chm = np.flipud(np.fliplr(chm))

    # Upsample CHM to RGB's size
    chm_resized = cv2.resize(chm, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)

    # Apply square root rescaling for non-linear transformation
    chm_scaled = sqrt_rescale(chm_resized)

    # Normalize CHM to 0-255 range
    chm_normalized = (chm_scaled - sqrt_rescale(global_min)) / (sqrt_rescale(global_max) - sqrt_rescale(global_min)) * 255
    chm_normalized = chm_normalized.astype(np.uint8)

    if method == "replace_blue":
        rgb[:,:,2] = chm_normalized
        return rgb
    
    elif method == "intensity_modulation":
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] + chm_normalized * 0.5, 0, 255)
        # hsv[:, :, 2] = np.clip((hsv[:, :, 2] * 0.5) + (chm_normalized * 0.5), 0, 255)
        rgb_modulated = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        return rgb_modulated


for image, chm in tqdm(zip(all_data_image_paths, all_data_chm_paths), total=len(all_data_chm_paths), desc="Processing Images", unit="image"):
    if os.path.exists(chm):
        # Create and save image
        merged = merge_rgb_chm(chm, image, global_min, global_max, MERGE_METHOD)
        save_path = chm_to_save_path[chm]
        os.makedirs(os.path.dirname(save_path), exist_ok = True)
        cv2.imwrite(save_path, cv2.cvtColor(merged, cv2.COLOR_RGB2BGR))

        # Save annotations
        label_path = save_path.replace(MERGED_DATA_SAVE_DIR+"image_subset/", "/ofo-share/scratch-david/NRS_labeling/labeled_images_12_17_merged_classes/")
        label_path = label_path.replace(".JPG", ".png")
        new_label_path = label_path.replace("/ofo-share/scratch-david/NRS_labeling/labeled_images_12_17_merged_classes/", MERGED_DATA_SAVE_DIR+"label_subset/")
        os.makedirs(os.path.dirname(new_label_path), exist_ok = True)

        if os.path.exists(label_path):
            shutil.copy(label_path, new_label_path)
        else:
            print(f"Label file {label_path} not found.")
    else:
        continue
