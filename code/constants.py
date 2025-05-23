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
CLASS_NAMES = list(IDS_TO_LABELS.values())
CLASS_ABBREVIATIONS = [x.split("_")[0] for x in CLASS_NAMES]

MESH_DOWNSAMPLE = 1
AGGREGATION_IMAGE_SCALE = 0.25

N_CAMERAS_PER_CHUNK = 100
SKIP_EXISTING = True
# geospatial export face confidence threshold
CONFIDENCE_THRESHOLD = 0.8
# Simplify the geometry such that the maximum deviation never exceeds this amount
SIMPLIFY_TOL = 0.1
BUFFER_AMOUNT = 0.2
VIS = False
TARGET_GSD = 0.25
MIN_OVERLAP_TO_REGISTER = 50 ^ 2

# Any pairwise shift greater than this value will be considered an outlier and removed
MAX_PAIRWISE_SHIFT = 10
# The weighting for each dataset to stay in the current location
CURRENT_LOCATION_WEIGHT = 0.01

# This can be replaced with an alternative absolute path if your data is in a different location
DATA_FOLDER = Path(Path(__file__).parent, "..", "data").resolve()


## inputs
METADATA_FILE = Path(DATA_FOLDER, "inputs", "mission_metadata.gpkg")
ALL_IMAGES_FOLDER = Path(DATA_FOLDER, "inputs", "images")
PHOTOGRAMMETRY_FOLDER = Path(DATA_FOLDER, "inputs", "photogrammetry")
CHMS_FOLDER = Path(PHOTOGRAMMETRY_FOLDER, "CHMs")
CAMERAS_FOLDER = Path(PHOTOGRAMMETRY_FOLDER, "cameras")
MESHES_FOLDER = Path(PHOTOGRAMMETRY_FOLDER, "meshes")
ORTHOS_FOLDER = Path(PHOTOGRAMMETRY_FOLDER, "orthos")
TRAINING_IMAGES_FOLDER = Path(DATA_FOLDER, "inputs", "TODO")
TRAINING_LABELS_FOLDER = Path(DATA_FOLDER, "inputs", "TODO")

## intermediate
WORK_DIR = Path(DATA_FOLDER, "intermediate", "training_results")
CITYSCAPES_FORMATTED_TRAINING_DATA = Path(
    DATA_FOLDER, "intermediate", "model_train_val_dataset"
)
PER_IMAGE_PREDICTIONS_FOLDER = Path(
    DATA_FOLDER, "intermediate", "per_image_predictions"
)
PROJECTIONS_TO_FACES_FOLDER = Path(DATA_FOLDER, "intermediate", "projections_to_faces")
PROJECTIONS_TO_GEOSPATIAL_FOLDER = Path(
    DATA_FOLDER, "intermediate", "projections_to_geospatial"
)
SHIFTS_PER_DATASET = Path(DATA_FOLDER, "intermediate", "shift_per_dataset.json")
POST_PROCESSED_MAPS_FOLDER = Path(DATA_FOLDER, "intermediate", "post_processed_maps")
SHIFTED_MAPS_FOLDER = Path(DATA_FOLDER, "intermediate", "shifted_maps")
PAIRWISE_SHIFTS_FILE = Path(DATA_FOLDER, "intermediate", "pairwise_registration.gpkg")
ABSOLUTE_SHIFTS_FILE = Path(DATA_FOLDER, "intermediate", "shift_per_dataset.json")

## outputs
SHIFTED_MAPS_FOLDER = Path(DATA_FOLDER, "outputs", "shifted_maps")
SHIFTED_ORTHOS_FOLDER = Path(DATA_FOLDER, "outputs", "shifted_orthos")
MERGED_MAPS_FOLDER = Path(DATA_FOLDER, "outputs", "merged_maps")
MERGED_CLIPPED_MAPS_FOLDER = Path(DATA_FOLDER, "outputs", "merged_clipped_maps")
TRANSITION_MATRICES_FOLDER = Path(DATA_FOLDER, "outputs", "transition_matrices")
TRANSITION_MATRIX_PLOTS_FOLDER = Path(
    DATA_FOLDER, "outputs", "transition_matrices_plots"
)
