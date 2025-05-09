from pathlib import Path
import geopandas as gpd
import sys

from geograypher.entrypoints.aggregate_images import aggregate_images

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    ALL_IMAGES_FOLDER,
    PER_IMAGE_PREDICTIONS_FOLDER,
    PHOTOGRAMMETRY_FOLDER,
    OUTPUT_FOLDER,
    IDS_TO_LABELS,
    MESH_DOWNSAMPLE,
    METADATA_FILE,
    N_CAMERAS_PER_CHUNK,
    SKIP_EXISTING,
    AGGREGATION_IMAGE_SCALE,
)


def project_dataset(dataset_id, skip_existings=False):
    # Compute relavent paths based on dataset
    # Path to the raw images
    images_folder = Path(ALL_IMAGES_FOLDER, dataset_id)
    # Path to the predictions from the model
    labels_folder = Path(PER_IMAGE_PREDICTIONS_FOLDER, dataset_id)

    # Path to input photogrammetry products
    mesh_file = Path(
        PHOTOGRAMMETRY_FOLDER, "mesh", f"mesh-internal-{dataset_id.lstrip('0')}.ply"
    )
    cameras_file = Path(
        PHOTOGRAMMETRY_FOLDER, "cameras", f"cameras-{dataset_id.lstrip('0')}.xml"
    )
    # Output files for the per-face result
    predicted_face_values_file = Path(OUTPUT_FOLDER, f"{dataset_id}.npy")

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
