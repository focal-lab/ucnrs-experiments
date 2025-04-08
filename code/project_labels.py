from pathlib import Path
import pandas as pd

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

SKIP_EXISTING = True

DATASET_IDS = [
    544,
    545,
    546,
    547,
    548,
    549,
    551,
    555,
    557,
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
    575,
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


def project_dataset(dataset_id, nrs_year, skip_existings=False):
    # Compute relavent paths based on dataset
    # Path to the raw images
    images_folder = Path(ALL_IMAGES_FOLDER, f"{nrs_year}-ucnrs", dataset_id)
    # Path to the predictions from the model
    labels_folder = Path(ALL_LABELS_FOLDER, f"ucnrs-{nrs_year}/{dataset_id}")

    # Path to input photogrammetry products
    mesh_file = Path(
        DOWNLOADS_FOLDER, "mesh", f"mesh-internal-{dataset_id.lstrip('0')}.ply"
    )
    cameras_file = Path(
        DOWNLOADS_FOLDER, "cameras", f"cameras-{dataset_id.lstrip('0')}.xml"
    )

    # Output files for the per-face and geospaital results
    top_down_vector_projection_file = Path(
        OUTPUT_FOLDER, "geospatial_maps", f"{dataset_id}.geojson"
    )
    predicted_face_values_file = Path(OUTPUT_FOLDER, "face_values", f"{dataset_id}.npy")

    # Check if labels are present
    if not Path(labels_folder).is_dir():
        print(f"Skipping {dataset_id} due to missing folder of labels {labels_folder}")
        return

    # If we're going to skip existing results, check if they have already been computed
    if (
        skip_existings
        and predicted_face_values_file.is_file()
        and top_down_vector_projection_file.is_file()
    ):
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
        top_down_vector_projection_savefile=top_down_vector_projection_file,
        mesh_downsample=0.2,
        aggregate_image_scale=0.25,
        take_every_nth_camera=1,
        n_cameras_per_aggregation_cluster=N_CAMERAS_PER_CHUNK,
    )
    # except Exception as e:
    #    print(f"Dataset {dataset_id} failed with the following error {e}")


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
