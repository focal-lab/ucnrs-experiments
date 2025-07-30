# Purpose: Map resprouting shrubs along with all veg preds

library(terra)
library(sf)
library(tidyverse)
library(tidyterra)

source("code/4_analysis-ecol/00_constants.R")

agg_pred_rast_20 = rast(file.path(COMPILED_FOR_ANALYSIS_PATH, "max_cover_type_agg20.tif"))
agg_pred_rast_23 = rast(file.path(COMPILED_FOR_ANALYSIS_PATH, "max_cover_type_agg23.tif"))

# Load fine-grained predicitons (currently only used for bbox)
hast20 = st_read(file.path(VEG_PREDS_PATH, "Hastings_2020_merged_years.gpkg"))
borr20 = st_read(file.path(VEG_PREDS_PATH, "BORR_2020_separate_years.gpkg"))


# Get the cells that were dead tree in 2020 but live tree in 2023
target = agg_pred_rast_20 == "HG_herbground" & agg_pred_rast_23 == "SL_shrub_live"

# Convert non-TRUE pixels to NA so they are not vectorized
target[!target] <- NA


### Plotting

# Crop to hast
pred_hast = crop(agg_pred_rast_23, st_bbox(hast20))
target_hast = crop(target, st_bbox(hast20))
# Conver to polygon
target_poly = as.polygons(target_hast, dissolve = TRUE)

ggplot() +
  geom_spatraster(d = pred_hast, aes(fill = veg_pred)) +
  scale_fill_manual(values = c("TD_tree_dead" = "#c9a628", "TL_tree_live" = "darkgreen", "HG_herbground" = "#ece47d",
                                "SL_shrub_live" = "#5ac45a", "SD_shrub_dead" = "#8e7b5f"),
                    na.value = "grey90", na.translate = FALSE) +
  geom_sf(data = target_poly, fill = NA, color = "red", linewidth = 0.8) +
  theme_minimal()

# Get the cells that were dead tree in 2020 but live tree in 2023

### Repeat for BORR

# Crop to borr
pred_borr = crop(agg_pred_rast_23, st_bbox(borr20))
target_borr = crop(target, st_bbox(borr20))
# Conver to polygon
target_poly = as.polygons(target_borr, dissolve = TRUE)

ggplot() +
  geom_spatraster(d = pred_borr, aes(fill = veg_pred)) +
  scale_fill_manual(values = c("TD_tree_dead" = "#c9a628", "TL_tree_live" = "darkgreen", "HG_herbground" = "#ece47d",
                                "SL_shrub_live" = "#5ac45a", "SD_shrub_dead" = "#8e7b5f"),
                    na.value = "grey90", na.translate = FALSE) +
  geom_sf(data = target_poly, fill = NA, color = "red", linewidth = 0.8) +
  theme_minimal()

# Get the cells that were dead tree in 2020 but live tree in 2023
