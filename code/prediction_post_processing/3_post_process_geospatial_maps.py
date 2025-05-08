# %%
import geopandas as gpd
import json
import logging
import geopandas as gpd
import geofileops as gfo
from pathlib import Path
from shapely import union, Geometry, MultiPolygon, make_valid, difference
import numpy as np
import typing

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

METADATA_FILE = "/ofo-share/drone-imagery-organization/3c_metadata-extracted/all-mission-polygons-w-metadata.gpkg"
SCRATCH_FOLDER = Path("/ofo-share/repos-david/UCNRS-experiments/scratch/geofileops")
BOUNDARY = Path(SCRATCH_FOLDER, "boundary.gpkg")

INPUT_DATA_GPKG = Path(SCRATCH_FOLDER, "input.gpkg")
SIMPLIFIED_1 = Path(SCRATCH_FOLDER, "simplified_1.gpkg")
SIMPLIFIED_2 = Path(SCRATCH_FOLDER, "simplified_2.gpkg")
BUFFERED_1 = Path(SCRATCH_FOLDER, "buffered_1.gpkg")
BUFFERED_2 = Path(SCRATCH_FOLDER, "buffered_2.gpkg")
BUFFERED_3 = Path(SCRATCH_FOLDER, "buffered_3.gpkg")
NONOVERLAPPING = Path(SCRATCH_FOLDER, "nonoverlapping.gpkg")
CLIPPED = Path(SCRATCH_FOLDER, "clipped.gpkg")

# Allows you to specify a subset of the data for testing
START_IND = 0
STOP_IND = 100


def ensure_non_overlapping_polygons(
    geometries: typing.Union[typing.List[Geometry], gpd.GeoDataFrame],
    inplace: bool = False,
):
    # Make sure geometries is a list of shapely objects
    if isinstance(geometries, gpd.GeoDataFrame):
        original_gdf = geometries
        geometries = geometries.geometry.tolist()
    else:
        original_gdf = None

    output_geometries = [None] * len(geometries)
    union_of_added_geoms = MultiPolygon()

    areas = [geom.area for geom in geometries]
    sorted_inds = np.argsort(areas)

    for ind in sorted_inds:
        print(f"Processing ind {ind}")
        # Get the input geometry and ensure it's valid
        geom = make_valid(geometries[ind])
        # Subtract the union of all
        geom_to_add = difference(geom, union_of_added_geoms)
        output_geometries[ind] = geom_to_add
        # Add the original geom, not the difference'd one, to avoid boundary artifacts
        union_of_added_geoms = union(geom, union_of_added_geoms)

    if original_gdf is None:
        return output_geometries
    elif inplace:
        original_gdf.geometry = output_geometries
    else:
        output_gdf = original_gdf.copy()
        output_gdf.geometry = output_geometries
        return output_gdf


def post_process_gfo(dataset_id, input_path, output_path, working_crs=3310):
    metadata = gpd.read_file(METADATA_FILE)
    metadata_for_mission = metadata.query("@dataset_id == mission_id")
    metadata_for_mission.to_file(BOUNDARY)

    logging.basicConfig(level=logging.INFO)
    input_data = gpd.read_file(input_path)
    input_data.to_crs(working_crs, inplace=True)
    input_data.to_file(INPUT_DATA_GPKG)

    gfo.simplify(
        input_path=INPUT_DATA_GPKG,
        output_path=SIMPLIFIED_1,
        tolerance=SIMPLIFY_TOL,
        force=True,
    )
    gfo.buffer(
        input_path=SIMPLIFIED_1,
        output_path=BUFFERED_1,
        distance=-BUFFER_AMOUNT,
        endcap_style=gfo.BufferEndCapStyle.FLAT,
        join_style=gfo.BufferJoinStyle.MITRE,
        force=True,
    )
    gfo.buffer(
        input_path=BUFFERED_1,
        output_path=BUFFERED_2,
        distance=2 * BUFFER_AMOUNT,
        endcap_style=gfo.BufferEndCapStyle.FLAT,
        join_style=gfo.BufferJoinStyle.MITRE,
        force=True,
    )
    gfo.buffer(
        input_path=BUFFERED_2,
        output_path=BUFFERED_3,
        distance=-BUFFER_AMOUNT,
        endcap_style=gfo.BufferEndCapStyle.FLAT,
        join_style=gfo.BufferJoinStyle.MITRE,
        force=True,
    )
    gfo.simplify(
        input_path=BUFFERED_3,
        output_path=SIMPLIFIED_2,
        tolerance=SIMPLIFY_TOL,
        force=True,
    )

    simplified = gpd.read_file(SIMPLIFIED_2)
    nonoverlapping = ensure_non_overlapping_polygons(simplified)
    nonoverlapping.to_crs(metadata_for_mission.crs, inplace=True)
    nonoverlapping.to_file(NONOVERLAPPING)

    gfo.clip(input_path=NONOVERLAPPING, clip_path=BOUNDARY, output_path=output_path)


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
        print(f"Skipping {dataset_id} because it exists already")
        continue

    print(f"Postprocessing {dataset_id}")

    post_process_gfo(
        dataset_id=dataset_id, input_path=map_file, output_path=output_file
    )

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
