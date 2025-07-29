# Purpose: Extract veg preds and topo indices for each 30 m pixel (using the DEM grid)

library(terra)
library(sf)
library(tidyverse)

source("code/4_analysis-ecol/00_constants.R")

COVER_TYPES = c("BE_bare_earth", "HL_herbaceous_live", "HD_herbaceous_dead", "MM_man_made_object", "SD_shrub_dead", "SL_shrub_live", "TD_tree_dead", "TL_tree_live", "W_water")


dem = rast(file.path(DEMS_PATH, "dem_merged.tif"))

hast20 = st_read(file.path(VEG_PREDS_PATH, "Hastings_2020_merged_years.gpkg"))
borr20 = st_read(file.path(VEG_PREDS_PATH, "BORR_2020_separate_years.gpkg"))
hast23 = st_read(file.path(VEG_PREDS_PATH, "Hastings_2023_2024_merged_years.gpkg"))
borr23 = st_read(file.path(VEG_PREDS_PATH, "BORR_2023_separate_years.gpkg"))

#!!! RESUME
# Merge "BE_bare_earth", "HL_herbaceous_live", "HD_herbaceous_dead", "MM_man_made_object" to "HG_hergroung"



# We need to get the area of each veg type within each pixel so that we can then aggregate to select
# the most common veg type (assuming it is at least x% of the pixel)

veg_layer_foc = hast20
cover_type_foc = "TL_tree_live"
raster_template = dem
layer_suffix = "20"

get_veg_type_cover = function(cover_type_foc, veg_layer_foc, raster_template, layer_suffix) {

  # Clip the DEM to the bbox

  bbox = st_bbox(veg_layer_foc) |> st_as_sfc() |> st_buffer(1000) |> st_as_sf()
  template_foc = crop(raster_template, bbox)

  veg_foc = veg_layer_foc[veg_layer_foc$class_names == cover_type_foc, ]
  cover_foc = rasterize(veg_foc, template_foc, field = "class_ID", cover = TRUE, fun = "count")

  if (nrow(veg_foc) == 0) {
    values(cover_foc) = 10000
  }
  
  cover_foc[is.nan(cover_foc)] = NA

  names(cover_foc) = paste0(cover_type_foc, "_", layer_suffix)

  return(cover_foc)

}

covers_hast20 = lapply(COVER_TYPES, get_veg_type_cover, veg_layer_foc = hast20, raster_template = dem, layer_suffix = "20") |> rast()
covers_borr20 = lapply(COVER_TYPES, get_veg_type_cover, veg_layer_foc = borr20, raster_template = dem, layer_suffix = "20") |> rast()
covers_hast23 = lapply(COVER_TYPES, get_veg_type_cover, veg_layer_foc = hast23, raster_template = dem, layer_suffix = "23") |> rast()
covers_borr23 = lapply(COVER_TYPES, get_veg_type_cover, veg_layer_foc = borr23, raster_template = dem, layer_suffix = "23") |> rast()

# Within a year, merge the covers across reserves
covers_merged_20 = merge(covers_hast20, covers_borr20)
covers_merged_23 = merge(covers_hast23, covers_borr23)

#  Make a layer for whether there was any predicted cover at all in the pixel
contains_preds_20 = sum(covers_merged_20, na.rm = TRUE) > 0
contains_preds_23 = sum(covers_merged_23, na.rm = TRUE) > 0
# Select only cells that had preds in both years
contains_preds = contains_preds_20 & contains_preds_23
names(contains_preds) = "contains_preds"

# Across years, stack the covers
covers_merged = c(covers_merged_20, covers_merged_23, contains_preds)


## Layer in the topographic indices
tpi = rast(file.path(ENV_PREDS_PATH, "tpi500.tif"))
srad = rast(file.path(ENV_PREDS_PATH, "srad.tif"))
hli = rast(file.path(ENV_PREDS_PATH, "hli.tif"))
slope = rast(file.path(ENV_PREDS_PATH, "slope.tif"))

indices = c(tpi, srad, hli, slope)
names(indices) = c("tpi500", "srad", "hli", "slope")

covers_extended = extend(covers_merged, indices)
indices_extended = extend(indices, covers_merged)

stack = c(covers_extended, indices_extended)

# Check that it makes sense
writeRaster(stack, file.path(ENV_PREDS_PATH, "veg_preds_and_topo_indices.tif"), overwrite = TRUE)


d = as.data.frame(stack, xy = TRUE)
d = d[!is.na(d$contains_preds), ]

# Lump the classes: HL, HD, BG, MM = herbground



# Get the max cover type for each pixel
names_d = d |> select(ends_with("_20")) |> names()
d2 = d |>
  rowwise() |>
  mutate(max_cover_agg20 = names_d[which.max(c_across(ends_with("_20")))],
         max_cover_agg23 = names_d[which.max(c_across(ends_with("_23")))]) |>
  # Get the area of the max cover type in each pixel
  mutate(max_cover_area_agg20 = max(c_across(ends_with("_20")), na.rm = TRUE),
         max_cover_area_agg23 = max(c_across(ends_with("_23")), na.rm = TRUE))


# To keep a pixel for analysis, it needs to have > 60% of the prediction area in the max
# cover type and at least 25% of the pixel area in the max cover type