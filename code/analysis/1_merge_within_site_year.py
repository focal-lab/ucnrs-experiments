import sys
import logging
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely import box
import pandas as pd

from spatial_utils.geometric import merge_classified_polygons_by_voting
from spatial_utils.geospatial import ensure_projected_CRS
from spatial_utils.geofileops_wrappers import geofileops_clip, geofileops_dissolve

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import METADATA_FILE, SHIFTED_MAPS_FOLDER, CLASS_NAMES

# Quail, BORR, Hastings
RESERVE = "BORR"
ONLY_LEAF_ON = True
ENSURE_NONOVERLAPPING = True

# Start and end date as month and year (mmdd)
LEAF_ON_START_DATE = 415
LEAF_ON_END_DATE = 1100

logging.basicConfig(level=logging.WARNING)

# %%
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


# %%
def plot_map(gdf, title=None):
    """Show the map, ensuring that colors are consistent across plots"""
    ax = gdf.plot(
        "class_names",
        cmap="tab10",
        vmin=-0.5,
        vmax=9.5,
        legend=True,
        categorical=False,
        categories=CLASS_NAMES,
    )
    if title is not None:
        ax.set_title(title)


def compute_standardized(
    preds: gpd.GeoDataFrame,
    shared_region: gpd.GeoDataFrame,
    ensure_nonoverlapping: bool = False,
):
    """
    Crop the predictions to the shared region, merge all instances of the same class, and optional
    remove any overlaps between classes"""
    if len(preds) == 0:
        return None

    # Make sure everything is in a projected CRS
    preds = ensure_projected_CRS(preds)
    # Clip the geometry to the shared region
    print("About to clip")
    clipped = geofileops_clip(preds, shared_region)
    print("Done clipping")
    # Whether we want to ensure no class regions overlap
    if ensure_nonoverlapping:
        print("About to merge by voting")
        subset = merge_classified_polygons_by_voting(clipped, "class_names")
        # Add back the ID column
        subset["class_ID"] = [
            CLASS_NAMES.index(c) for c in subset["class_names"].to_list()
        ]
        # The class names are dropped in this process, so add them back in
        print("Done merging")
    else:
        # Dissolve all instances of the same class across all predicted datasets
        subset = geofileops_dissolve(
            clipped, groupby_columns="class_names", retain_all_columns=True
        )

    # Clean up the geometry
    subset.geometry = subset.buffer(0)
    # Compute the area fraction
    total_area = (
        gpd.GeoDataFrame(data={"geometry": shared_region})
        .to_crs(subset.crs)
        .area.values[0]
    )

    subset["area_fraction"] = subset.area / total_area

    return subset


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

    index = (int_month_day > LEAF_ON_START_DATE) & (int_month_day < LEAF_ON_END_DATE)

    print(f"{len(index) - index.sum()} rows that were leaf off were dropped")
    all_preds = all_preds[index]

# Add the information about which reserve it corresponds to
all_preds = gpd.sjoin(all_preds, RESERVE_BOUNDS, how="left", predicate="intersects")

# Select data from only one reserve
reserve_preds = all_preds[all_preds["reserve"] == RESERVE]
# Add useful attributes
reserve_preds["year"] = reserve_preds["earliest_datetime_local_derived"].dt.year
reserve_preds["is_2020"] = reserve_preds["year"] == 2020

# Get the bounds of the predictions for each year
per_year_bounds = reserve_preds.dissolve(by="year", as_index=False)

# Find the areas that are present in all years for which any data is available
shared_region_all_years = gpd.GeoDataFrame(
    geometry=[per_year_bounds.geometry.intersection_all()], crs=per_year_bounds.crs
)
# Perform the same operation, but first merge 2023 and 2024
shared_region_2020_vs_23_24 = gpd.GeoDataFrame(
    geometry=[per_year_bounds.dissolve("is_2020").geometry.intersection_all()],
    crs=per_year_bounds.crs,
)

breakpoint()
standardized_2020 = compute_standardized(
    reserve_preds[reserve_preds.year == 2020],
    shared_region_all_years,
    ensure_nonoverlapping=ENSURE_NONOVERLAPPING,
)
standardized_2023 = compute_standardized(
    reserve_preds[reserve_preds.year == 2023],
    shared_region_all_years,
    ensure_nonoverlapping=ENSURE_NONOVERLAPPING,
)
standardized_2024 = compute_standardized(
    reserve_preds[reserve_preds.year == 2024],
    shared_region_all_years,
    ensure_nonoverlapping=ENSURE_NONOVERLAPPING,
)

standardized_2020_merged = compute_standardized(
    reserve_preds[reserve_preds.is_2020],
    shared_region_2020_vs_23_24,
    ensure_nonoverlapping=ENSURE_NONOVERLAPPING,
)

standardized_2023_2024_merged = compute_standardized(
    reserve_preds[~reserve_preds.is_2020],
    shared_region_2020_vs_23_24,
    ensure_nonoverlapping=ENSURE_NONOVERLAPPING,
)
