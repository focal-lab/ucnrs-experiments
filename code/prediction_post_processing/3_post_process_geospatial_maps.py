import geopandas as gpd
import json
import logging
import geopandas as gpd
import geofileops as gfo
from pathlib import Path
from shapely import union, Geometry, MultiPolygon, make_valid, difference
import numpy as np
import typing
from spatial_utils.geofileops_wrappers import (
    geofileops_clip,
    geofileops_simplify,
    geofileops_buffer,
)
from spatial_utils.geometric import ensure_non_overlapping_polygons

from pathlib import Path


DATA_FOLDER = Path("/ofo-share/repos-david/UCNRS-experiments/data")
METADATA_FILE = Path(DATA_FOLDER, "inputs", "mission_metadata.gpkg")

GEOSPATIAL_MAPS_FOLDER = Path(DATA_FOLDER, "intermediate", "geospatial_maps")
POST_PROCESSED_MAPS_FOLDER = Path(DATA_FOLDER, "intermediate", "post_processed_maps")
SHIFTED_MAPS_FOLDER = Path(DATA_FOLDER, "intermediate", "shifted_maps")

SHIFTS_PER_DATASET = Path(DATA_FOLDER, "intermediate", "shift_per_dataset.json")

# Simplify the geometry such that the maximum deviation never exceeds this amount
SIMPLIFY_TOL = 0.1
BUFFER_AMOUNT = 0.2
VIS = False

SKIP_EXISTING = True

SCRATCH_FOLDER = Path("/ofo-share/repos-david/UCNRS-experiments/scratch/geofileops")
BOUNDARY = Path(SCRATCH_FOLDER, "boundary.gpkg")


def post_process_gfo(dataset_id, input_path, output_path, metadata):

    logging.basicConfig(level=logging.INFO)
    input_data = gpd.read_file(input_path)
    simplified1 = geofileops_simplify(
        input_data, tolerence=SIMPLIFY_TOL, convert_to_projected_CRS=True
    )
    buffered1 = geofileops_buffer(
        simplified1, distance=-1 * BUFFER_AMOUNT, convert_to_projected_CRS=True
    )
    buffered2 = geofileops_buffer(
        buffered1, distance=2 * BUFFER_AMOUNT, convert_to_projected_CRS=True
    )
    buffered3 = geofileops_buffer(
        buffered2, distance=-1 * BUFFER_AMOUNT, convert_to_projected_CRS=True
    )
    simplified2 = geofileops_simplify(
        buffered3, tolerence=SIMPLIFY_TOL, convert_to_projected_CRS=True
    )

    nonoverlapping = ensure_non_overlapping_polygons(simplified2)

    # TODO determine if it's cheaper to do this operation up front before simplifcation. The one
    # downside is the boundary might not be as precise. So it might be important to do it both
    # before and after.
    # Extract the metadata for this mission
    metadata_for_mission = metadata.query("@dataset_id == mission_id")
    clipped = geofileops_clip(nonoverlapping, metadata_for_mission)

    clipped.to_file(output_path)


metadata_for_missions = gpd.read_file(METADATA_FILE)
map_files = sorted(GEOSPATIAL_MAPS_FOLDER.glob("*"))

POST_PROCESSED_MAPS_FOLDER.mkdir(exist_ok=True, parents=True)
for map_file in map_files:
    dataset_id = map_file.stem

    output_file = Path(
        POST_PROCESSED_MAPS_FOLDER, map_file.relative_to(GEOSPATIAL_MAPS_FOLDER)
    )
    if SKIP_EXISTING and output_file.is_file():
        print(f"Skipping {dataset_id} because it exists already")
        continue

    print(f"Postprocessing {dataset_id}")

    post_process_gfo(
        dataset_id=dataset_id,
        input_path=map_file,
        output_path=output_file,
        metadata=metadata_for_missions,
    )

map_files = sorted(POST_PROCESSED_MAPS_FOLDER.glob("*"))

with open(SHIFTS_PER_DATASET, "r") as infile:
    shifts_per_dataset = json.load(infile)

SHIFTED_MAPS_FOLDER.mkdir(exist_ok=True, parents=True)
for map_file in map_files:
    # Read the file
    pred = gpd.read_file(map_file)
    # Record the original CRS
    original_crs = pred.crs

    # Convert to a projected CRS
    pred.to_crs(crs=3310, inplace=True)

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
