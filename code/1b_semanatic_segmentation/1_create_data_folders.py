import sys
from pathlib import Path
from mmseg_utils.dataset_creation.folder_to_cityscapes import folder_to_cityscapes

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    CLASS_NAMES,
    TRAINING_IMAGES_FOLDER,
    TRAINING_LABELS_FOLDER,
    CITYSCAPES_FORMATTED_TRAINING_DATA,
)

# The file extensions to include
IMAGE_EXT = ["jpg", "JPG", "jpeg"]
# What fraction of the data should be included in the training set
TRAIN_FRAC = 0.8
# What fraction of the data should be included in the validation set
VAL_FRAC = 0.2

# Run the conversion
folder_to_cityscapes(
    images_folder=TRAINING_IMAGES_FOLDER,
    labels_folder=TRAINING_LABELS_FOLDER,
    output_folder=CITYSCAPES_FORMATTED_TRAINING_DATA,
    classes=CLASS_NAMES,
    image_ext=IMAGE_EXT,
    train_frac=TRAIN_FRAC,
    val_frac=VAL_FRAC,
)
