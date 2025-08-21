# Purpose: Based on a fire history layer, at the same resolution as the topo indices, compute
# whether burned or unburned in 2020.

library(terra)
library(sf)

source("code/4_analysis-ecol/00_constants.R")

dem = rast(file.path(DEMS_PATH, "dem_merged.tif"))
fires = st_read(file.path(FIRE_PERIMS_PATH, "fire-perims-2020.gpkg"))

fires$burned = TRUE

# Rasterize the fire perimeters to the DEM grid
fires = st_transform(fires, crs(dem))
fires_rast = rasterize(vect(fires), dem, field = "burned", background = FALSE)
names(fires_rast) = "burned_2020"

writeRaster(fires_rast, file.path(FIRE_PERIMS_PATH, "burned-2020.tif"), overwrite = TRUE)
