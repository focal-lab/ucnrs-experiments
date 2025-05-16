import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay
from itertools import product

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    CLASS_ABBREVIATIONS,
    TRANSITION_MATRICES_FOLDER,
    TRANSITION_MATRIX_PLOTS_FOLDER,
)


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
    Adapted from scikit-learn's confusion matrix visualization:
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


def save_transition_matrix_plots(transition_matrix_file):
    # Load the transition matrix from the last step
    transition_matrix = np.load(transition_matrix_file, allow_pickle=True)
    # Parse the reserve, first year, and second year(s) from the filename
    reserve, first_year, second_year = transition_matrix_file.stem.split("_")
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


files = TRANSITION_MATRICES_FOLDER.glob("*")
TRANSITION_MATRIX_PLOTS_FOLDER.mkdir(exist_ok=True, parents=True)
for file in files:
    save_transition_matrix_plots(file)
