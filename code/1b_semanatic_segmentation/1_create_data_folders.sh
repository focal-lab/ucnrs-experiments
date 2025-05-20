#!/bin/bash
# This script creates the train-val data folders and generates the mmsegmentation config file.
# Usage: ./create_data_folders.sh <images_dir> <labels_dir> <output_dir>

set -e

IMAGES_DIR="$1"
LABELS_DIR="$2"
OUTPUT_DIR="$3"

CONDA_ENV_NAME="mmseg-utils" # Modify if your conda environment has a different name
SEG_UTILS_DIR="/path/to/segmentation_utils"  # Path to your local clone of https://github.com/open-forest-observatory/segmentation_utils.git

# Activate conda environment. Ensure conda is added to PATH.
echo "Activating conda environment: $CONDA_ENV_NAME"
eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

echo "Creating train-val data folders and generating mmsegmentation config file..."
cd "$SEG_UTILS_DIR/dev/dataset_creation"
python folder_to_cityscapes.py \
    --images-folder "$IMAGES_DIR" \
    --labels-folder "$LABELS_DIR" \
    --output-folder "$OUTPUT_DIR" \
    --classes "BE_bare_earth HL_herbaceous_live MM_man_made_object SD_shrub_dead SL_shrub_live TD_tree_dead TL_tree_live W_water" \
    --image-ext "jpg JPG jpeg" \
    --train-frac "0.8" \
    --val-frac "0.2"
echo "Completed. Data saved to: $OUTPUT_DIR"
