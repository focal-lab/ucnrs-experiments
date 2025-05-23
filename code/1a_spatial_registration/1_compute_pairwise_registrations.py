import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from GDRT.raster.register_images import align_two_rasters
from GDRT.raster.registration_algorithms import sitk_intensity_registration
from scientific_python_utils.geospatial import ensure_projected_CRS

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    CHMS_FOLDER,
    METADATA_FILE,
    MIN_OVERLAP_TO_REGISTER,
    PAIRWISE_SHIFTS_FILE,
    TARGET_GSD,
)


def get_all_registrations(overlay_gdf):
    all_predicted_shifts = []

    # Iterate over all the pairs of overlapping datasets
    for _, row in overlay_gdf.iterrows():
        # Strip leading zeros from mission name
        mission_1 = row["mission_id_1"].lstrip("0")
        mission_2 = row["mission_id_2"].lstrip("0")
        # Compute the years for each dataset
        year_1 = row["earliest_year_derived_1"]
        year_2 = row["earliest_year_derived_2"]
        # Compute the CHM file path
        fixed_chm_filename = Path(CHMS_FOLDER, f"chm-mesh-{mission_1}.tif")
        moving_chm_filename = Path(CHMS_FOLDER, f"chm-mesh-{mission_2}.tif")
        print(f"Running {mission_1} and {mission_2} for year {year_1} and {year_2}")
        try:
            # Try to compute a shift between the two datasets based on minimizing the CHM discrepency
            transforms = align_two_rasters(
                fixed_chm_filename,
                moving_chm_filename,
                aligner_alg=sitk_intensity_registration,
                target_GSD=TARGET_GSD,
                vis_chips=False,
                vis_kwargs={},
                aligner_kwargs={"align_means": False},
            )
            # Extract the shift component of the predicted transform
            mv2fx_tr = transforms["geospatial_mv2fx_transform"]
            predicted_shift = [mv2fx_tr[0, 2], mv2fx_tr[1, 2]]
        except Exception as e:
            print(e.__traceback__)
            print(f"Failed for missions {mission_1} and {mission_2}")
            predicted_shift = (np.nan, np.nan)
        print(f"Predicted shift: {predicted_shift}")

        all_predicted_shifts.append(predicted_shift)

    return all_predicted_shifts


metadata = gpd.read_file(METADATA_FILE)
# Remove extranous columns
metadata = metadata[["mission_id", "earliest_year_derived", "geometry"]]
# Make sure it's in a projected CRS
metadata = ensure_projected_CRS(metadata)
# Split by year for NRS datasets
# This is not done solely based on the year since other projects (not NRS) might be included as well
metadata_2020 = metadata[metadata["earliest_year_derived"].astype(int) == 2020]
metadata_2023 = metadata[metadata["earliest_year_derived"].astype(int) == 2023]
metadata_2024 = metadata[metadata["earliest_year_derived"].astype(int) == 2024]

# Determine overlaps between years
overlay_2020_2023 = metadata_2020.overlay(metadata_2023)
overlay_2020_2024 = metadata_2020.overlay(metadata_2024)
overlay_2023_2024 = metadata_2023.overlay(metadata_2024)

# Concatenate all overlays
all_overlays = gpd.GeoDataFrame(
    pd.concat(
        (overlay_2020_2023, overlay_2020_2024, overlay_2023_2024), ignore_index=True
    ),
    crs=overlay_2020_2023.crs,
)

# Filter out pairs with limited overlap
all_overlays = all_overlays[all_overlays.area > MIN_OVERLAP_TO_REGISTER]

# Perform registration
all_shifts = get_all_registrations(all_overlays)

# Add shifts to overlay file
all_shifts = np.array(all_shifts)
all_overlays["xshift"] = all_shifts[:, 0]
all_overlays["yshift"] = all_shifts[:, 1]

# Write shifts to file along with overlapping region
all_overlays.to_file(PAIRWISE_SHIFTS_FILE)
