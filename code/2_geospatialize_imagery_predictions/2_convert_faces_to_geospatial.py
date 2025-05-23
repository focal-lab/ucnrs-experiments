import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from geograypher.meshes import TexturedPhotogrammetryMesh
from geograypher.utils.indexing import find_argmax_nonzero_value

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    CAMERAS_FOLDER,
    CONFIDENCE_THRESHOLD,
    IDS_TO_LABELS,
    MESH_DOWNSAMPLE,
    MESHES_FOLDER,
    METADATA_FILE,
    PROJECTIONS_TO_FACES_FOLDER,
    PROJECTIONS_TO_GEOSPATIAL_FOLDER,
    SKIP_EXISTING,
)


def project_dataset(dataset_id, skip_existings=False):
    # Path to input photogrammetry products
    mesh_file = Path(MESHES_FOLDER, f"{dataset_id}.ply")
    cameras_file = Path(CAMERAS_FOLDER, f"{dataset_id}.xml")
    # Input file for the per-face result
    predicted_face_values_file = Path(PROJECTIONS_TO_FACES_FOLDER, f"{dataset_id}.npy")
    # Output file for the data converted to geospatial
    top_down_vector_projection_file = Path(
        PROJECTIONS_TO_GEOSPATIAL_FOLDER, f"{dataset_id}.gpkg"
    )

    if skip_existings and top_down_vector_projection_file.is_file():
        print(f"Skipping existing geospatial file {dataset_id}")
        return

    # Load the projected face values
    face_values = np.load(predicted_face_values_file)

    # Determine the max class
    max_class = find_argmax_nonzero_value(face_values, keepdims=False)
    max_value = np.max(face_values, axis=1)
    # Remove low confidence faces
    max_class[max_value < CONFIDENCE_THRESHOLD] = np.nan

    # Load a mesh
    mesh = TexturedPhotogrammetryMesh(
        mesh_file,
        transform_filename=cameras_file,
        texture=max_class,
        downsample_target=MESH_DOWNSAMPLE,
        IDs_to_labels=IDS_TO_LABELS,
    )
    # Convert the faces to top down vector file
    mesh.export_face_labels_vector(
        face_labels=max_class,
        export_file=top_down_vector_projection_file,
        label_names=IDS_TO_LABELS,
        vis=False,
    )


# Load the list of dataset IDs
metadata = gpd.read_file(METADATA_FILE)

# Loop over datasets
for dataset_id in metadata.mission_id.values:
    project_dataset(
        dataset_id=dataset_id,
        skip_existings=SKIP_EXISTING,
    )
