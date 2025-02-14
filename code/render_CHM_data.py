from pathlib import Path
import pandas as pd

from geograypher.meshes import TexturedPhotogrammetryMesh
from geograypher.cameras import MetashapeCameraSet


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
DOWNLOADS_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data/"
OUTPUT_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data/geograypher_outputs"

SKIP_EXISTING = False
RENDER_SCALE = 0.1


def render_chm(dataset_id, nrs_year, skip_existings=False):
    # Compute relavent paths based on dataset
    # Path to the raw images
    images_folder = Path(ALL_IMAGES_FOLDER, f"{nrs_year}-ucnrs", dataset_id)
    # Path to input photogrammetry products
    mesh_file = Path(DOWNLOADS_FOLDER, "mesh", f"mesh-internal-{dataset_id[3:]}.ply")
    cameras_file = Path(DOWNLOADS_FOLDER, "cameras", f"cameras-{dataset_id[3:]}.xml")
    dtm_file = Path(DOWNLOADS_FOLDER, "DTM", f"dtm-ptcloud-{dataset_id[3:]}.tif")

    # Match the format of the input imagery for easy post-processing
    rendered_CHMs_folder = Path(
        OUTPUT_FOLDER, "CHM_renders", f"{nrs_year}-ucnrs", dataset_id
    )

    if skip_existings and rendered_CHMs_folder.is_dir():
        print(f"Skipping {dataset_id} because output folder exists")

    # Load the mesh and the cameras
    mesh = TexturedPhotogrammetryMesh(mesh_file, transform_filename=cameras_file)
    cameras = MetashapeCameraSet(
        camera_file=cameras_file,
        image_folder=images_folder,
        original_image_folder=images_folder,
    )

    # Compute the height of each mesh vertex above the DTM ground estimate
    height_above_ground = mesh.get_height_above_ground(dtm_file)
    # Set the height above ground as the per-vertex texture
    mesh.load_texture(height_above_ground)

    # Save out the renders of height-above-ground from each perspective
    mesh.save_renders(
        cameras,
        render_image_scale=RENDER_SCALE,
        output_folder=rendered_CHMs_folder,
        save_native_resolution=False,
        cast_to_uint8=False,
    )


# Load the list of dataset IDs
processing_ids = pd.read_csv(PROCESSING_IDS_FILE)
for _, row in list(processing_ids.iterrows())[3:]:
    dataset_id = f"{row.dataset_id:06}"
    processed_id = row.processed_path

    if dataset_id <= "000580":
        nrs_year = "2020"
    elif dataset_id <= "000630":
        nrs_year = "2023"
    else:
        nrs_year = "2024"

    render_chm(
        dataset_id=dataset_id,
        nrs_year=nrs_year,
        skip_existings=SKIP_EXISTING,
    )
