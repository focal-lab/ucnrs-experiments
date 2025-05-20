#!/bin/bash
# This script is used to run inference using MMsegmentation.
# Prior to running this script, run train_model.sh to generate the checkpoint and config file.
# Usage: ./run_inference.sh <config_path> <checkpoint_path> <image_folder> <output_folder> <batch_size>

set -e

CONFIG_PATH="$1"
CHECKPOINT_PATH="$2"
IMAGE_FOLDER="$3"
OUTPUT_FOLDER="$4"
BATCH_SIZE="$5"

# Configuration variables
CONDA_ENV_NAME="openmmlab"
MMSEG_DIR="/path/to/mmsegmentation"  # Path to your local clone of https://github.com/open-forest-observatory/mmsegmentation.git

# Activate conda environment. Ensure conda is added to PATH.
echo "Activating conda environment: $CONDA_ENV_NAME"
eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

# Inference
echo "Running inference..."
cd "$MMSEG_DIR/tools"
python inference.py \
    "$CONFIG_PATH" \
    "$CHECKPOINT_PATH" \
    "$IMAGE_FOLDER" \
    "$OUTPUT_FOLDER" \
    --batch-size "$BATCH_SIZE"
echo "Inference complete. Results saved in: $OUTPUT_FOLDER"