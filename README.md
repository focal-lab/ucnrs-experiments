# UCNRS-experiments


## Different functionality
- `code/find_corresponding_image_for_subset.py` For finding which files in the labeled subset correspond to the full set of images.
- `code/labels/create_standardized_labels.py` For linking the labels into a standardized structure matching the OFO images
- `code/render_new_labeled_views.py` For rendering views from new perspectives of regions labeled from a single viewpoint.
- `code/post_process_geospatial_maps.py` Perform simplifying operations on the polygons and then shift them spatially so all datasets are registered.
- `code/cover_change.ipynb` Compute summaries of the year-to-year cover change for areas that have predictions across multiple years.


## Training data generation
We have manually annotated image-level data using an open-source web tool called [VIAME](https://www.viametoolkit.org/). This tool does not provide exports in a standaridized format, so we have written a converter, `convert_annotations_new_download.py`. This is run to encode each image's annotation in the Cityscapes format. The `.py` config file produced by this script can be used to train a model using MMSegmentation (this [script]())

## Model inference
The first step in model inference is to create a folder containing a sub-folder for the images for each mission. If working on `/ofo-share`, this can be done using `code/imagery_inference/symlink_subset_of_datasets.py`. Then, use this [script](https://github.com/open-forest-observatory/mmsegmentation/blob/main/tools/inference.py) to produce a folder of predictions in a parellel structure to the input images. To do so you must active the appropriate conda environment for mmsegmentation. Then the format of the command will be
```
python inference.py --config_path <config path output by training step> \
    --checkpoint_path <latest checkpoint output by training step> \
    --image_folder <folder of symlinked images from last step> \
    --output_folder <location to write the predictions>
```


## Projection post processing
This section begins by assuming you've generated predictions for each image.
 Due to some inconsistencies with how image orientation metadata is handled across different tools in our pipeline, we need to flip some of these predictions so they are consistent with the metadata-free interpretation of the image's orientation. This is done with the `flip_preds.py` script. This creates a new folder of predictions that is consistent with the orientation expected by `geograypher`.

Then these per-image predictions can be projected to geospatial coordinates using `project_labels.py`. This creates two main outputs, the per-face aggregated predictions and the geospatial representation of the most common class per face. The geospatial representation has information from all faces that at least one image projected to. But some of these predictions may not be very confident. The `geospatialize_high_conf_mesh_faces.py` script allows the per-face data saved out by the previous script to be converted into geospatial information, but only for faces where all corresponding predictions have a high degree of agreement.

Finally, the geospatial predictions need to be post-processed with `post_process_geospatial_maps.py`. This does two main steps. The first is to geometrically simplify the polygons by applying boundary simplification and morphological operations. The second is to take the simplified polygons and shift them. This is done based on the results of the `registration` scripts such that all of the datasets are spatially registered.