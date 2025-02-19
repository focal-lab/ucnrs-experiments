from pathlib import Path
import pandas as pd

from geograypher.meshes import TexturedPhotogrammetryMesh
from geograypher.cameras import MetashapeCameraSet

# A file containing all the dataset IDs
PROCESSING_IDS_FILE = "/ofo-share/repos-david/UCNRS-experiments/data/processed_ids.csv"
# Path to the folder of images used for photogrammetry
ALL_IMAGES_FOLDER = "/ofo-share/drone-imagery-organization/3_sorted-notcleaned-combined"
# Where the input photogrammetry products are
PHOTOGRAMMETRY_PRODUCTS_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data/"
# Where to save the results
OUTPUT_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data/geograypher_outputs/CHM_pointcloud_renders_vis"

# Should the dataset be skipped if the output folder exists already
SKIP_EXISTING = True
# This controls the fidelity of the rendering by rendering as if the image were captured at this
# fraction of the original resolution. A lower value results in faster runtimes and less space on
# disk, but a smoother, less detailed rendered CHM image.
RENDER_SCALE = 0.1
# Subsample the cameras to 1 out of this number. Useful for testing.
TAKE_EVERY_NTH_CAMERA = 100
# Show the rendered data alongside the original image. Useful for testing.
MAKE_COMPOSITE = True
# Should the mesh be shown
VIS_MESH = True
# The first dataset is very large, so it can be useful to skip it for experiments
START_INDEX = 10
# Should the pointcloud be used for the CHM values rather than the mesh
USE_POINTCLOUD_CHM = True


def render_chm(
    dataset_id,
    nrs_year,
    skip_existings=False,
    vis=VIS_MESH,
    take_every_nth_camera=TAKE_EVERY_NTH_CAMERA,
    make_composite=MAKE_COMPOSITE,
    use_point_cloud_CHM=True,
):
    # Compute relavent paths based on dataset
    # Path to the raw images
    images_folder = Path(ALL_IMAGES_FOLDER, f"{nrs_year}-ucnrs", dataset_id)
    # Path to input photogrammetry products
    mesh_file = Path(
        PHOTOGRAMMETRY_PRODUCTS_FOLDER, "mesh", f"mesh-internal-{dataset_id[3:]}.ply"
    )
    cameras_file = Path(
        PHOTOGRAMMETRY_PRODUCTS_FOLDER, "cameras", f"cameras-{dataset_id[3:]}.xml"
    )
    dtm_file = Path(
        PHOTOGRAMMETRY_PRODUCTS_FOLDER, "DTM", f"dtm-ptcloud-{dataset_id[3:]}.tif"
    )
    chm_file = Path(
        PHOTOGRAMMETRY_PRODUCTS_FOLDER, "CHM", f"chm-ptcloud-{dataset_id[3:]}.tif"
    )

    # Match the format of the input imagery for easy post-processing
    rendered_CHMs_folder = Path(OUTPUT_FOLDER, f"{nrs_year}-ucnrs", dataset_id)

    if not images_folder.is_dir():
        print(
            f"Skipping {dataset_id} because there is no corresponding folder of images"
        )
        return

    if skip_existings and rendered_CHMs_folder.is_dir():
        print(f"Skipping {dataset_id} because output folder exists")
        return

    # Load the mesh and the cameras
    mesh = TexturedPhotogrammetryMesh(mesh_file, transform_filename=cameras_file)
    cameras = MetashapeCameraSet(
        camera_file=cameras_file,
        image_folder=images_folder,
        original_image_folder=images_folder,
    )

    if use_point_cloud_CHM:
        # This option is using the pointcloud CHM
        mesh.load_texture(texture=chm_file)
    else:
        # This option is using the mesh CHM
        # Compute the height of each mesh vertex above the DTM ground estimate
        height_above_ground = mesh.get_height_above_ground(dtm_file)
        # Set the height above ground as the per-vertex texture
        mesh.load_texture(height_above_ground)

    # If requested, take only every nth camera in the set.
    if take_every_nth_camera != 1:
        cameras = cameras.get_subset_cameras(
            range(0, len(cameras), take_every_nth_camera)
        )

    if vis:
        mesh.vis(camera_set=cameras)

    try:
        # Save out the renders of height-above-ground from each perspective
        mesh.save_renders(
            cameras,
            render_image_scale=RENDER_SCALE,
            output_folder=rendered_CHMs_folder,
            save_native_resolution=False,
            cast_to_uint8=False,
            make_composites=make_composite,
        )
    except Exception as e:
        print(f"Dataset {dataset_id} failed with the following exception: {e}")


# Load the list of dataset IDs
processing_ids = pd.read_csv(PROCESSING_IDS_FILE)
for _, row in processing_ids.iloc[START_INDEX:, :].iterrows():
    # Format the dataset ID
    dataset_id = f"{row.dataset_id:06}"

    # Determine which year of data collections it corresponds to
    if dataset_id <= "000580":
        nrs_year = "2020"
    elif dataset_id <= "000630":
        nrs_year = "2023"
    else:
        nrs_year = "2024"

    # Render the CHMs for that dataset
    render_chm(
        dataset_id=dataset_id,
        nrs_year=nrs_year,
        skip_existings=SKIP_EXISTING,
        use_point_cloud_CHM=USE_POINTCLOUD_CHM,
    )
