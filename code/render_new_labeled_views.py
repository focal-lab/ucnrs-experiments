from pathlib import Path
import numpy as np
from geograypher.cameras import MetashapeCameraSet
from geograypher.meshes import TexturedPhotogrammetryMesh
from geograypher.meshes.derived_meshes import TexturedPhotogrammetryMeshChunked

from geograypher.predictors.derived_segmentors import LookUpSegmentor
from geograypher.cameras.segmentor import SegmentorPhotogrammetryCameraSet
from geograypher.utils.indexing import find_argmax_nonzero_value
from geograypher.utils.geospatial import ensure_projected_CRS

import geopandas as gpd
import matplotlib.pyplot as plt


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


def project_labels(
    cameras_file,
    images_path,
    mesh_file,
    labels_folder,
    subset_saved_images_folder,
    renders_folder,
    ids_to_labels,
    camera_buffer_dist=50,
    mesh_buffer_dist=100,
    render_downsample=0.2,
):
    # Create the camera set
    cameras = MetashapeCameraSet(cameras_file, images_path, images_path)

    # Create the lookup segmentor can camera set
    segmentor = LookUpSegmentor(images_path, labels_folder)
    segmentor_camera_set = SegmentorPhotogrammetryCameraSet(
        cameras, segmentor=segmentor
    )
    # Only a subset of the images are labeled, so extract a camera set object corresponding to
    # only those images
    segmentor_camera_set = segmentor_camera_set.get_subset_with_valid_segmentation()

    # Create an ROI to subset the cam
    camera_locations = segmentor_camera_set.get_lon_lat_coords()
    lon, lat = zip(*camera_locations)
    ROI = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon, lat), crs=4326)
    ROI = ensure_projected_CRS(ROI)

    # Create the mesh that will be used for aggregation
    aggregation_mesh = TexturedPhotogrammetryMesh(
        mesh_file,
        transform_filename=cameras_file,
        ROI=ROI,
        ROI_buffer_meters=mesh_buffer_dist,
    )
    # Project the labels onto the mesh
    average_projection, _ = aggregation_mesh.aggregate_projected_images(
        segmentor_camera_set, aggregate_img_scale=render_downsample
    )

    # Get the most common class for each face
    projected_labels_class = find_argmax_nonzero_value(average_projection)
    # Save out the projection information
    Path(renders_folder).mkdir(exist_ok=True, parents=True)
    np.save(Path(renders_folder, "labels.npy"), projected_labels_class)
    aggregation_mesh.vis(
        vis_scalars=projected_labels_class,
        camera_set=segmentor_camera_set,
        screenshot_filename=Path(renders_folder, "aggregated_mesh_vis.png"),
        IDs_to_labels=ids_to_labels,
    )

    # Now create a second mesh for rendering out the texture for un-labeled perspectives
    labeled_mesh = TexturedPhotogrammetryMesh(
        mesh_file,
        transform_filename=cameras_file,
        texture=projected_labels_class,
        IDs_to_labels=ids_to_labels,
        ROI=ROI,
        ROI_buffer_meters=mesh_buffer_dist,
    )

    # Subset the cameras to the regions around the labeled cameras
    render_cameras = cameras.get_subset_ROI(ROI, buffer_radius=camera_buffer_dist)
    # Symlink a folder of images that correspond to the labels we will create
    render_cameras.save_images(subset_saved_images_folder)

    labeled_mesh.vis(
        camera_set=render_cameras,
        screenshot_filename=Path(renders_folder, "render_mesh_vis.png"),
    )

    # Save out the labels
    labeled_mesh.save_renders(
        camera_set=render_cameras,
        output_folder=renders_folder,
        render_image_scale=render_downsample,
        save_native_resolution=True,
    )


DATASETS = (
    # "000479",
    # "000544",
    # "000545",
    # "000546",
    # "000547",
    # "000548",
    # "000549",
    # "000550",
    # "000551",
    # "000552",
    # "000553",
    # "000554",
    # "000555",
    # "000556",
    # "000557",
    # "000558",
    # "000559",
    # "000560",
    # "000561",
    # "000562",
    # "000563",
    # "000564",
    # "000565",
    # "000566",
    # "000567",
    # "000568",
    # "000569",
    # "000570",
    # "000571",
    # "000572",
    # "000573",
    # "000574",
    # "000575",
    # "000576",
    # "000577",
    # "000578",
    # "000579",
    # "000580",
    # "000581",
    # "000582",
    # "000583",
    # "000584",
    # "000585",
    # "000586",
    # "000587",
    # "000588",
    # "000610",
    # "000611",
    # "000612",
    # "000613",
    # "000614",
    # "000615",
    # "000616",
    # "000617",
    # "000618",
    # "000619",
    # "000620",
    # "000621",
    # "000622",
    # "000623",
    # "000624",
    # "000625",
    # "000626",
    # "000627",
    # "000628",
    # "000629",
    # "000630",
    # "000841",
    # "000908",
    # "000909",
    # "000910",
    # "000911",
    # "000912",
    # "000913",
    # "000914",
    # "000915",
    # "000916",
    # "000917",
    # "000918",
    # "000919",
    "000920",
    "000921",
    "000922",
    "000923",
    "000924",
    "000925",
    "000926",
    "000927",
    "000928",
    "000929",
    "000930",
    "000931",
)

for dataset in DATASETS:
    labels_folder = f"/ofo-share/repos-david/UCNRS-experiments/data/labels/labeled_images_12_17_merged_classes_standardized/{dataset}"

    if not Path(labels_folder).is_dir():
        print(f"skipping {dataset} since there are no labels")
        continue

    if int(dataset[3:]) <= 588:
        year = "2020"
    elif int(dataset[3:]) <= 841:
        year = "2023"
    else:
        year = "2024"

    images_path = f"/ofo-share/drone-imagery-organization/3_sorted-notcleaned-combined/{year}-ucnrs/{dataset}"

    photogrammetry_folders = sorted(
        Path(f"/ofo-share/drone-data-publish/01/{dataset}").glob("processed*")
    )
    if len(photogrammetry_folders) < 1:
        continue
    photogrammetry_folder = Path(photogrammetry_folders[-1], "full")
    mesh_file = Path(photogrammetry_folder, "mesh-internal.ply")
    cameras_file = Path(photogrammetry_folder, "cameras.xml")

    subset_saved_images_folder = Path(
        f"/ofo-share/scratch-david/NRS-multi-year/rendered_labels/{dataset}/images"
    )
    renders_folder = Path(
        f"/ofo-share/scratch-david/NRS-multi-year/rendered_labels/{dataset}/renders"
    )

    try:
        print(f"Trying dataset {dataset}")
        project_labels(
            cameras_file=cameras_file,
            images_path=images_path,
            mesh_file=mesh_file,
            labels_folder=labels_folder,
            subset_saved_images_folder=subset_saved_images_folder,
            renders_folder=renders_folder,
            ids_to_labels=IDS_TO_LABELS,
        )
    except:
        print(f"dataset {dataset} failed")
