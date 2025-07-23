import sys
from pathlib import Path

import geopandas as gpd
from geograypher.entrypoints.aggregate_images import aggregate_images

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    AGGREGATION_IMAGE_SCALE,
    ALL_IMAGES_FOLDER,
    CAMERAS_FOLDER,
    IDS_TO_LABELS,
    MESH_DOWNSAMPLE,
    MESHES_FOLDER,
    METADATA_FILE,
    N_CAMERAS_PER_CHUNK,
    PER_IMAGE_PREDICTIONS_FOLDER,
    PROJECTIONS_TO_FACES_FOLDER,
    SKIP_EXISTING,
)


def project_dataset(dataset_id, skip_existings=False):
    # Compute relavent paths based on dataset
    # Path to the raw images
    images_folder = Path(ALL_IMAGES_FOLDER, dataset_id)
    # Location of the images during the original metashape run. This must be subtracted from the
    # recorded path name
    original_image_folder = Path("/data/03_input-images", dataset_id)
    # Path to the predictions from the model
    labels_folder = Path(PER_IMAGE_PREDICTIONS_FOLDER, dataset_id)

    # Path to input photogrammetry products
    mesh_file = Path(MESHES_FOLDER, f"{dataset_id}.ply")
    cameras_file = Path(CAMERAS_FOLDER, f"{dataset_id}.xml")
    # Output files for the per-face result
    predicted_face_values_file = Path(PROJECTIONS_TO_FACES_FOLDER, f"{dataset_id}.npy")

    # Check if labels are present
    if not Path(labels_folder).is_dir():
        print(f"Skipping {dataset_id} due to missing folder of labels {labels_folder}")
        return

    # If we're going to skip existing results, check if they have already been computed
    if skip_existings and predicted_face_values_file.is_file():
        print(f"Dataset {dataset_id} exists already. Skipping")
        return

    # Actually run the aggregation step
    print(f"Running {dataset_id}")
    aggregate_images(
        mesh_file,
        cameras_file,
        images_folder,
        labels_folder,
        original_image_folder=original_image_folder,
        IDs_to_labels=IDS_TO_LABELS,
        aggregated_face_values_savefile=predicted_face_values_file,
        mesh_downsample=MESH_DOWNSAMPLE,
        aggregate_image_scale=AGGREGATION_IMAGE_SCALE,
        take_every_nth_camera=1,
        n_cameras_per_aggregation_cluster=N_CAMERAS_PER_CHUNK,
    )


metadata = gpd.read_file(METADATA_FILE)

# Loop over datasets
for dataset_id in metadata.mission_id.values:
    project_dataset(
        dataset_id=dataset_id,
        skip_existings=SKIP_EXISTING,
    )
