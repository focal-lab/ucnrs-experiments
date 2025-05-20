import json
import logging
import sys
from pathlib import Path

import geofileops as gfo
import geopandas as gpd
from spatial_utils.geofileops_wrappers import (
    geofileops_buffer,
    geofileops_clip,
    geofileops_simplify,
)
from spatial_utils.geometric import ensure_non_overlapping_polygons
from spatial_utils.geospatial import ensure_projected_CRS

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    BUFFER_AMOUNT,
    METADATA_FILE,
    POST_PROCESSED_MAPS_FOLDER,
    PROJECTIONS_TO_GEOSPATIAL_FOLDER,
    SHIFTED_MAPS_FOLDER,
    SHIFTS_PER_DATASET,
    SIMPLIFY_TOL,
    SKIP_EXISTING,
)

RUN_POST_PROCESSING = True
RUN_SHIFTS = True


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
    # The geofileops implementation of clip has errors if there are geometry collections
    # Turn everything into polygons or multipolygons
    nonoverlapping = nonoverlapping.explode()
    nonoverlapping = nonoverlapping[nonoverlapping.geometry.type == "Polygon"]
    nonoverlapping = nonoverlapping.dissolve(
        by=["class_ID", "class_names"], as_index=False
    )

    # TODO determine if it's cheaper to do this operation up front before simplifcation. The one
    # downside is the boundary might not be as precise. So it might be important to do it both
    # before and after.
    # Extract the metadata for this mission
    metadata_for_mission = metadata.query("@dataset_id == mission_id")

    clipped = geofileops_clip(nonoverlapping, metadata_for_mission)
    clipped.to_file(output_path)


if RUN_POST_PROCESSING:
    metadata_for_missions = gpd.read_file(METADATA_FILE)
    map_files = sorted(PROJECTIONS_TO_GEOSPATIAL_FOLDER.glob("*"))

    POST_PROCESSED_MAPS_FOLDER.mkdir(exist_ok=True, parents=True)
    for map_file in map_files:
        dataset_id = map_file.stem

        output_file = Path(
            POST_PROCESSED_MAPS_FOLDER,
            map_file.relative_to(PROJECTIONS_TO_GEOSPATIAL_FOLDER),
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


if RUN_SHIFTS:
    map_files = sorted(POST_PROCESSED_MAPS_FOLDER.glob("*"))

    with open(SHIFTS_PER_DATASET, "r") as infile:
        shifts_per_dataset = json.load(infile)
        SHIFTED_MAPS_FOLDER.mkdir(exist_ok=True, parents=True)
    for map_file in map_files:
        print(f"shifting {map_file}")

        # Read the file
        pred = gpd.read_file(map_file)
        # Record the original CRS
        original_crs = pred.crs
        print(pred)
        # Convert to a projected CRS. The shift is assumed to be with respect to this projected CRS.
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
