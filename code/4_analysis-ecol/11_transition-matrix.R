# Purpose: Conctruct a veg cover transition visualization

library(tidyverse)
library(networkD3)

source("code/4_analysis-ecol/00_constants.R")

COVER_TYPES = c("HG_herbground", "SD_shrub_dead", "SL_shrub_live", "TD_tree_dead", "TL_tree_live", "W_water")
# COVER_TYPES = c(COVER_TYPES, "BE_bare_earth", "HL_herbaceous_live", "HD_herbaceous_dead", "MM_man_made_object") # Add a layer for whether there are any veg preds in the pixel

d = read_csv(file.path(COMPILED_FOR_ANALYSIS_PATH, "veg_preds_and_topo_indices.csv"))

# Filter to burned only
d = d |>
  filter(burned == 1)

d_agg = d |>
  group_by(max_cover_type_agg20, max_cover_type_agg23) |>
  summarise(n = n())
  
n_pixels = sum(d_agg$n)

d_sk = d_agg |>
  mutate(max_cover_type_agg20 = paste0(max_cover_type_agg20, "_20"),
         max_cover_type_agg23 = paste0(max_cover_type_agg23, "_23")) |>
  mutate(pct = n/n_pixels)

nodes <- data.frame(
  name=c(as.character(d_sk$max_cover_type_agg20), 
  as.character(d_sk$max_cover_type_agg23)) %>% unique()
)
 
# With networkD3, connection must be provided using id, not using real name like in the links dataframe.. So we need to reformat it.
d_sk$IDsource <- match(d_sk$max_cover_type_agg20, nodes$name)-1 
d_sk$IDtarget <- match(d_sk$max_cover_type_agg23, nodes$name)-1
 
# Make the Network
p <- sankeyNetwork(Links = d_sk, Nodes = nodes,
              Source = "IDsource", Target = "IDtarget", Value = "pct", sinksRight = FALSE,
             NodeID = "name")
p


