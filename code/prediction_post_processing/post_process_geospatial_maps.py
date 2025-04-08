# %%
import geopandas as gpd
import json
import matplotlib.pyplot as plt
import pandas as pd
import time
from geograypher.utils.geospatial import (
    ensure_non_overlapping_polygons,
    ensure_projected_CRS,
)

from pathlib import Path

# %%
GEOSPATIAL_MAPS_FOLDER = Path(
    "/ofo-share/repos-david/UCNRS-experiments/data/geograypher_outputs/geospatial_maps_high_conf"
)
POST_PROCESSED_MAPS_FOLDER = Path(
    "/ofo-share/repos-david/UCNRS-experiments/data/geograypher_outputs/geospatial_maps_post_processed_high_conf"
)
SHIFTED_MAPS_FOLDER = Path(
    "/ofo-share/repos-david/UCNRS-experiments/data/final/post_processed_shifted_predictions_high_conf"
)

METADATA_FILE = "/ofo-share/drone-imagery-organization/3c_metadata-extracted/all-mission-polygons-w-metadata.gpkg"
SHIFT_PER_DATASET = (
    "/ofo-share/repos-david/UCNRS-experiments/data/shift_per_dataset.json"
)

# Simplify the geometry such that the maximum deviation never exceeds this amount
SIMPLIFY_TOL = 0.1
BUFFER_AMOUNT = 0.2
VIS = False

SKIP_EXISTING = True

# Allows you to specify a subset of the data for testing
START_IND = 0
STOP_IND = 100

# %%
# Load the metadata for all missions, which includes the flight polygons
metadata_for_missions = gpd.read_file(METADATA_FILE)
metadata_for_missions

# %%
# List all the files that are present
map_files = sorted(GEOSPATIAL_MAPS_FOLDER.glob("*"))[START_IND:STOP_IND]

for map_file in map_files:
    dataset_id = map_file.stem

    output_file = Path(
        POST_PROCESSED_MAPS_FOLDER, map_file.relative_to(GEOSPATIAL_MAPS_FOLDER)
    )
    if SKIP_EXISTING and output_file.is_file():
        print(f"{output_file} exists, skipping")
        continue

    # get the associated metadata entry
    metadata = metadata_for_missions.query("mission_id == @dataset_id")
    if VIS:
        metadata.plot()
        plt.show()

    preds = gpd.read_file(map_file)
    if VIS:
        preds.plot("class_names", legend=True)
        plt.show()

    # Make sure this is in a projected CRS so geometric operations work as expected
    preds = ensure_projected_CRS(preds)
    # Simplify the geometry to make future operations faster
    print("Simplifying ")
    start = time.time()
    preds.geometry = preds.simplify(SIMPLIFY_TOL)
    print(f"Simplifying took {time.time() - start}")
    if VIS:
        preds.plot("class_names", legend=True)
        plt.show()

    print("Buffering in")
    start = time.time()
    preds.geometry = preds.buffer(-BUFFER_AMOUNT)
    print(f"Buffering in took {time.time() - start}")
    if VIS:
        preds.plot("class_names", legend=True)
        plt.show()

    print("Buffering out")
    start = time.time()
    preds.geometry = preds.buffer(2 * BUFFER_AMOUNT)
    print(f"Buffering out took {time.time() - start}")
    if VIS:
        preds.plot("class_names", legend=True)
        plt.show()

    print("Buffering in")
    start = time.time()
    preds.geometry = preds.buffer(-BUFFER_AMOUNT)
    print(f"Buffering in took {time.time() - start}")
    if VIS:
        preds.plot("class_names", legend=True)
        plt.show()

    print("Simplifying again")
    start = time.time()
    preds.geometry = preds.simplify(SIMPLIFY_TOL)
    print(f"Simplifying took {time.time() - start}")
    if VIS:
        preds.plot("class_names", legend=True)
        plt.show()

    # Favor the class with the smallest area
    print("Ensuring non-overlapping polygons")
    start = time.time()
    preds = ensure_non_overlapping_polygons(preds)
    print(f"Non-overlapping {time.time() - start}")
    if VIS:
        preds.plot("class_names", legend=True)
        plt.show()

    # Consider doing the thing to make classes non-overlapping by taking the rarest class

    preds.to_crs(metadata.crs, inplace=True)

    print("Clipping")
    start = time.time()
    preds = gpd.clip(gdf=preds, mask=metadata, keep_geom_type=True)
    print(f"Clipping took {time.time() - start}")
    if VIS:
        preds.plot("class_names")
        plt.show()

    # Create containing directory and save file
    output_file.parent.mkdir(exist_ok=True)
    preds.to_file(output_file)

# %%
# List all the files that are present
map_files = sorted(POST_PROCESSED_MAPS_FOLDER.glob("*"))[START_IND:STOP_IND]

with open(SHIFT_PER_DATASET, "r") as infile:
    shifts_per_dataset = json.load(infile)

for map_file in map_files:
    # Read the file
    pred = gpd.read_file(map_file)
    # Record the original CRS
    original_crs = pred.crs

    # Convert to a projected CRS
    pred = ensure_projected_CRS(pred)

    # Get the shift
    name = map_file.stem
    if name in shifts_per_dataset:
        shift = shifts_per_dataset[name]
    else:
        shift = (0, 0)

    # Apply the shift
    pred.geometry = pred.translate(xoff=shift[0], yoff=shift[1])

    # Convert back to the original CRS
    pred.to_crs(original_crs, inplace=True)

    output_file = Path(
        SHIFTED_MAPS_FOLDER, map_file.relative_to(POST_PROCESSED_MAPS_FOLDER)
    )
    # Create the output folder and save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    pred.to_file(output_file)
