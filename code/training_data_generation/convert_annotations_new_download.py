from mmseg_utils.dataset_creation.parsing import parse_viame_annotations_dataset
import json
from mmseg_utils.dataset_creation.folder_to_cityscapes import folder_to_cityscapes
from pathlib import Path

DOWNLOAD_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data/labels/VIAME_download"
OUTPUT_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data/labels/merged_classes"
CITYSCAPE_FORMATTED_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data/labels/merged_classes_cityscapes_formatted"

CLASS_MAP = "/ofo-share/repos-david/UCNRS-experiments/data/labels/class_map_merged.json"

CLASS_NAMES = [
    "BE_bare_earth",
    "HL_herbaceous_live",
    "MM_man_made_object",
    "SD_shrub_dead",
    "SL_shrub_live",
    "TD_tree_dead",
    "TL_tree_live",
    "W_water",
]

if False:
    annotation_files = sorted(Path(DOWNLOAD_FOLDER).rglob("*/*.csv"))
    for annotation_file in annotation_files:
        chunk_str = annotation_file.parts[-2]
        site_year = annotation_file.parts[-3]
        image_folder = annotation_file.parent

        site, year = site_year.split("_")
        chunk = chunk_str[6:]

        print(f"Processing {site}, {year}, {chunk}")

        output_folder = Path(OUTPUT_FOLDER, site_year, chunk_str)
        parse_viame_annotations_dataset(
            image_folder=image_folder,
            annotation_file=annotation_file,
            output_folder=output_folder,
            class_map=CLASS_MAP,
        )

if True:
    with open(CLASS_MAP, "r") as infile:
        class_map = json.load(infile)

    class_map.pop("unknown")
    class_names = list(class_map.keys())

    folder_to_cityscapes(
        images_folder=DOWNLOAD_FOLDER,
        labels_folder=OUTPUT_FOLDER,
        image_ext="JPG",
        label_ext="png",
        train_frac=0.8,
        val_frac=0.2,
        output_folder=CITYSCAPE_FORMATTED_FOLDER,
        remove_old=True,
        classes=CLASS_NAMES,
        vis_number=80,
    )
