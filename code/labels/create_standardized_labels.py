from pathlib import Path
import json
import shutil
import pprint

MAPPING_FILE = Path(
    "/ofo-share/repos-david/UCNRS-experiments/data/subset_to_all_images_mapping.json"
)

LABELED_IMAGES_FOLDER = Path(
    "/ofo-share/repos-david/UCNRS-experiments/data/labels/merged_classes"
)
STANDARDIZED_LABELED_IMAGES_FOLDER = Path(
    "/ofo-share/repos-david/UCNRS-experiments/data/labels/merged_classes_standardized"
)

INITIAL_LOCATION = "/ofo-share/scratch-david/NRS_labeling/image_subset"

FULL_FOLDER = "/ofo-share/drone-imagery-organization/3_sorted-notcleaned-combined"

with open(MAPPING_FILE, "r") as infile:
    mapping = json.load(infile)

mapping = {Path(k).with_suffix(""): v for k, v in mapping.items()}

files = sorted([f for f in (LABELED_IMAGES_FOLDER.rglob("*")) if f.is_file()])

for file in files:
    key = Path(
        str(file).replace(str(LABELED_IMAGES_FOLDER), INITIAL_LOCATION)
    ).with_suffix("")
    if key in mapping:
        value = mapping[key]
        value = Path(
            value.replace(str(FULL_FOLDER), str(STANDARDIZED_LABELED_IMAGES_FOLDER))
        ).with_suffix(".png")
        value.parent.mkdir(parents=True, exist_ok=True)
        #print(f"Copying {file} {value}")
        shutil.copy(file, value)
    else:
        print(f"Skipping {key}")
