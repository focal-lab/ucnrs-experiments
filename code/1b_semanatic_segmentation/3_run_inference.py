from pathlib import Path
import sys
import mmseg

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    ALL_IMAGES_FOLDER,
    PER_IMAGE_PREDICTIONS_FOLDER,
    CITYSCAPES_FORMATTED_TRAINING_DATA,
    WORK_DIR,
)

# The MMSegmentation "tools" cannot be directly imported because they are not part of the module.
# To get around this, we must determine the folder they are in and add it to the search path.
mmseg_search_path = str(Path(Path(mmseg.__file__).parent, "..", "tools").resolve())
sys.path.append(mmseg_search_path)
# Import the main function from the inference script
from inference import main as inference_main

INFERENCE_BATCH_SIZE = 2

# Determine the path to the single config file in the formatted training directory
config_files = list(CITYSCAPES_FORMATTED_TRAINING_DATA.glob("*.py"))
if len(config_files) != 1:
    raise ValueError("Config file is not present and unambiguous")
config_file = config_files[0]
# Compute the path to the checkpoint
checkpoint_file = Path(WORK_DIR, "iter_10000.pth")

# Run inference
inference_main(
    config_path=str(config_files),
    checkpoint_path=str(checkpoint_file),
    image_folder=ALL_IMAGES_FOLDER,
    output_folder=PER_IMAGE_PREDICTIONS_FOLDER,
    batch_size=INFERENCE_BATCH_SIZE,
)
