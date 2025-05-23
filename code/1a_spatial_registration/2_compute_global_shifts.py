import sys
from pathlib import Path
import geopandas as gpd
import numpy as np
import pprint
import json
import matplotlib.pyplot as plt

from GDRT.harmonizing import compute_global_shifts_from_pairwise

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    PAIRWISE_SHIFTS_FILE,
    ABSOLUTE_SHIFTS_FILE,
    CURRENT_LOCATION_WEIGHT,
    MAX_PAIRWISE_SHIFT,
)

# Read the pairwise shifts
gdf = gpd.read_file(PAIRWISE_SHIFTS_FILE)
# Convert into a dictionary mapping from the pair of dataset IDs and the shift between them
shifts = {
    k: v
    for k, v in zip(
        list(zip(gdf["mission_id_1"].to_list(), gdf["mission_id_2"].to_list())),
        list(zip(gdf["xshift"].to_list(), gdf["yshift"].to_list())),
    )
}

# Remove any shifts that are nan, corresponding to failed registration
shifts = {k: v for k, v in list(shifts.items()) if np.all(np.isfinite(v))}
# Remove any shifts that have a very large value, suggesting erronous registration
shifts = {
    k: v
    for k, v in list(shifts.items())
    if np.all(np.linalg.norm(v) < MAX_PAIRWISE_SHIFT)
}

# Get the list of all dataset IDs
all_dataset_ids = gdf["mission_id_1"].to_list() + gdf["mission_id_2"].to_list()
# Give each dataset the same weighting for staying in the original location
dataset_weights = {
    dataset_id: CURRENT_LOCATION_WEIGHT for dataset_id in all_dataset_ids
}

# Weight each shift identically. In the future this could be updated to include some metric of
# confidence in the shift
shift_weights = np.ones(len(shifts))

# Compute the global shift that minimizes all the error terms using least squares.
global_shifts = compute_global_shifts_from_pairwise(
    shifts,
    shift_weights=shift_weights,
    dataset_weights=dataset_weights,
)
# Print the results
pprint.pprint(global_shifts)

# Save them to a json file
with open(ABSOLUTE_SHIFTS_FILE, "w") as output_h:
    json.dump(global_shifts, output_h, ensure_ascii=True, indent=4, sort_keys=True)

# Show the histogram of pairwise shifts that were the inputs to this algorithm
pairwise_shifts = np.array(list(shifts.values()))
pairwise_shift_dists = np.linalg.norm(pairwise_shifts, axis=1)
plt.title("Histogram of pairwise shift distances")
plt.hist(pairwise_shift_dists, bins=25)
plt.show()
plt.clf()

# Negate to sort largest to smallest
sorting_shift_inds = np.argsort(-pairwise_shift_dists)
dataset_ids = np.array(list(shifts.keys()))

shifts_per_dataset_sorted = [
    (tuple(k), v)
    for k, v in zip(
        dataset_ids[sorting_shift_inds], pairwise_shift_dists[sorting_shift_inds]
    )
]
pprint.pprint(shifts_per_dataset_sorted)

# Show the histogram of per-dataset final shifts that were obtained from the least squares solver
global_shift_values = np.array(list(global_shifts.values()))
global_shift_dists = np.linalg.norm(global_shift_values, axis=1)
plt.title("Histogram of global shift distances")
plt.hist(global_shift_dists, bins=25)
plt.show()
