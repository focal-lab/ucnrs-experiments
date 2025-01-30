import geopandas as gpd
from GDRT.raster.register_images import align_two_rasters
from GDRT.raster.registration_algorithms import sitk_intensity_registration
from pathlib import Path
from scientific_python_utils.geospatial import ensure_projected_CRS
import numpy as np
import pandas as pd

MERGED_POLYGONS_FILE = "/ofo-share/drone-imagery-organization/3c_metadata-extracted/all-mission-polygons-w-metadata.gpkg"

CHMS_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data/CHMs"
PREDICTED_SHIFTS_FILE = (
    "/ofo-share/scratch-david/georeferencing-experiments/registration_all_pairs.geojson"
)

TARGET_GSD = 0.25

MIN_OVERLAP_TO_REGISTER = 50 ^ 2


def get_all_registrations(overlay_gdf):
    all_predicted_shifts = []

    for _, row in overlay_gdf.iterrows():
        dataset_1 = row["dataset_id_1"][3:]
        dataset_2 = row["dataset_id_2"][3:]
        year_1 = row["earliest_year_derived_1"]
        year_2 = row["earliest_year_derived_2"]

        fixed_chm_filename = Path(CHMS_FOLDER, f"chm-mesh-{dataset_1}.tif")
        moving_chm_filename = Path(CHMS_FOLDER, f"chm-mesh-{dataset_2}.tif")

        print(f"Running {dataset_1} and {dataset_2} for year {year_1} and {year_2}")

        try:
            transforms = align_two_rasters(
                fixed_chm_filename,
                moving_chm_filename,
                aligner_alg=sitk_intensity_registration,
                target_GSD=TARGET_GSD,
                vis_chips=False,
                vis_kwargs={},
                aligner_kwargs={"align_means": False},
            )
            mv2fx_tr = transforms["geospatial_mv2fx_transform"]
            predicted_shift = [mv2fx_tr[0, 2], mv2fx_tr[1, 2]]
        except:
            print(f"Failed for datasets {dataset_1} and {dataset_2}")
            predicted_shift = (np.nan, np.nan)
        print(f"Predicted shift: {predicted_shift}")

        all_predicted_shifts.append(predicted_shift)

    return all_predicted_shifts


gdf = gpd.read_file(MERGED_POLYGONS_FILE)
# Remove extranous columns
gdf = gdf[["dataset_id", "earliest_year_derived", "geometry"]]
# Make sure it's in a projected CRS
gdf = ensure_projected_CRS(gdf)

# Split by year for NRS datasets
# This is not done solely based on the year since other projects (not NRS) might be included as well
polygons_2020 = gdf[(gdf["dataset_id"] <= "000588") & (gdf["dataset_id"] >= "000479")]
polygons_2023 = gdf[(gdf["dataset_id"] <= "000841") & (gdf["dataset_id"] >= "000610")]
polygons_2024 = gdf[(gdf["dataset_id"] <= "000931") & (gdf["dataset_id"] >= "000908")]

# Determine overlaps between years
overlay_2020_2023 = polygons_2020.overlay(polygons_2023)
overlay_2020_2024 = polygons_2020.overlay(polygons_2024)
overlay_2023_2024 = polygons_2023.overlay(polygons_2024)

all_overlays = gpd.GeoDataFrame(
    pd.concat(
        (overlay_2020_2023, overlay_2020_2024, overlay_2023_2024), ignore_index=True
    ),
    crs=overlay_2020_2023.crs,
)

all_overlays = all_overlays[all_overlays.area > MIN_OVERLAP_TO_REGISTER]

all_shifts = get_all_registrations(all_overlays)

all_shifts = np.array(all_shifts)

all_overlays["xshift"] = all_shifts[:, 0]
all_overlays["yshift"] = all_shifts[:, 1]

all_overlays.to_file(Path(PREDICTED_SHIFTS_FILE))
