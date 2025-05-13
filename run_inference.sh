#!/bin/bash
# This script is used to run inference using MMsegmentation.
# Prior to running this script, run train_model.sh to generate the checkpoint and config file.
# Usage: ./run_inference.sh <config_path> <checkpoint_path> <image_folder> <output_folder>

set -e

CONFIG_PATH="$1"
CHECKPOINT_PATH="$2"
IMAGE_FOLDER="$3"
OUTPUT_FOLDER="$4"

# Configuration variables
CONDA_ENV_NAME="openmmlab"
MMSEG_DIR="/path/to/mmsegmentation"  # Path to your local clone of https://github.com/open-forest-observatory/mmsegmentation.git

# Activate conda environment. Ensure conda is added to PATH.
echo "Activating conda environment: $CONDA_ENV_NAME"
eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

# Inference
echo "Running inference..."
cd "$MMSEG_DIR"
python inference.py \
    --config_path "$CONFIG_PATH" \
    --checkpoint_path "$CHECKPOINT_PATH" \
    --image_folder "$IMAGE_FOLDER" \
    --output_folder "$OUTPUT_FOLDER"
echo "Inference complete. Results saved in: $OUTPUT_FOLDER"