import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from itertools import product

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    CLASS_ABBREVIATIONS,
    TRANSITION_MATRICES_FOLDER,
    TRANSITION_MATRIX_PLOTS_FOLDER,
)


def save_transition_matrix_plots(transition_matrix_file):
    # Load the transition matrix from the last step
    transition_matrix = np.load(transition_matrix_file, allow_pickle=True)
    # Parse the reserve, first year, and second year(s) from the filename
    reserve, first_year, second_year = transition_matrix_file.stem.split("_")


files = TRANSITION_MATRICES_FOLDER.glob("*")
TRANSITION_MATRIX_PLOTS_FOLDER.mkdir(exist_ok=True, parents=True)
for file in files:
    save_transition_matrix_plots(file)
