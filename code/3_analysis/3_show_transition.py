import sys
from pathlib import Path

from itertools import product
import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from spatial_utils.geofileops_wrappers import geofileops_overlay

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    CLASS_NAMES,
    MERGED_CLIPPED_MAPS_FOLDER,
    TRANSITION_MATRICES_FOLDER,
    TRANSITION_MATRIX_PLOTS_FOLDER,
    CLASS_ABBREVIATIONS,
)

# The reserves to run this on, defaults to all
RESERVES = ["Quail", "BORR", "Hastings"]


def plot_transition(
    transition_matrix,
    display_labels,
    include_values=True,
    cmap="viridis",
    xticks_rotation="horizontal",
    values_format=None,
    ax=None,
    colorbar=True,
    im_kw=None,
    text_kw=None,
):
    """
    Lightly adapted from scikit-learn's confusion matrix visualization:
    https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    n_classes = transition_matrix.shape[0]

    default_im_kw = dict(interpolation="nearest", cmap=cmap)
    im_kw = im_kw or {}
    im_kw = {**default_im_kw, **im_kw}
    text_kw = text_kw or {}

    im_ = ax.imshow(transition_matrix, **im_kw)
    text_ = None
    cmap_min, cmap_max = im_.cmap(0), im_.cmap(1.0)

    if include_values:
        text_ = np.empty_like(transition_matrix, dtype=object)

        # print text with appropriate color depending on background
        thresh = (transition_matrix.max() + transition_matrix.min()) / 2.0

        for i, j in product(range(n_classes), range(n_classes)):
            color = cmap_max if transition_matrix[i, j] < thresh else cmap_min

            if values_format is None:
                text_cm = format(transition_matrix[i, j], ".2g")
                if transition_matrix.dtype.kind != "f":
                    text_d = format(transition_matrix[i, j], "d")
                    if len(text_d) < len(text_cm):
                        text_cm = text_d
            else:
                text_cm = format(transition_matrix[i, j], values_format)

            default_text_kwargs = dict(ha="center", va="center", color=color)
            text_kwargs = {**default_text_kwargs, **text_kw}

            text_[i, j] = ax.text(j, i, text_cm, **text_kwargs)

    if display_labels is None:
        display_labels = np.arange(n_classes)
    else:
        display_labels = display_labels
    if colorbar:
        fig.colorbar(im_, ax=ax)
    ax.set(
        xticks=np.arange(n_classes),
        yticks=np.arange(n_classes),
        xticklabels=display_labels,
        yticklabels=display_labels,
        ylabel="First year's classes",
        xlabel="Second year's classes",
    )

    ax.set_ylim((n_classes - 0.5, -0.5))
    plt.setp(ax.get_xticklabels(), rotation=xticks_rotation)


def compute_transition_matrix(
    first_class_df, second_class_df, reserve, first_year=None, second_year=None
):
    # Transitions can't be shown if data doesn't exist for both years
    if first_class_df is None or second_class_df is None:
        return

    # Expensive operation
    overlay = geofileops_overlay(first_class_df, second_class_df)
    union_area = overlay.area.sum()
    # Drop any rows that don't have data from both years
    overlay.dropna(inplace=True)
    intersection_area = overlay.area.sum()
    print(
        f"Dropped {100*(union_area - intersection_area)/union_area:.4f}% of unioned area due to imperfect alignment between the two regions"
    )

    # Get the classes for the left and right dataframes
    i_inds = overlay["l1_class_ID"].to_numpy().astype(int)
    j_inds = overlay["l2_class_ID"].to_numpy().astype(int)
    # Get the areas of the overlaps
    values = overlay.area.to_numpy()

    # Build a matrix to populate
    transition_matrix = np.zeros((8, 8))
    transition_matrix[i_inds, j_inds] = values
    # Save the transition matrix values
    np.save(
        Path(
            TRANSITION_MATRICES_FOLDER,
            f"{reserve}_{first_year}_{second_year}.npy",
        ),
        transition_matrix,
    )

    # Compute the normalized version such that rows sum to 1
    transition_matrix_row_normed = transition_matrix / np.expand_dims(
        transition_matrix.sum(axis=1), axis=1
    )

    # Display the results
    plot_transition(transition_matrix, CLASS_ABBREVIATIONS)
    plt.title(f"Transition matrix for {reserve} for {first_year}-{second_year}")
    plt.savefig(
        Path(
            TRANSITION_MATRIX_PLOTS_FOLDER,
            f"{reserve}_{first_year}_{second_year}.png",
        ),
        bbox_inches="tight",
    )
    plt.show()

    # Show the results with each row normalized to a sum of one
    plot_transition(transition_matrix_row_normed, CLASS_ABBREVIATIONS)
    plt.title(
        f"Transition matrix (row-normalized) for\n{reserve} for {first_year}-{second_year}"
    )
    plt.savefig(
        Path(
            TRANSITION_MATRIX_PLOTS_FOLDER,
            f"{reserve}_{first_year}_{second_year}_row_normalized.png",
        ),
        bbox_inches="tight",
    )


def read_if_present(input_file):
    """Try to read a geopandas file, return None if it does not exist"""
    try:
        return gpd.read_file(input_file)
    except:
        return None


# Make output directories
TRANSITION_MATRICES_FOLDER.mkdir(parents=True, exist_ok=True)
TRANSITION_MATRIX_PLOTS_FOLDER.mkdir(parents=True, exist_ok=True)

# Compute transition matrices for each reserve
for reserve in RESERVES:
    # Read the merged files for each year
    separate_2020 = read_if_present(
        Path(MERGED_CLIPPED_MAPS_FOLDER, f"{reserve}_2020_separate_years.gpkg")
    )
    separate_2023 = read_if_present(
        Path(MERGED_CLIPPED_MAPS_FOLDER, f"{reserve}_2023_separate_years.gpkg")
    )
    separate_2024 = read_if_present(
        Path(MERGED_CLIPPED_MAPS_FOLDER, f"{reserve}_2024_separate_years.gpkg")
    )

    # Populate a table of class fractions
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

    # Display the class fractions
    separate_table_vis = pd.DataFrame(
        data=separate_table, columns=["2020", "2023", "2024"], index=CLASS_NAMES
    )
    print(f"Class fractions for {reserve}, separated by years")
    print(separate_table_vis)

    # Compute and save the year-to-year transition matrices
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
    # Read the files corresponding to the merged 2023+2024 data
    merged_2020 = read_if_present(
        Path(MERGED_CLIPPED_MAPS_FOLDER, f"{reserve}_2020_merged_years.gpkg")
    )
    merged_2023_2024 = read_if_present(
        Path(MERGED_CLIPPED_MAPS_FOLDER, f"{reserve}_2023_2024_merged_years.gpkg")
    )

    # Populate a table of class fractions for the merged data
    merged_table = np.zeros((8, 2))
    if merged_2020 is not None:
        separate_table[merged_2020["class_ID"].to_numpy(), 0] = merged_2020[
            "area_fraction"
        ]
    if merged_2023_2024 is not None:
        separate_table[merged_2023_2024["class_ID"].to_numpy(), 1] = merged_2023_2024[
            "area_fraction"
        ]

    # Display the class fractions
    merged_table_vis = pd.DataFrame(
        data=merged_table, columns=["2020", "2023+2024"], index=CLASS_NAMES
    )
    print(f"Class fractions for {reserve}, with 2023 and 2024 merged")
    print(merged_table_vis)

    # Compute transition matrix
    compute_transition_matrix(
        merged_2020,
        merged_2023_2024,
        reserve=reserve,
        first_year="2020",
        second_year="2023+2024",
    )
