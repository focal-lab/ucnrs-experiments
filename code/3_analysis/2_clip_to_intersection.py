import sys
from pathlib import Path

import shapely
import geopandas as gpd
import numpy as np
import pandas as pd

from spatial_utils.geofileops_wrappers import geofileops_clip

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    CLASS_NAMES,
    MERGED_MAPS_FOLDER,
    TRANSITION_MATRICES_FOLDER,
    TRANSITION_MATRIX_PLOTS_FOLDER,
    MERGED_CLIPPED_MAPS_FOLDER,
)


# The reserves to run this on, defaults to all
RESERVES = ["Quail", "BORR", "Hastings"]


def read_if_present(input_file):
    """Try to read a geopandas file, return None if it does not exist"""
    try:
        return gpd.read_file(input_file)
    except:
        return None


# Make output directories
TRANSITION_MATRICES_FOLDER.mkdir(parents=True, exist_ok=True)
TRANSITION_MATRIX_PLOTS_FOLDER.mkdir(parents=True, exist_ok=True)
MERGED_CLIPPED_MAPS_FOLDER.mkdir(parents=True, exist_ok=True)


# Compute transition matrices for each reserve
for reserve in RESERVES:
    # Read the merged files for each year
    separate_2020 = read_if_present(Path(MERGED_MAPS_FOLDER, f"{reserve}_2020.gpkg"))
    separate_2023 = read_if_present(Path(MERGED_MAPS_FOLDER, f"{reserve}_2023.gpkg"))
    separate_2024 = read_if_present(Path(MERGED_MAPS_FOLDER, f"{reserve}_2024.gpkg"))
    # Get the bounds for non-null reserves
    bounds_per_year = [
        x.dissolve().geometry[0]
        for x in [separate_2020, separate_2023, separate_2024]
        if x is not None
    ]

    if len(bounds_per_year) > 1:
        # TODO this could be updated to geofileops, but it seems like a fairly fast operation anyway
        intersection = shapely.intersection_all(bounds_per_year)

        if separate_2020 is not None:
            separate_2020 = geofileops_clip(separate_2020, intersection)

        if separate_2023 is not None:
            separate_2023 = geofileops_clip(separate_2023, intersection)

        if separate_2024 is not None:
            separate_2024 = geofileops_clip(separate_2024, intersection)

    # Write out files
    if separate_2020 is not None:
        separate_2020.to_file(
            Path(MERGED_CLIPPED_MAPS_FOLDER, f"{reserve}_2020_separate_years.gpkg")
        )
    if separate_2023 is not None:
        separate_2023.to_file(
            Path(MERGED_CLIPPED_MAPS_FOLDER, f"{reserve}_2023_separate_years.gpkg")
        )
    if separate_2024 is not None:
        separate_2024.to_file(
            Path(MERGED_CLIPPED_MAPS_FOLDER, f"{reserve}_2024_separate_years.gpkg")
        )


for reserve in RESERVES:
    # Read the files corresponding to the 2020 and merged 2023+2024 data
    merged_2020 = read_if_present(Path(MERGED_MAPS_FOLDER, f"{reserve}_2020.gpkg"))
    merged_2023_2024 = read_if_present(
        Path(MERGED_MAPS_FOLDER, f"{reserve}_2023_2024_merged_years.gpkg")
    )

    if not None in (merged_2020, merged_2023_2024):
        # No need to do anything if there aren't two things to compare

        # Compute the intersection between the two
        # It would be more confusing, but you could alternatively skip computing an explicit intersection
        # and just crop each file with the other one, which would produce the same results
        intersection = shapely.intersection(merged_2020, merged_2023_2024)

        if merged_2020 is not None:
            merged_2020 = geofileops_clip(merged_2020, intersection)

        if merged_2023_2024 is not None:
            merged_2023_2024 = geofileops_clip(merged_2023_2024, intersection)

    if merged_2020 is not None:
        merged_2020.to_file(
            Path(MERGED_CLIPPED_MAPS_FOLDER, f"{reserve}_2020_merged_years.gpkg")
        )

    if merged_2023_2024 is not None:
        merged_2023_2024.to_file(
            Path(MERGED_CLIPPED_MAPS_FOLDER, f"{reserve}_2023_2024_merged_years.gpkg")
        )
