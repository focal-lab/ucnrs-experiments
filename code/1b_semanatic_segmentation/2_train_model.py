from pathlib import Path
import sys
import mmseg

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
# Import constants that are shared across this project
from constants import WORK_DIR, CITYSCAPES_FORMATTED_TRAINING_DATA

# The MMSegmentation "tools" cannot be directly imported because they are not part of the module.
# To get around this, we must determine the folder they are in and add it to the search path.
mmseg_search_path = str(Path(Path(mmseg.__file__).parent, "..", "tools").resolve())
sys.path.append(mmseg_search_path)
# Import main function from the the training tool
from train import main as train_main

# Determine the path to the single config file in the formatted training directory
config_files = list(CITYSCAPES_FORMATTED_TRAINING_DATA.glob("*.py"))
if len(config_files) != 1:
    raise ValueError("Config file is not present and unambiguous")
config_file = config_files[0]

# Run training
train_main(config=str(config_file), work_dir=str(WORK_DIR))
