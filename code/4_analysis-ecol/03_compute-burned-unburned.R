# Purpose: Based on a fire history layer, at the same resolution as the topo indices, and also
# disaggregated by factor of 10 in both dimensions, compute whether burned or unburned in 2020.

library(terra)
library(sf)

source("code/4_analysis-ecol/00_constants.R")

# Cells within this distance (m) of a fire perimeter are set to NA, since their burn status is
# uncertain
PERIM_BUFFER_M = 50

dem = rast(file.path(DEMS_PATH, "dem_merged.tif"))
fires = st_read(file.path(FIRE_PERIMS_PATH, "fire-perims-2020.gpkg"))

fires$burned = TRUE

# Rasterize the fire perimeters to the DEM grid
fires = st_transform(fires, crs(dem))
fires_rast = rasterize(vect(fires), dem, field = "burned", background = FALSE)
names(fires_rast) = "burned_2020"

writeRaster(fires_rast, file.path(FIRE_PERIMS_PATH, "burned-2020.tif"), overwrite = TRUE)

# A buffer around the perimeter lines (both inside and outside the perimeters), to exclude cells
# whose burn status is uncertain
perim_buffer = st_union(fires) |>
  st_boundary() |>
  st_buffer(PERIM_BUFFER_M)

# Repeat with disaggregated DEM (3 m), this time coding as 1 (burned), 0 (unburned), and NA (within
# PERIM_BUFFER_M of a fire perimeter)
dem_disagg = rast(file.path(DEMS_PATH, "dem_merged_disagg.tif"))
fires_rast_disagg = rasterize(vect(fires), dem_disagg, field = 1, background = 0)
perim_buffer_rast_disagg = rasterize(vect(perim_buffer), dem_disagg, field = 1, background = 0)
fires_rast_disagg[perim_buffer_rast_disagg == 1] = NA
names(fires_rast_disagg) = "burned_2020"

writeRaster(fires_rast_disagg, file.path(FIRE_PERIMS_PATH, "burned-2020_disagg.tif"), overwrite = TRUE)
