# Purpose: Based on the footprints of the veg cover predictions (plus buffer), get a DEM for the
# area

library(sf)
library(terra)
library(elevatr)

source("code/4_analysis-ecol/00_constants.R")

# One layer (year) per site, using the year that contains the full extent
hast20 = st_read(file.path(VEG_PREDS_PATH, "Hastings_2020_separate_years.gpkg"))
borr20 = st_read(file.path(VEG_PREDS_PATH, "BORR_2020_merged_years.gpkg"))

# Get the bbox and buffer by 500 m, and transform to 4326 to avoid resmapling dems
hast20_bbox = st_bbox(hast20) |> st_as_sfc() |> st_buffer(1000) |> st_as_sf() |> st_transform(4326)
borr20_bbox = st_bbox(borr20) |> st_as_sfc() |> st_buffer(1000) |> st_as_sf() |> st_transform(4326)

# Download the DEMs. TODO: Consider getting a 10 m DEM.
hast20_dem = elevatr::get_elev_raster(hast20_bbox, src="gl1", clip = "bbox")
borr20_dem = elevatr::get_elev_raster(borr20_bbox, src="gl1", clip = "bbox")

# Convert to rast
hast20_dem = rast(hast20_dem)
borr20_dem = rast(borr20_dem)

# # Save the DEMs
# writeRaster(hast20_dem, file.path(DEMS_PATH, "dem_hast.tif"), overwrite = TRUE)
# writeRaster(borr20_dem, file.path(DEMS_PATH, "dem_borr.tif"), overwrite = TRUE)


# Make a merged DEM
merged_dem = terra::vrt(sprc(hast20_dem, borr20_dem), overwrite = TRUE)

# Reproject to UTM so we can do other operations in meters (also this is the CRS of the veg cover predictions)
merged_dem = project(merged_dem, "epsg:32610", method = "bilinear")

# Write
writeRaster(merged_dem, filename = file.path(DEMS_PATH, "dem_merged.tif"), overwrite = TRUE)
