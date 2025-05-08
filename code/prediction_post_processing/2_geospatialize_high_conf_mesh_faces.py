from pathlib import Path
import pandas as pd
import numpy as np

from geograypher.utils.indexing import find_argmax_nonzero_value
from geograypher.meshes import TexturedPhotogrammetryMesh
from geograypher.entrypoints.aggregate_images import aggregate_images


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

PROCESSING_IDS_FILE = "/ofo-share/repos-david/UCNRS-experiments/data/processed_ids.csv"
ALL_IMAGES_FOLDER = "/ofo-share/drone-imagery-organization/3_sorted-notcleaned-combined"
DOWNLOADS_FOLDER = (
    "/ofo-share/repos-david/UCNRS-experiments/data/photogrammetry_products"
)
OUTPUT_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data/geograypher_outputs"
ALL_LABELS_FOLDER = "/ofo-share/scratch-david/NRS-all-sites/preds_flipped"

N_CAMERAS_PER_CHUNK = 100

SKIP_EXISTING = False

DATASET_IDS = [
    544,
    545,
    546,
    547,
    548,
    549,
    551,
    555,
    #    557,
    558,
    563,
    564,
    565,
    566,
    567,
    568,
    570,
    573,
    574,
    #    575,
    576,
    577,
    578,
    579,
    580,
    582,
    583,
    584,
    585,
    586,
    587,
    588,
    1336,
    1337,
    610,
    611,
    612,
    613,
    614,
    619,
    620,
    621,
    622,
    623,
    627,
    630,
    908,
    911,
    912,
    913,
    919,
    921,
    924,
    925,
    926,
    927,
    928,
    929,
    930,
    931,
    559,
    479,
]
DATASET_IDS = [576, 577, 578, 614, 913]


def project_dataset(dataset_id, nrs_year, skip_existings=False):
    # Path to input photogrammetry products
    mesh_file = Path(
        DOWNLOADS_FOLDER, "mesh", f"mesh-internal-{dataset_id.lstrip('0')}.ply"
    )
    cameras_file = Path(
        DOWNLOADS_FOLDER, "cameras", f"cameras-{dataset_id.lstrip('0')}.xml"
    )

    predicted_face_values_file = Path(OUTPUT_FOLDER, "face_values", f"{dataset_id}.npy")
    top_down_vector_projection_file = Path(
        OUTPUT_FOLDER, "geospatial_maps_high_conf", f"{dataset_id}.geojson"
    )

    if top_down_vector_projection_file.is_file():
        print(f"Skipping existing geospatial file {dataset_id}")
        return

    face_values = np.load(predicted_face_values_file)

    max_class = find_argmax_nonzero_value(face_values, keepdims=False)
    max_value = np.max(face_values, axis=1)
    max_class[max_value < 0.8] = np.nan

    mesh = TexturedPhotogrammetryMesh(
        mesh_file,
        transform_filename=cameras_file,
        texture=max_class,
        downsample_target=0.2,
        IDs_to_labels=IDS_TO_LABELS,
    )
    # mesh.vis()
    mesh.export_face_labels_vector(
        face_labels=max_class,
        export_file=top_down_vector_projection_file,
        label_names=IDS_TO_LABELS,
        vis=False,
    )


# Load the list of dataset IDs
processing_ids = pd.read_csv(PROCESSING_IDS_FILE)

# Loop over datasets
for dataset_id in DATASET_IDS:
    # row = processing_ids[processing_ids.dataset_id == dataset_id]
    # row = row.iloc[0, :]
    dataset_id = f"{dataset_id:06}"

    if dataset_id <= "000588" or dataset_id >= "001336":
        nrs_year = "2020"
    elif dataset_id <= "000630":
        nrs_year = "2023"
    else:
        nrs_year = "2024"

    project_dataset(
        dataset_id=dataset_id,
        nrs_year=nrs_year,
        skip_existings=SKIP_EXISTING,
    )
