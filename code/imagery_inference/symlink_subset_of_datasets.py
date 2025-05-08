from pathlib import Path
# Where the data sorted by mission is stored
INPUT_DIRECTORY = Path("/ofo-share/ARCHIVED_drone-imagery-organization/2_sorted")
# You can select where to create this directory
OUTPUT_DIRECTORY = Path("/ofo-share/repos-david/UCNRS-experiments/data/dataset_images")

# All the dataset IDs (padded to six digits) that we want to symlink
DATASET_IDS = [
"000479",
"000544",
"000545",
"000546",
"000547",
"000548",
"000549",
"000551",
"000555",
"000557",
"000558",
"000559",
"000563",
"000564",
"000565",
"000566",
"000567",
"000568",
"000570",
"000573",
"000574",
"000575",
"000576",
"000577",
"000578",
"000579",
"000580",
"000582",
"000583",
"000584",
"000585",
"000586",
"000587",
"000588",
"001336",
"001337",
"000610",
"000611",
"000612",
"000613",
"000614",
"000619",
"000620",
"000621",
"000622",
"000623",
"000627",
"000630",
"000908",
"000911",
"000912",
"000913",
"000919",
"000921",
"000924",
"000925",
"000926",
"000927",
"000928",
"000929",
"000930",
"000931",
]

# Create the output directory if it does not exist
OUTPUT_DIRECTORY.mkdir(exist_ok=True, parents=True)
# Link each dataset
for dataset_id in DATASET_IDS:
    dataset_target = Path(INPUT_DIRECTORY, dataset_id)
    dataset_source = Path(OUTPUT_DIRECTORY, dataset_id)
    # Create a symlink at dataset source pointing to the target
    dataset_source.symlink_to(dataset_target)