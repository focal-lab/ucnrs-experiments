# Overview
This repository contains the processing steps to replicate experiments on a vegetation mapping task using UAV imagery. This project was conducted at three sites within the University of California Natural Reserve System ([UCNRS](https://ucnrs.org/)). Imagery was collected during 60 UAV missions flown in 2020, 2023, and 2024. The objective was to study post-fire vegetation dynamics following fires that occured at all three reserves in 2020, prior to when any imagery was collected.

# Install
These experiments rely on functionality from several projects, many developed by the [Open Forest Observatory](https://openforestobservatory.org/). Because they have incompatible dependencies, you will need to create multiple separate conda environments for various steps. You will largely follow the instructions provided in the README file of each repository. However, if you want to ensure that the code you are using from these projects exactly matches what was used to conduct these experiments, conduct the following steps. First, clone the project locally from github. Then, from within the project, run `git checkout <tag name>` where the `<tag name>` refers to a named version of the code listed in each of the following sections. Also, there is a suggested name for the conda environment for each tool in the following sections.

## [MMSegmentation](https://github.com/open-forest-observatory/mmsegmentation/tree/main)
This project is used for training and deploying state of the art semantic segementation models. Our fork has a small set of changes to the base repository. The tag is `v.xyz` and the conda environment should be called `mmseg`.

## [Segmentation utils](https://github.com/open-forest-observatory/segmentation_utils)
This project is used for managing practical challenges around preparing data to be used for semantic segmentation experiments. The tag is `v.xyz` and the conda environment should be called `segmentation-utils`.

## [Spatial utils](https://github.com/open-forest-observatory/spatial-utils)
This project is a collection of geospatial operations that are somewhat general, but still more complex that what is provided by existing foundational libraries such as `geopandas` and `geofileops`. The tag is `v.xyz` and the conda environment should be called `spatial-utils`.

## [Geograypher](https://github.com/open-forest-observatory/geograypher)
This project is used for converting per-image predictions into geospatial maps. The tag is `v.xyz` and the conda environment should be called `geograypher`.

## [Geospatial data registration toolkit](https://github.com/open-forest-observatory/geospatial-data-registration-toolkit)
This project is used for spatially registring data products from multiple drone missions. The tag is `v.xyz` and the conda environment should be called `GDRT`.

# Data
All the data required to reproduce these experiments are provided, broken up into `inputs`, `intermediate`, and `outputs`. The data can be downloaded from this [box folder](https::/TODO/link).

# Processing steps
The processing steps are in `code` and are broken up into four folders of scripts, corresponding to a type of operations: `1a_spatial_registration`,  `1b_semanatic_segmentation`, `2_geospatialize_imagery_predictions` and  `3_analysis`. The first two folders can be run in an arbitrary order since they do not depend on each other, but otherwise each folder must be run sequentially. Within each folder there are numbered scripts that must also be run sequentially.

## Spatial registration
The goal of registration is to spatially register photogrammetry products across multiple drone datasets. All of the scripts in this section should be run using the `GDRT` conda environment.
- `1_compute_pairwise_registrations.py`: Determines which datasets overlap. Then, it extracts the canopy height model (CHM) data for the overlapping region, as determined by the initial alignment. Then, the shift which minimizes the discrepency between the CHM heights is found, using an optimization based approach initially developed for registering medical images.
- `2_compute_global_shifts.py`: The previous step computes a set of pairwise shifts between individual datasets. However, to perform downstream analysis, these pairwise shifts must be converted into a single absolute shift for each dataset. This script uses least squares minimization to optimize a shift for each dataset that respects both the initial location of each dataset as well as the pairwise shifts between datasets.
- `3_shift_orthos.py`: This script produces a copy of each input orthomosaic using the global shift computed in the previous step. The outputs of this script are not required for any subsequent processing steps, only for visualization.

## Semantic segmentation
This section covers the steps to train a semantic segmentation model from annotated data and generate predictions on all the images that were collected.
- `1_create_data_folders.py`: Creates a train-test split for the annotated data and otherwise formats the data appropriately for model training. This script should be run with the `segmentation-utils` conda environment.
- `2_train_model.py`: Trains the model and is compuationally intensive. You will need a GPU-enabled machine with at least 13GB of video RAM (VRAM). Training will take approximately two hours, depending on the performance of your computer. This script should be run with the `mmseg` conda environment.
- `3_run_inference.py`: This runs inference on every image in the dataset. It still requires a GPU-enabled machine but does not require nearly as much VRAM. However, the runtime is multiple hours. This script should be run with the `mmseg` conda environment.

## Geospatialize imagery predictions
This section covers taking the per-image predictions generated by semantic segmentation and processing them into corresponding geospatial predictions.
- `1_project_labels.py`: Projects the image-based predictions to the mesh representation derived from photogrammetry. The fraction of predictions across all images for each class is recorded for every face on the mesh and saved out. This script should be run using the `geograypher` conda environment.
- `2_convert_faces_to_geospatial.py`: This tTakes the per-face information and converts it into geospatial information. Only faces which had a high degree of classification agreement across views are included. This threshold is determined by the `CONFIDENCE_THRESHOLD` constant which is imported from `constants.py`. This script should be run using the `geograypher` conda environment.
- `3_post_process_geospatial_maps.py`: Performs a combination of geometry simplifications, dilates, and errodes to simplify the geometry of the geospatial predictions. It also shifts each predicted map based on the results of geospatial registration. This script should be run using the `spatial-utils` conda environment.

## Analysis
The goal of this section is to conduct the final interpretation of the results. Both steps should be run using the `spatial-utils` conda environment.
- `1_merge_within_site_year.py`: There are multiple datasets for each site and year and this script merges the predictions across all of them. For each location, the final class is assigned based on what was predicted most commonly across all datasets. If there is a tie, it is broken in favor of the least common class. These merged predictions are computed only for the regions which are present in all years that have any data.
- `2_show_transition.py`: Computes the fraction of each class for each site and year. Then, within a given site, the fraction of each class in the first year that transitions to each other class is computed.
