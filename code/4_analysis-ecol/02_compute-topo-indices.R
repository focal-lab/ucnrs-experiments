# Purpose: Based on the DEM, compute topographic indices slope, topographic positio, solar
# radiation, and heat load (the latter two using hillshade as an approximation).

library(terra)
library(spatialEco)
library(solrad)

source("code/4_analysis-ecol/00_constants.R")

dem = rast(file.path(DEMS_PATH, "dem_merged.tif"))

## TPI at 500 m scale. This is slow at DEM resolutions finer than 30 m. Could drastically speed up by splitting to BORR and Hast and doing each separately, then merging.
tpi_merged = tpi(dem, win = "circle", scale = 500)
writeRaster(tpi_merged, file.path(ENV_PREDS_PATH, "tpi500.tif"), overwrite = TRUE)

## Hillshade to combine slope and aspect 
slope_rad = terrain(dem, v = "slope", unit = "radians")
aspect_rad = terrain(dem, v = "aspect", unit = "radians")

direction = 180
angle_wi = 29
angle_sp = 53
angle_su = 76
angle_fa = 53

shade_wi = shade(slope_rad, aspect_rad, direction = direction, angle = angle_wi)
shade_wi[shade_wi < 0] = 0

shade_sp = shade(slope_rad, aspect_rad, direction = direction, angle = angle_sp)
shade_sp[shade_sp < 0] = 0

shade_su = shade(slope_rad, aspect_rad, direction = direction, angle = angle_su)
shade_su[shade_su < 0] = 0

shade_fa = shade(slope_rad, aspect_rad, direction = direction, angle = angle_fa)
shade_fa[shade_fa < 0] = 0

shade_tot_norot = shade_wi + shade_sp + shade_su + shade_fa


# Repeat for a rotation of 45 degrees so SW is the hottest
direction = 225

shade_wi = shade(slope_rad, aspect_rad, direction = direction, angle = angle_wi)
shade_wi[shade_wi < 0] = 0

shade_sp = shade(slope_rad, aspect_rad, direction = direction, angle = angle_sp)
shade_sp[shade_sp < 0] = 0

shade_su = shade(slope_rad, aspect_rad, direction = direction, angle = angle_su)
shade_su[shade_su < 0] = 0

shade_fa = shade(slope_rad, aspect_rad, direction = direction, angle = angle_fa)
shade_fa[shade_fa < 0] = 0

shade_tot_rot = shade_wi + shade_sp + shade_su + shade_fa


# Write
writeRaster(shade_tot_norot, file.path(ENV_PREDS_PATH, "srad.tif"), overwrite = TRUE)
writeRaster(shade_tot_rot, file.path(ENV_PREDS_PATH, "hli.tif"), overwrite = TRUE)


## Also write the slope to use on its own
slope = terrain(dem, v = "slope", unit = "degrees")
writeRaster(slope, file.path(ENV_PREDS_PATH, "slope.tif"), overwrite = TRUE)
