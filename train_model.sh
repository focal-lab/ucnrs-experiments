#!/bin/bash
# This script is used to train a model using MMsegmentation. Prior to running this script, 
# run code/scratch/training_data_generation/convert_annotations_new_download.py to generate the (.py) config file.
# Usage: ./train_model.sh <config_path> <work_dir>

set -e

CONFIG_PATH="$1"
WORK_DIR="$2"

# Configuration variables
CONDA_ENV_NAME="openmmlab"
MMSEG_DIR="/path/to/mmsegmentation"  # Path to your local clone of https://github.com/open-forest-observatory/mmsegmentation.git

# Activate conda environment. Ensure conda is added to PATH.
echo "Activating conda environment: $CONDA_ENV_NAME"
eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

# Training
echo "Starting training with config: $CONFIG_PATH"
cd "$MMSEG_DIR/tools"
python train.py "$CONFIG_PATH" --work-dir "$WORK_DIR"
echo "Training complete. Logs and checkpoints saved in: $WORK_DIR"