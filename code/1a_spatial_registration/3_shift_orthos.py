import geopandas as gpd
import sys
from GDRT.raster.utils import update_transform
import json
from pathlib import Path
import numpy as np

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    ORTHOS_FOLDER,
    SHIFTED_ORTHOS_FOLDER,
    SHIFTS_PER_DATASET,
    METADATA_FILE,
)

# Open the list of shifts for each dataset
with open(SHIFTS_PER_DATASET, "r") as infile:
    shifts_per_dataset = json.load(infile)

metadata = gpd.read_file(METADATA_FILE)

for mission_id in metadata.mission_id:
    # Determine whether a shift was calculated for this mission
    if mission_id not in shifts_per_dataset:
        print(f"Mission ID not in shifts: {mission_id}")
        shift = (0, 0)
    else:
        shift = shifts_per_dataset[mission_id]

    # Determine the input and output filenames
    input_filename = Path(ORTHOS_FOLDER, f"{mission_id}.tif")
    output_filename = Path(SHIFTED_ORTHOS_FOLDER, f"{mission_id}.tif")

    # Build a shift-only relative transform
    relative_transform = [
        [
            1,
            0,
            shift[0],
        ],
        [0, 1, shift[1]],
        [0, 0, 1],
    ]
    relative_transform = np.array(relative_transform)

    # Create a file with an updated (shifted) transform
    update_transform(
        input_filename,
        output_filename,
        relative_transform=relative_transform,
        update_existing=True,
    )
