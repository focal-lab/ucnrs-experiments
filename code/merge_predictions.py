# %%
import geopandas as gpd
import json
import matplotlib.pyplot as plt
import pandas as pd
from scientific_python_utils.geospatial import ensure_projected_CRS

from pathlib import Path

# %%
GEOSPATIAL_MAPS_FOLDER = Path("/ofo-share/scratch-david/NRS-all-sites/geospatial_maps")
SHIFT_PER_DATASET = (
    "/ofo-share/repos-david/UCNRS-experiments/data/shift_per_dataset.json"
)
METADATA_FILE = "/ofo-share/drone-imagery-organization/3c_metadata-extracted/all-mission-polygons-w-metadata.gpkg"
OUTPUT_FILE = (
    "/ofo-share/repos-david/UCNRS-experiments/data/all_geospatial_maps_merged.geojson"
)

SIMPLIFY_TOL = 1

# %%
map_files = sorted(GEOSPATIAL_MAPS_FOLDER.glob("*"))

with open(SHIFT_PER_DATASET, "r") as infile:
    shifts_per_dataset = json.load(infile)

all_dataframes = []

for map_file in map_files:
    dataset = map_file.stem

    if dataset not in shifts_per_dataset:
        print(f"Dataset {dataset} not in shifts_per_dataset. Skipping.")
        continue

    shift = shifts_per_dataset[dataset]

    print(f"Reading {map_file}")
    try:
        gdf = gpd.read_file(map_file)
    except:
        print(f"Failed to read {dataset}. Skipping")
        continue

    gdf = ensure_projected_CRS(gdf)
    gdf.geometry = gdf.simplify(SIMPLIFY_TOL)
    gdf["dataset"] = dataset
    gdf.geometry = gdf.translate(xoff=shift[0], yoff=shift[1])
    all_dataframes.append(gdf)
    # gdf.plot("class_names", legend=True, vmin=-0.5, vmax=9.5)
    # plt.show()


# %%
merged_dataframes = pd.concat(all_dataframes)
# merged_dataframes.to_file(OUTPUT_FILE)
print(merged_dataframes)

# %%
metadata = gpd.read_file(METADATA_FILE).to_crs(merged_dataframes.crs)
print(metadata.columns)
print(metadata["mission_id"])

# %%
merged_dataframes_w_metadata = gpd.GeoDataFrame(
    pd.merge(
        merged_dataframes,
        metadata,
        left_on="dataset",
        right_on="mission_id",
        suffixes=(None, "_metadata"),
    ),
    crs=merged_dataframes.crs,
)

merged_dataframes_w_metadata.set_geometry("geometry", drop=True, inplace=True)
# also need to crop geometry to boundary of the region
merged_dataframes_w_metadata

# %%
dataset_boundaries = merged_dataframes_w_metadata["geometry_metadata"]
dataset_boundaries

# %%
dataset_boundaries = dataset_boundaries.make_valid()

# %%
merged_dataframes_w_metadata.geometry = merged_dataframes_w_metadata.make_valid()
# This seems to be required because of an issue with two coinciding points
# https://gis.stackexchange.com/questions/484691/topologyexception-side-location-conflict-while-intersects-on-valid-polygons
merged_dataframes_w_metadata.geometry = merged_dataframes_w_metadata.buffer(-0.01)

# %%
import shapely

clipped_rows = []

for i, row in merged_dataframes_w_metadata.iterrows():
    print(i)
    row.geometry = shapely.intersection(
        row.geometry, row.geometry_metadata, grid_size=0.01
    )
    clipped_rows.append(row)

# %%
clipped_gdf

# %%
i = 1

metadata = merged_dataframes_w_metadata.iloc[i : i + 1, :]
print(f"Clipping metadata: {metadata}")
print(bounds)

metadata.geometry = metadata.make_valid()
# metadata.geometry = metadata.simplify(0.1)
metadata.geometry = metadata.buffer(-0.01)

bounds = shapely.make_valid(bounds)

gpd.GeoDataFrame(geometry=[bounds]).plot()
plt.show()
metadata.plot()
plt.show()

clipped = metadata.clip(bounds)

# %%
