# Purpose: Based on the footprints of the veg cover predictions (plus buffer), get a DEM for the
# area

library(terra)
library(spatialEco)

source("code/4_analysis-ecol/00_constants.R")

dem_hast20 = rast(file.path(DEMS_PATH, "dem_hast.tif"))
dem_merged = rast(file.path(DEMS_PATH, "dem_merged.tif"))

# Calc n cells for window knowing dem is ~30 m pixels and we want a 500 m window
window_size = round(500 / 30)
tpi_merged = tpi(dem_merged, scale = window_size)
writeRaster(tpi_merged, file.path(ENV_PREDS_PATH, "tpi_merged.tif"), overwrite = TRUE)

