import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import CLASS_NAMES, MERGED_MAPS_FOLDER, TRANSITION_MATRICES_FOLDER

RESERVES = ["Quail", "BORR", "Hastings"]


def compute_transition_matrix(
    first_class_df, second_class_df, reserve, first_year=None, second_year=None
):
    if first_class_df is None or second_class_df is None:
        return

    overlay = first_class_df.overlay(second_class_df)

    # Get the classes for the left and right dataframes
    i_inds = overlay["class_ID_1"].to_numpy().astype(int)
    j_inds = overlay["class_ID_2"].to_numpy().astype(int)
    # Get the areas of the overlaps
    values = overlay.area.to_numpy()

    # Build a matrix to populate
    transition_matrix = np.zeros((8, 8))
    transition_matrix[i_inds, j_inds] = values
    transition_matrix_row_normed = transition_matrix / np.expand_dims(
        transition_matrix.sum(axis=1), axis=1
    )

    # Display the results
    ConfusionMatrixDisplay(transition_matrix, display_labels=CLASS_NAMES).plot()
    plt.title(f"Transition matrix for {reserve} for {first_year}-{second_year}")
    plt.xticks(rotation=70)
    plt.savefig(
        Path(
            TRANSITION_MATRICES_FOLDER,
            f"{reserve}_{first_year}_{second_year}.png",
        )
    )
    plt.show()
    # Show the results with each row normalized to a sum of one
    ConfusionMatrixDisplay(
        transition_matrix_row_normed, display_labels=CLASS_NAMES
    ).plot()
    plt.title(
        f"Transition matrix (row-normalized) for {reserve} for {first_year}-{second_year}"
    )
    plt.xticks(rotation=70)
    plt.savefig(
        Path(
            TRANSITION_MATRICES_FOLDER,
            f"{reserve}_{first_year}_{second_year}_row_normalized.png",
        )
    )
    plt.show()


def read_if_present(input_file):
    try:
        return gpd.read_file(input_file)
    except:
        return None


TRANSITION_MATRICES_FOLDER.mkdir(parents=True, exist_ok=True)
for reserve in RESERVES:
    separate_2020 = read_if_present(
        Path(MERGED_MAPS_FOLDER, f"{reserve}_2020_separate_years.gpkg")
    )
    separate_2023 = read_if_present(
        Path(MERGED_MAPS_FOLDER, f"{reserve}_2023_separate_years.gpkg")
    )
    separate_2024 = read_if_present(
        Path(MERGED_MAPS_FOLDER, f"{reserve}_2024_separate_years.gpkg")
    )

    separate_table = np.zeros((8, 3))
    if separate_2020 is not None:
        separate_table[separate_2020["class_ID"].to_numpy(), 0] = separate_2020[
            "area_fraction"
        ]
    if separate_2023 is not None:
        separate_table[separate_2023["class_ID"].to_numpy(), 1] = separate_2023[
            "area_fraction"
        ]
    if separate_2024 is not None:
        separate_table[separate_2024["class_ID"].to_numpy(), 2] = separate_2024[
            "area_fraction"
        ]

    final_table_vis = pd.DataFrame(
        data=separate_table, columns=["2020", "2023", "2024"], index=CLASS_NAMES
    )

    compute_transition_matrix(
        separate_2020,
        separate_2023,
        reserve=reserve,
        first_year="2020",
        second_year="2023",
    )
    compute_transition_matrix(
        separate_2020,
        separate_2024,
        reserve=reserve,
        first_year="2020",
        second_year="2024",
    )
    compute_transition_matrix(
        separate_2023,
        separate_2024,
        reserve=reserve,
        first_year="2023",
        second_year="2024",
    )

for reserve in RESERVES:
    merged_2020 = read_if_present(
        Path(MERGED_MAPS_FOLDER, f"{reserve}_2020_merged_years.gpkg")
    )
    merged_2023_2024 = read_if_present(
        Path(MERGED_MAPS_FOLDER, f"{reserve}_2023_2024_merged_years.gpkg")
    )

    compute_transition_matrix(
        merged_2020,
        merged_2023_2024,
        reserve=reserve,
        first_year="2020",
        second_year="2023+2024",
    )
