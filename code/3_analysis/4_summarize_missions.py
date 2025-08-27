import sys
import geopandas as gpd
from pathlib import Path
import pandas as pd
from shapely import box, union
from spatial_utils.geospatial import ensure_projected_CRS

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import METADATA_FILE

# Start and end date as month and year (mmdd), only applicable if ONLY_LEAF_ON=True
LEAF_ON_START_DATE = 415
LEAF_ON_END_DATE = 1100

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

# Compute the total surveyed areas
metadata = gpd.read_file(METADATA_FILE)
metadata["earliest_datetime_local_derived"] = pd.to_datetime(
    metadata["earliest_datetime_local_derived"]
)
int_month_day = (
    metadata["earliest_datetime_local_derived"].dt.strftime("%m%d").astype(int)
)
leaf_on_index = (int_month_day > LEAF_ON_START_DATE) & (
    int_month_day < LEAF_ON_END_DATE
)

print(
    f"{len(leaf_on_index) - leaf_on_index.sum()} rows that were leaf off were dropped"
)
# Determine which surveys were during leaf-on times
all_surveys = metadata[leaf_on_index]
# Keep only the year and the geometry
all_surveys["early_vs_late"] = all_surveys["earliest_year_derived"] > "2020"
all_surveys = all_surveys[["early_vs_late", "geometry"]]
# Convert to a projected CRS so the area will be valid m^2
all_surveys = ensure_projected_CRS(all_surveys)

# Add a field for what reserve each dataset came from
RESERVE_BOUNDS.to_crs(all_surveys.crs, inplace=True)
all_surveys = gpd.sjoin(all_surveys, RESERVE_BOUNDS, how="left", predicate="intersects")

# Dissolve by reserve and year
all_surveys_grouped_by_year_reserve = all_surveys.dissolve(["reserve", "early_vs_late"])
breakpoint()

# Compute the areas which were predicted
hast_early = gpd.read_file(
    "/ofo-share/repos-david/UCNRS-experiments/data/outputs/merged_maps/Hastings_2020.gpkg"
)
hast_late = gpd.read_file(
    "/ofo-share/repos-david/UCNRS-experiments/data/outputs/merged_maps/Hastings_2023_2024_merged.gpkg"
)
hast_intersection = gpd.read_file(
    "/ofo-share/repos-david/UCNRS-experiments/data/outputs/merged_clipped_maps/Hastings_2020_separate_years.gpkg"
)

borr_early = gpd.read_file(
    "/ofo-share/repos-david/UCNRS-experiments/data/outputs/merged_maps/BORR_2020.gpkg"
)
borr_late = gpd.read_file(
    "/ofo-share/repos-david/UCNRS-experiments/data/outputs/merged_maps/BORR_2023.gpkg"
)
borr_intersection = gpd.read_file(
    "/ofo-share/repos-david/UCNRS-experiments/data/outputs/merged_clipped_maps/BORR_2020_separate_years.gpkg"
)

Quail_late = gpd.read_file(
    "/ofo-share/repos-david/UCNRS-experiments/data/outputs/merged_maps/Quail_2023.gpkg"
)


print(f"Hast early area {hast_early.area.sum() / 1e4}")
print(f"Hast late area {hast_late.area.sum() / 1e4}")
print(f"Hast intersection area {hast_intersection.area.sum() / 1e4}")

print(f"BORR early area {borr_early.area.sum() / 1e4}")
print(f"BORR late area {borr_late.area.sum() / 1e4}")
print(f"BORR intersection area {borr_intersection.area.sum() / 1e4}")

print(f"Quail late area {Quail_late.area.sum() / 1e4}")
