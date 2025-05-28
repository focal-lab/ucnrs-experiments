import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    CLASS_NAMES,
    TRANSITION_MATRICES_FOLDER
)

# Iterate over saved transition matrix files
for file in TRANSITION_MATRICES_FOLDER.glob("*"):
    # Load data
    data = np.load(file)
    # Compute area for each
    class_abundance = data.sum(axis=1)
    # Determine fraction of each class that transitions to the corresponding classes
    row_normalized = data / np.expand_dims(class_abundance, axis=1)

    # Concatenate the table of class abundances and convert to percentages
    data = np.concat([np.expand_dims(class_abundance, axis=1) / class_abundance.sum(), row_normalized], axis=1) * 100
    # Create a dataframe
    df = pd.DataFrame(data=data, columns=["Abundance"] + CLASS_NAMES, index=CLASS_NAMES)
    # Print what reserve and year this data corresponds to
    reserve, first_year, second_year = file.stem.split("_")
    print(f"{reserve}: {first_year} - {second_year}")
    # Print the table
    print(df.to_latex(float_format="%.1f",column_format="|l||r|r|r|r|r|r|r|r|r|") )


