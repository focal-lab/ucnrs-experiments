from pathlib import Path


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
MESH_DOWNSAMPLE = 0.2
AGGREGATION_IMAGE_SCALE = 0.25

N_CAMERAS_PER_CHUNK = 100
SKIP_EXISTING = True

# This can be replaced with an alternative absolute path if your data is in a different location
DATA_FOLDER = Path(Path(__file__).parent, "..", "data").resolve()

ALL_IMAGES_FOLDER = Path(DATA_FOLDER, "inputs", "images")
PHOTOGRAMMETRY_FOLDER = Path(DATA_FOLDER, "inputs", "photogrammetry")
PER_IMAGE_PREDICTIONS_FOLDER = Path(
    DATA_FOLDER, "intermediate", "per_image_predictions"
)
METADATA_FILE = Path(DATA_FOLDER, "inputs", "mission_metadata.gpkg")
OUTPUT_FOLDER = Path(DATA_FOLDER, "intermediate", "projections_to_faces")
