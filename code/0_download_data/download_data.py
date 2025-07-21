import shutil
import sys
import tempfile
from pathlib import Path

import geopandas as gpd
from rclone_python import rclone

# Add folder where constants.py is to system search path
sys.path.append(str(Path(Path(__file__).parent, "..").resolve()))
from constants import (
    ALL_IMAGES_FOLDER,
    CAMERAS_FOLDER,
    CHMS_FOLDER,
    MESHES_FOLDER,
    METADATA_FILE,
    ORTHOS_FOLDER,
)

REMOTE = "js2s3"
DOWNLOAD_PHOTOGRAMMETRY = False
DOWNLOAD_IMAGES = True

# Read in a list of datasets that need to be downloaded
metadata = gpd.read_file(METADATA_FILE)

# Extract the mission IDs
mission_ids = metadata.mission_id.tolist()

# Make output directories
[
    folder.mkdir(exist_ok=True, parents=True)
    for folder in (
        CAMERAS_FOLDER,
        CHMS_FOLDER,
        MESHES_FOLDER,
        ORTHOS_FOLDER,
        ALL_IMAGES_FOLDER,
    )
]

if DOWNLOAD_PHOTOGRAMMETRY:
    # Iterate over missions and download the four photogrammetry products
    for mission_id in mission_ids:
        photogrammetry_path_remote = (
            f"{REMOTE}:/ofo-public/drone/missions_01/{mission_id}/processed_02/full/"
        )

        # TODO do error checking to ensure the data was actually downloaded

        # Copy the cameras
        camera_path_remote = photogrammetry_path_remote + f"{mission_id}_cameras.xml"
        camera_path_local = Path(CAMERAS_FOLDER, f"{mission_id}.xml")

        rclone.copy(camera_path_remote, camera_path_local)

        # Copy the CHMs
        CHM_path_remote = photogrammetry_path_remote + f"{mission_id}_chm-ptcloud.tif"
        CHM_path_local = Path(CHMS_FOLDER, f"{mission_id}.tif")

        rclone.copy(CHM_path_remote, CHM_path_local)

        # Copy the mesh
        mesh_path_remote = photogrammetry_path_remote + f"{mission_id}_model-local.ply"
        mesh_path_local = Path(MESHES_FOLDER, f"{mission_id}.ply")

        rclone.copy(mesh_path_remote, mesh_path_local)

        # Copy the ortho
        ortho_path_remote = (
            photogrammetry_path_remote + f"{mission_id}_ortho-dsm-ptcloud.tif"
        )
        ortho_path_local = Path(ORTHOS_FOLDER, f"{mission_id}.tif")

        rclone.copy(ortho_path_remote, ortho_path_local)

        # Copy the images
        images_path_remote = ()
        images_path_local = Path(ALL_IMAGES_FOLDER, mission_id)

# This will re-run even if the data exists because the
if DOWNLOAD_IMAGES:
    for mission_id in mission_ids:
        images_path_remote = f"{REMOTE}:/ofo-public/drone/missions_01/{mission_id}/images/{mission_id}_images.zip"

        # Create a temporary directory because a tempfile creates a managed object that can't be
        # written to in the same wawy
        temp_dir = tempfile.TemporaryDirectory(dir="/ofo-share/tmp")
        # Create a filepath within the folder
        zipfile = str(Path(str(temp_dir.name), f"{mission_id}.zip"))
        # To match the format, the top level `mission_id` must be included
        images_output_folder = Path(ALL_IMAGES_FOLDER, mission_id)
        print(f"Downloading to {zipfile}")
        # Download the zip file
        # TODO determine why `copyto` vs. `copy` is required. The latter creates a directory with
        # the .zip extension then creates the file with the original name within it.
        rclone.copyto(images_path_remote, zipfile)
        print("About to unpack the zip file")
        # Unzip the zip file
        shutil.unpack_archive(zipfile, images_output_folder)
        # Once the temp_dir variables is overwritten the object will go out of scope and the
        # temp dir will be deleted
