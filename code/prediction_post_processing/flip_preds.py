from pathlib import Path

import numpy as np
from PIL import Image

INPUT_LABELS_FOLDER = Path("/ofo-share/scratch-david/NRS-all-sites/preds/")
OUTPUT_LABELS_FOLDER = Path("/ofo-share/scratch-david/NRS-all-sites/preds_flipped")
IMAGES_FOLDER = Path(
    "/ofo-share/drone-imagery-organization/3_sorted-notcleaned-combined"
)

updated_datasets = set()

for i, label_file in enumerate(sorted(INPUT_LABELS_FOLDER.rglob("*.png"))):
    if i % 1000 == 0:
        print(i)
        print(updated_datasets)
    image_path = Path(IMAGES_FOLDER, label_file.relative_to(INPUT_LABELS_FOLDER))
    output_path = Path(
        OUTPUT_LABELS_FOLDER, label_file.relative_to(INPUT_LABELS_FOLDER)
    )

    year = image_path.parts[4][-4:]

    search_path = Path(IMAGES_FOLDER, f"{year}-ucnrs", *label_file.parts[6:-1])
    search_str = label_file.stem + "*"
    files = [f for f in search_path.glob(search_str) if f.suffix in (".jpg", ".JPG")]
    if len(files) != 1:
        print(files)
        continue

    file = files[0]

    orientation = Image.open(file).getexif()[274]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if orientation == 1:
        if output_path.is_symlink():
            output_path.unlink()
        output_path.symlink_to(label_file)
    elif orientation == 3:
        label = np.asarray(Image.open(label_file))
        label = np.flip(label, (0, 1))
        Image.fromarray(label).save(output_path)
        updated_datasets.add(label_file.parts[6])
    else:
        raise ValueError()
print(updated_datasets)
