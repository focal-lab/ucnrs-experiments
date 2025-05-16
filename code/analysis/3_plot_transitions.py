import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    CLASS_ABBREVIATIONS,
    TRANSITION_MATRICES_FOLDER,
    TRANSITION_MATRIX_PLOTS_FOLDER,
)


def plot_transition(transition_matrix_file):
    transition_matrix = np.load(transition_matrix_file, allow_pickle=True)
    reserve, first_year, second_year = transition_matrix_file.stem.split("_")
    transition_matrix_row_normed = transition_matrix / np.expand_dims(
        transition_matrix.sum(axis=1), axis=1
    )

    # Display the results
    ConfusionMatrixDisplay(transition_matrix, display_labels=CLASS_ABBREVIATIONS).plot()
    plt.title(f"Transition matrix for {reserve} for {first_year}-{second_year}")
    plt.xticks(rotation=70)
    plt.savefig(
        Path(
            TRANSITION_MATRIX_PLOTS_FOLDER,
            f"{reserve}_{first_year}_{second_year}.png",
        ),
        bbox_inches="tight",
    )
    plt.show()
    # Show the results with each row normalized to a sum of one
    ConfusionMatrixDisplay(
        transition_matrix_row_normed, display_labels=CLASS_ABBREVIATIONS
    ).plot()
    plt.title(
        f"Transition matrix (row-normalized) for {reserve} for {first_year}-{second_year}"
    )
    plt.xticks(rotation=70)

    plt.savefig(
        Path(
            TRANSITION_MATRIX_PLOTS_FOLDER,
            f"{reserve}_{first_year}_{second_year}_row_normalized.png",
        ),
        bbox_inches="tight",
    )


files = TRANSITION_MATRICES_FOLDER.glob("*")
TRANSITION_MATRIX_PLOTS_FOLDER.mkdir(exist_ok=True, parents=True)
for file in files:
    plot_transition(file)
