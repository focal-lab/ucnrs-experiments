from pathlib import Path
import numpy as np
import geopandas as gpd

from geograypher.utils.indexing import find_argmax_nonzero_value
from geograypher.meshes import TexturedPhotogrammetryMesh


IDS_TO_LABELS = {
    0: "BE_bare_earth",
    1: "HL_herbaceous_live",
    2: "MM_man_made_object",
    3: "SD_shrub_dead",
    4: "SL_shrub_live",
    5: "TD_tree_dead",
    6: "TL_tree_live",
    7: "W_water",
}

DATA_FOLDER = Path("/ofo-share/repos-david/UCNRS-experiments/data")
ALL_IMAGES_FOLDER = Path(DATA_FOLDER, "inputs", "images")
PHOTOGRAMMETRY_FOLDER = Path(DATA_FOLDER, "inputs", "photogrammetry")

METADATA_FILE = Path(DATA_FOLDER, "inputs", "mission_metadata.gpkg")
PROJECTIONS_FOLDER = Path(
    DATA_FOLDER,
    "intermediate",
    "projections_to_faces",
)
OUTPUT_FOLDER = Path(DATA_FOLDER, "intermediate", "geospatial_maps")

CONFIDENCE_THRESHOLD = 0.8
N_CAMERAS_PER_CHUNK = 100

SKIP_EXISTING = False


def project_dataset(dataset_id, skip_existings=False):
    # Path to input photogrammetry products
    mesh_file = Path(
        PHOTOGRAMMETRY_FOLDER, "mesh", f"mesh-internal-{dataset_id.lstrip('0')}.ply"
    )
    cameras_file = Path(
        PHOTOGRAMMETRY_FOLDER, "cameras", f"cameras-{dataset_id.lstrip('0')}.xml"
    )
    # Output files for the per-face result
    predicted_face_values_file = Path(PROJECTIONS_FOLDER, f"{dataset_id}.npy")
    top_down_vector_projection_file = Path(OUTPUT_FOLDER, f"{dataset_id}.geojson")

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
        downsample_target=0.2,
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
