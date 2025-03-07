from pathlib import Path
import hashlib
from tqdm import tqdm
import itertools
import glob

import json

# Where all the images are stored, organized by projects
ALL_IMAGES_FOLDER = "/ofo-share/drone-imagery-organization/3_sorted-notcleaned-combined"

# Where the original images and "linking.json" files are
IMAGE_SUBSET_FOLDER = Path("/ofo-share/scratch-david/NRS_labeling/image_subset")

IMAGE_EXTENSIONS = ("JPG", "jpg")

OUTPUT_FILE = "data/subset_to_all_images_mapping.json"


# taken from https://www.geeksforgeeks.org/python-program-to-find-hash-of-file/
def compute_file_hash(file_path, algorithm="sha256"):
    """Compute the hash of a file using the specified algorithm."""
    hash_func = hashlib.new(algorithm)

    with open(file_path, "rb") as file:
        # Read the file in chunks of 8192 bytes
        while chunk := file.read(8192):
            hash_func.update(chunk)

    return hash_func.hexdigest()


# The first step is to find all of the files in the folder with any of the specified extensions.
# Then the hashes of each file are computed. This is returned as a dictionary mapping from the hash
# value to the file path of the image, or vice-versa if hash_to_file is specified.
def get_file_hash_dict(folder_path, extensions, hash_to_file=False):
    all_files = list(
        itertools.chain(
            *[
                list(glob.glob(f"{folder_path}/**/*.{ext}", recursive=True))
                for ext in (extensions)
            ]
        )
    )
    mapping_dict = {f: compute_file_hash(f) for f in tqdm(all_files)}

    if hash_to_file:
        mapping_dict = {v: k for k, v in mapping_dict.items()}

    return mapping_dict


# This is a mapping from filename to the associated hash
subset_hashes = get_file_hash_dict(IMAGE_SUBSET_FOLDER, IMAGE_EXTENSIONS)

# For each of the three folders of years, compute the mapping. This time it is hash to filename,
# since the files are assumed to be unique. In contrast, the multiple filenames in the subset refer
# to the same image because some were annotated by both Ellyn and later interns.
all_images_dict = get_file_hash_dict(f"{ALL_IMAGES_FOLDER}/2020-ucnrs", IMAGE_EXTENSIONS, hash_to_file=True)
all_images_dict.update(get_file_hash_dict(f"{ALL_IMAGES_FOLDER}/2023-ucnrs", IMAGE_EXTENSIONS, hash_to_file=True))
all_images_dict.update(get_file_hash_dict(f"{ALL_IMAGES_FOLDER}/2024-ucnrs", IMAGE_EXTENSIONS, hash_to_file=True))

# For each image in the subset, find the image in the full set with the same hash. Since we're using
# the .get method, missing keys will return None.
subset_to_all_mappings = {k: all_images_dict.get(v) for k, v in subset_hashes.items()}
# Determine which files had a match
valid_mappings = {k: v for k, v in subset_to_all_mappings.items() if v is not None}

if len(subset_to_all_mappings) > len(valid_mappings):
    print(f"WARNING: {len(subset_to_all_mappings) - len(valid_mappings)} files in the subset did not have a correspondence")

# Write the mapping to disk
with open(OUTPUT_FILE, "w") as outfile:
    json.dump(valid_mappings, outfile)
