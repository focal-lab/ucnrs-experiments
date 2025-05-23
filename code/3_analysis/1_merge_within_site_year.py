import logging
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import box
from spatial_utils.geofileops_wrappers import geofileops_dissolve
from spatial_utils.geometric import merge_classified_polygons_by_voting
from spatial_utils.geospatial import ensure_projected_CRS

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    CLASS_NAMES,
    MERGED_MAPS_FOLDER,
    METADATA_FILE,
    SHIFTED_MAPS_FOLDER,
)

# Which reserves to process, default is all
RESERVES = ["BORR", "Quail", "Hastings"]

TIEBREAKING_ORDER = [
    "SD_shrub_dead",
    "MM_man_made_object",
    "W_water",
    "HL_herbaceous_live",
    "SL_shrub_live",
    "TD_tree_dead",
    "TL_tree_live",
    "BE_bare_earth",
]

# Should missions be retained only if they were collected during a time where leaves are expected
ONLY_LEAF_ON = True

# Start and end date as month and year (mmdd), only applicable if ONLY_LEAF_ON=True
LEAF_ON_START_DATE = 415
LEAF_ON_END_DATE = 1100

# Should the per-class predictions be post processed such that there are never two class predictions
# for the same region
ENSURE_NONOVERLAPPING = True

logging.basicConfig(level=logging.WARNING)

# The generous bounds of the reserves
RESERVE_BOUNDS = gpd.GeoDataFrame(
    {
        "geometry": [
            box(xmin=-122.5, ymin=38, xmax=-122, ymax=39),
            box(xmin=-122, ymin=37, xmax=-121.5, ymax=38),
            box(xmin=-122, ymin=36, xmax=-121.5, ymax=37),
        ],
        "reserve": ["Quail", "BORR", "Hastings"],
    },
    crs=4326,
)
RESERVE_BOUNDS = ensure_projected_CRS(RESERVE_BOUNDS)


def compute_merged(
    preds: gpd.GeoDataFrame,
    output_file: Path,
    ensure_nonoverlapping: bool = False,
):
    """
    Crop the predictions to the shared region, merge all instances of the same class, and optional
    remove any overlaps between classes"""
    # If there are no predictions, just return
    if len(preds) == 0:
        return None

    # Make sure everything is in a projected CRS
    preds = ensure_projected_CRS(preds)
    # Lower the precision of the geometry to make future operations faster
    preds.geometry = preds.set_precision(grid_size=0.01)
    # Whether we want to ensure no class regions overlap
    if ensure_nonoverlapping:
        print("About to merge by voting")
        merged = merge_classified_polygons_by_voting(
            preds,
            "class_names",
            tiebreaking_class_order=TIEBREAKING_ORDER,
            print_tiebreaking_stats=True,
        )
        # The class names are dropped in this process, so add them back in
        merged["class_ID"] = [
            CLASS_NAMES.index(c) for c in merged["class_names"].to_list()
        ]
        print("Done merging")
    else:
        # Dissolve all instances of the same class across all predicted datasets
        merged = geofileops_dissolve(
            preds, groupby_columns="class_names", retain_all_columns=True
        )

    # Clean up the geometry
    merged.geometry = merged.buffer(0)

    # Write out the file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    # Remove file if it exists since weird thinks can happen with gpkg data containing multiple layers
    # if a file exists already
    output_file.unlink(missing_ok=True)
    # Write to file
    merged.to_file(output_file)


# This all needs to be wrapped in this block because of weird issues with multiprocessing in geofileops
# see: https://github.com/geofileops/geofileops/issues/466
if __name__ == "__main__":
    # Find all predicted maps in the folder
    pred_files = sorted(SHIFTED_MAPS_FOLDER.glob("*"))
    # Read the metadata to get additional attributes
    metadata = gpd.read_file(METADATA_FILE)

    preds = []
    for pred_file in pred_files:
        # Load the predicted map for one dataset
        pred = gpd.read_file(pred_file)
        # Add the mission ID information so it's tracked in the future
        pred["mission_id"] = pred_file.stem
        preds.append(pred)

    all_preds = pd.concat(preds)
    # All the preds are in lat-lon. Convert to a more appropriate CRS for geometric operations.
    all_preds = ensure_projected_CRS(all_preds)
    # Convert the class_ID field from float to int
    all_preds["class_ID"] = all_preds["class_ID"].astype(int)

    # Retain only the date from hte metadata
    metadata = metadata[["mission_id", "earliest_datetime_local_derived"]]
    metadata["earliest_datetime_local_derived"] = pd.to_datetime(
        metadata["earliest_datetime_local_derived"]
    )
    # Ensure that both columns are the same type
    metadata["mission_id"] = metadata["mission_id"].astype(int)
    all_preds["mission_id"] = all_preds["mission_id"].astype(int)
    # Add the date column to the predictions
    all_preds = all_preds.merge(metadata, on="mission_id")

    # Restrict to the time period that leaves would be one
    if ONLY_LEAF_ON:
        # Extract the mmdd representation of the month and day
        int_month_day = (
            all_preds["earliest_datetime_local_derived"].dt.strftime("%m%d").astype(int)
        )

        leaf_on_index = (int_month_day > LEAF_ON_START_DATE) & (
            int_month_day < LEAF_ON_END_DATE
        )

        print(
            f"{len(leaf_on_index) - leaf_on_index.sum()} rows that were leaf off were dropped"
        )
        all_preds = all_preds[leaf_on_index]

    # Add the information about which reserve it corresponds to
    all_preds = gpd.sjoin(all_preds, RESERVE_BOUNDS, how="left", predicate="intersects")

    for reserve in RESERVES:
        # Select data from only the reserve in question
        reserve_preds = all_preds[all_preds["reserve"] == reserve]
        # Add useful attributes
        reserve_preds["year"] = reserve_preds["earliest_datetime_local_derived"].dt.year
        reserve_preds["is_2020"] = reserve_preds["year"] == 2020

        # Compute the merged versions, separated by individual years
        reserve_preds_2020 = reserve_preds[reserve_preds.year == 2020]
        reserve_preds_2023 = reserve_preds[reserve_preds.year == 2023]
        reserve_preds_2024 = reserve_preds[reserve_preds.year == 2024]

        compute_merged(
            reserve_preds_2020,
            output_file=Path(MERGED_MAPS_FOLDER, f"{reserve}_2020.gpkg"),
            ensure_nonoverlapping=ENSURE_NONOVERLAPPING,
        )
        compute_merged(
            reserve_preds_2023,
            output_file=Path(MERGED_MAPS_FOLDER, f"{reserve}_2023.gpkg"),
            ensure_nonoverlapping=ENSURE_NONOVERLAPPING,
        )
        compute_merged(
            reserve_preds_2024,
            output_file=Path(MERGED_MAPS_FOLDER, f"{reserve}_2024.gpkg"),
            ensure_nonoverlapping=ENSURE_NONOVERLAPPING,
        )

        # Only compute the merged versions if it will be different than the separate ones because
        # there is data for both '23 and '24
        if len(reserve_preds_2023) > 0 and len(reserve_preds_2024) > 0:
            compute_merged(
                reserve_preds[~reserve_preds.is_2020],
                output_file=Path(
                    MERGED_MAPS_FOLDER, f"{reserve}_2023_2024_merged.gpkg"
                ),
                ensure_nonoverlapping=ENSURE_NONOVERLAPPING,
            )
