from pathlib import Path
import numpy as np
import pandas as pd
from geograypher.cameras import MetashapeCameraSet
from geograypher.meshes import TexturedPhotogrammetryMesh
from geograypher.meshes.derived_meshes import TexturedPhotogrammetryMeshChunked

from geograypher.predictors.derived_segmentors import LookUpSegmentor
from geograypher.cameras.segmentor import SegmentorPhotogrammetryCameraSet
from geograypher.utils.indexing import find_argmax_nonzero_value
from geograypher.utils.geospatial import ensure_projected_CRS
from geograypher.entrypoints.aggregate_images import aggregate_images

import geopandas as gpd
import matplotlib.pyplot as plt
from urllib.request import urlretrieve


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

CYVERSE_URL_STUB = (
    "https://data.cyverse.org/dav-anon/iplant/projects/ofo/public/missions/"
)
ALL_IMAGES_FOLDER = "/ofo-share/drone-imagery-organization/3_sorted-notcleaned-combined"
DOWNLOADS_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data/"
OUTPUT_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data/geograypher_outputs"


def project_dataset(dataset_id, processed_folder, nrs_year):
    # Compute relavent paths based on dataset
    images_folder = Path(ALL_IMAGES_FOLDER, f"{nrs_year}-ucnrs", dataset_id)
    labels_folder = Path(
        f"/ofo-share/scratch-david/NRS-all-sites/preds/ucnrs-{nrs_year}/{dataset_id}"
    )
    top_down_vector_projection_file = Path(
        OUTPUT_FOLDER, "geospatial_maps", f"{dataset_id}.geojson"
    )
    predicted_face_values_file = Path(OUTPUT_FOLDER, "face_values", f"{dataset_id}.npy")

    cyverse_processed_url = "/".join(
        (CYVERSE_URL_STUB, dataset_id, processed_folder, "full")
    )

    cameras_url = f"{cyverse_processed_url}/cameras.xml"
    mesh_url = f"{cyverse_processed_url}/mesh-internal.ply"

    temp_mesh_file = Path(DOWNLOADS_FOLDER, "meshes", f"mesh_{dataset_id}.ply")
    temp_cameras_file = Path(
        DOWNLOADS_FOLDER, "cameras", f"cameras_file_{dataset_id}.xml"
    )

    if not Path(labels_folder).is_dir():
        print(f"Skipping {dataset_id} due to missing folder of labels")
        return

    if Path(predicted_face_values_file).is_file():
        print(f"Dataset {dataset_id} exists already. Skipping")
        return

    # Ensure that the containing folders exist to save the downloaded data into
    temp_cameras_file.parent.mkdir(exist_ok=True, parents=True)
    temp_mesh_file.parent.mkdir(exist_ok=True, parents=True)

    # Download the mesh and cameras files
    urlretrieve(cameras_url, temp_cameras_file)
    print("retrieved cameras")
    urlretrieve(mesh_url, temp_mesh_file)
    print("retrieved mesh")

    try:
        aggregate_images(
            temp_mesh_file,
            temp_cameras_file,
            images_folder,
            labels_folder,
            original_image_folder=images_folder,
            IDs_to_labels=IDS_TO_LABELS,
            aggregated_face_values_savefile=predicted_face_values_file,
            top_down_vector_projection_savefile=top_down_vector_projection_file,
            mesh_downsample=0.2,
            aggregate_image_scale=0.25,
            take_every_nth_camera=1,
        )
    except:
        print(f"Dataset {dataset_id} failed")


processing_ids = pd.read_csv(
    "/ofo-share/repos-david/UCNRS-experiments/data/processed_ids.csv"
)

for _, row in processing_ids.iterrows():
    dataset_id = f"{row.dataset_id:06}"
    processed_id = row.processed_path

    if dataset_id <= "000580":
        nrs_year = "2020"
    elif dataset_id <= "000630":
        nrs_year = "2023"
    else:
        nrs_year = "2024"

    print(dataset_id, processed_id, nrs_year)

    project_dataset(
        dataset_id=dataset_id, processed_folder=processed_id, nrs_year=nrs_year
    )
