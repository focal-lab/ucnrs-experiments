# Purpose: Map resprouting shrubs along with all veg preds

library(terra)
library(sf)
library(tidyverse)
library(tidyterra)
library(patchwork)

source("code/4_analysis-ecol/00_constants.R")


# Plotting function for one reserve and one year, to use across all reserves and years
map_one_reserve_one_year = function(pred, target_poly, bbox, title, include_legend = FALSE) {

  # Change the veg pred names to be consistent with elsewhere in the paper
  pred = pred |>
    mutate(veg_pred = case_when(veg_pred == "TD_tree_dead" ~ "Tree Dead",
                                veg_pred == "TL_tree_live" ~ "Tree Live",
                                veg_pred == "HG_herbground" ~ "Herbaceous & Bare",
                                veg_pred == "SL_shrub_live" ~ "Shrub Live",
                                veg_pred == "SD_shrub_dead" ~ "Shrub Dead"))

  if(include_legend == TRUE) {guide_arg = "legend"} else {guide_arg = "none"} 

  ggplot() +
    scale_fill_manual(values = c("Tree Dead" = "#c9a628", "Tree Live" = "darkgreen", "Herbaceous & Bare" = "#ece47d",
                                  "Shrub Live" = "#5ac45a", "Shrub Dead" = "#8e7b5f"),
                      na.value = "grey90", na.translate = FALSE, guide = guide_arg, name = NULL) +
    # make the fill a very transparent orange
    geom_sf(data = fires, fill = "#ffe5a479", color = "orange", linewidth = 0.6) +
    theme_minimal() +
    geom_spatraster(d = pred, aes(fill = veg_pred)) +
    geom_sf(data = target_poly, fill = NA, color = "red", linewidth = 0.3) +
    # repeat the fire perim, but just the line, so it shows up on top of the veg raster
    geom_sf(data = fires, fill = "NA", color = "orange", linewidth = 0.6) +
    coord_sf(xlim = c(bbox["xmin"], bbox["xmax"]),
                ylim = c(bbox["ymin"], bbox["ymax"])) +
    labs(title = title) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))

}

# Load the 30 m predictions
agg_pred_rast_20 = rast(file.path(COMPILED_FOR_ANALYSIS_PATH, "max_cover_type_agg20.tif"))
agg_pred_rast_23 = rast(file.path(COMPILED_FOR_ANALYSIS_PATH, "max_cover_type_agg23.tif"))

# Load fine-grained predicitons (currently only used for defining the reserve-specific bbox)
hast20_fine = st_read(file.path(VEG_PREDS_PATH, "Hastings_2020_merged_years.gpkg"))
borr20_fine = st_read(file.path(VEG_PREDS_PATH, "BORR_2020_separate_years.gpkg"))
quail23_fine = st_read(file.path(VEG_PREDS_PATH, "Quail_2023_separate_years.gpkg"))

# Load the fire perims
fires = st_read(file.path(FIRE_PERIMS_PATH, "fire-perims-2020.gpkg")) |> st_transform(st_crs(agg_pred_rast_20))

# Defining a region to highlight with an outline on the maps

# # Get the cells that were herb/ground in 2020 but live shrub in 2023
# target = agg_pred_rast_20 == "HG_herbground" & agg_pred_rast_23 == "SL_shrub_live"

# ALTERNATIVE: get cells that were dead tree in 2020 but live tree in 2023
target = agg_pred_rast_20 %in% c("TD_tree_dead") &
         agg_pred_rast_23 %in% c("TL_tree_live", "SL_shrub_live")


# Convert non-TRUE pixels to NA so they are not vectorized
target[!target] <- NA


### Plotting

# Hast 20
bbox = st_bbox(hast20_fine) # Year doesn't matter, just using to define the extent of the map
pred = crop(agg_pred_rast_20, bbox)
target_poly = crop(target, bbox) |> as.polygons(dissolve = TRUE)

hast20 = map_one_reserve_one_year(pred = pred, target_poly = target_poly, bbox = bbox, title = "Hastings early")


# Hast 23
bbox = st_bbox(hast20_fine) # Year doesn't matter, just using to define the extent of the map
pred = crop(agg_pred_rast_23, bbox)
target_poly = crop(target, bbox) |> as.polygons(dissolve = TRUE)

hast23 = map_one_reserve_one_year(pred = pred, target_poly = target_poly, bbox = bbox, title = "Hastings late", include_legend = TRUE)


# Borr 20
bbox = st_bbox(borr20_fine) # Year doesn't matter, just using to define the extent of the map
pred = crop(agg_pred_rast_20, bbox)
target_poly = crop(target, bbox) |> as.polygons(dissolve = TRUE)

borr20 = map_one_reserve_one_year(pred = pred, target_poly = target_poly, bbox = bbox, title = "BORR early")


# Borr 23
bbox = st_bbox(borr20_fine) # Year doesn't matter, just using to define the extent of the map
pred = crop(agg_pred_rast_23, bbox)
target_poly = crop(target, bbox) |> as.polygons(dissolve = TRUE)

borr23 = map_one_reserve_one_year(pred = pred, target_poly = target_poly, bbox = bbox, title = "BORR late")


# # Quail 23
# bbox = st_bbox(quail23_fine) # Year doesn't matter, just using to define the extent of the map
# pred = crop(agg_pred_rast_23, bbox)
# target_poly = crop(target, bbox) |> as.polygons(dissolve = TRUE)

# Combine with patchwork

p = (hast20 + hast23) / (borr20 + borr23) + plot_layout(guides = "collect") & theme(legend.position = "bottom")
p

png(file.path(FIGURES_PATH, "veg-pred-maps-30m.png"), width = 1200, height = 1200, res = 150)
print(p)
dev.off()
