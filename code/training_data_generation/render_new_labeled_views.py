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

OUTPUT_FOLDER = (
    "/ofo-share/repos-david/UCNRS-experiments/data/labels/geograypher_rendered_fixed"
)
PHOTOGRAMMETRY_FOLDER = (
    "/ofo-share/repos-david/UCNRS-experiments/data/photogrammetry_products"
)
IMAGES_FOLDER = "/ofo-share/drone-imagery-organization/3_sorted-notcleaned-combined"
LABELS_FOLDER = (
    "/ofo-share/repos-david/UCNRS-experiments/data/labels/merged_classes_standardized/"
)

CAMERA_BUFFER_DIST = 75
MESH_BUFFER_DIST = 200

DATASETS = (
    #"000582",
    #"000583",
    #"000584",
    #"000585",
    #"000586",
    #"000587",
    #"000588",
    "001336",
    "001337",
)


def project_labels(
    cameras_file,
    images_path,
    mesh_file,
    labels_folder,
    subset_saved_images_folder,
    renders_folder,
    ids_to_labels,
    camera_buffer_dist=CAMERA_BUFFER_DIST,
    mesh_buffer_dist=MESH_BUFFER_DIST,
    render_downsample=0.2,
    take_every_nth_image=1,
    n_cameras_per_chunk=100,
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
    labeled_mesh = TexturedPhotogrammetryMeshChunked(
        mesh_file,
        transform_filename=cameras_file,
        texture=projected_labels_class,
        IDs_to_labels=ids_to_labels,
        ROI=ROI,
        ROI_buffer_meters=mesh_buffer_dist,
    )

    # Subset the cameras to the regions around the labeled cameras
    render_cameras = cameras.get_subset_ROI(ROI, buffer_radius=camera_buffer_dist)

    render_cameras = render_cameras.get_subset_cameras(
        range(0, len(render_cameras), take_every_nth_image)
    )

    # Symlink a folder of images that correspond to the labels we will create
    render_cameras.save_images(subset_saved_images_folder)

    labeled_mesh.vis(
        camera_set=render_cameras,
        screenshot_filename=Path(renders_folder, "render_mesh_vis.png"),
    )

    n_chunks = int(np.ceil(len(render_cameras) / n_cameras_per_chunk))

    # Save out the labels
    labeled_mesh.save_renders(
        camera_set=render_cameras,
        output_folder=renders_folder,
        render_image_scale=render_downsample,
        save_native_resolution=True,
        make_composites=False,
        n_clusters=n_chunks,
    )


for dataset in DATASETS:
    dataset_no_leading_z = dataset.replace("0", "")
    if int(dataset_no_leading_z) <= 588 or int(dataset_no_leading_z) >=1336:
        year = "2020"
    elif int(dataset[3:]) <= 841:
        year = "2023"
    else:
        year = "2024"

    images_path = Path(IMAGES_FOLDER, f"{year}-ucnrs", f"{dataset}")
    labels_folder = Path(LABELS_FOLDER, f"{year}-ucnrs", f"{dataset}")

    if not Path(labels_folder).is_dir():
        print(f"skipping {dataset} since there are no labels")
        continue

    mesh_file = Path(
        PHOTOGRAMMETRY_FOLDER,
        "mesh",
        f"mesh-internal-{dataset[2:]}.ply",
    )
    cameras_file = Path(
        PHOTOGRAMMETRY_FOLDER,
        "cameras",
        f"cameras-{dataset[2:]}.xml",
    )
    subset_saved_images_folder = Path(OUTPUT_FOLDER, f"{dataset}/images")
    renders_folder = Path(OUTPUT_FOLDER, f"{dataset}/renders")

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
            take_every_nth_image=1,
        )
    except Exception as e:
        print(f"dataset {dataset} failed")
        print(e)
