import pandas as pd
from urllib.request import urlretrieve
from pathlib import Path

import argparse

CYVERSE_URL_STUB = (
    "https://data.cyverse.org/dav-anon/iplant/projects/ofo/public/missions/"
)
PROCESSING_IDS_FILE = "/ofo-share/repos-david/UCNRS-experiments/data/processed_ids.csv"
DOWNLOADS_FOLDER = "/ofo-share/repos-david/UCNRS-experiments/data"
SKIP_EXISTING = True


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--download-type",
        nargs="+",
        choices=("CHM", "DSM", "DTM", "ortho", "mesh", "cameras"),
    )
    args = parser.parse_args()

    return args


def download_data(download_type):
    DOWNLOAD_FILE_STEM = {
        "CHM": "chm-ptcloud",
        "DSM": "dsm-ptcloud",
        "DTM": "dtm-ptcloud",
        "ortho": "orthomosaic",
        "mesh": "mesh-internal",
        "cameras": "cameras",
    }[download_type]
    DOWNLOAD_FILE_EXTENSION = {
        "CHM": "tif",
        "DSM": "tif",
        "DTM": "tif",
        "ortho": "tif",
        "mesh": "ply",
        "cameras": "xml",
    }[download_type]

    # The mapping between the dataset ID and the "processed" photogrammetry run identifier on CyVerse
    processing_ids = pd.read_csv(PROCESSING_IDS_FILE)

    for _, row in processing_ids.iterrows():
        dataset_id = f"{row.dataset_id:06}"
        processed_id = row.processed_path

        cyverse_processed_url = "/".join(
            (
                CYVERSE_URL_STUB,
                dataset_id,
                processed_id,
                "full",
                f"{DOWNLOAD_FILE_STEM}.{DOWNLOAD_FILE_EXTENSION}",
            )
        )

        output_file = f"{DOWNLOADS_FOLDER}/{download_type}/{DOWNLOAD_FILE_STEM}-{row.dataset_id}.{DOWNLOAD_FILE_EXTENSION}"

        if SKIP_EXISTING and Path(output_file).is_file():
            print(f"Skipping {output_file} since it exists already")
            continue

        # Ensure that the folder to download to exists
        Path(output_file).parent.mkdir(exist_ok=True, parents=True)
        print(f"Downloading {output_file}")
        try:
            urlretrieve(cyverse_processed_url, output_file)
        except:
            print(f"Failed to download {cyverse_processed_url}")


args = parse_args()

for download_type in args.download_type:
    download_data(download_type=download_type)
