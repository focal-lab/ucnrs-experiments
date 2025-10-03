# Purpose: Conctruct a veg cover transition visualization

# NOTE: On linux I had to set the env var export OPENSSL_CONF="" to get webshot to work

library(tidyverse)
library(networkD3)
library(webshot)

source("code/4_analysis-ecol/00_constants.R")

# COVER_TYPES = c("HG_herbground", "SD_shrub_dead", "SL_shrub_live", "TD_tree_dead", "TL_tree_live", "W_water")
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

  # Change the veg pred names to be consistent with elsewhere in the paper
  d_sk = d_sk |>
    mutate(max_cover_type_agg20 = case_when(max_cover_type_agg20 == "TD_tree_dead_20" ~ "Tree Dead",
                                max_cover_type_agg20 == "TL_tree_live_20" ~ "Tree Live",
                                max_cover_type_agg20 == "HG_herbground_20" ~ "Herbaceous & Bare",
                                max_cover_type_agg20 == "SL_shrub_live_20" ~ "Shrub Live",
                                max_cover_type_agg20 == "SD_shrub_dead_20" ~ "Shrub Dead",
                                max_cover_type_agg20 == "W_water_20" ~ "Water"),
           max_cover_type_agg23 = case_when(max_cover_type_agg23 == "TD_tree_dead_23" ~ "Tree Dead ",
                                max_cover_type_agg23 == "TL_tree_live_23" ~ "Tree Live ",
                                max_cover_type_agg23 == "HG_herbground_23" ~ "Herbaceous & Bare ",
                                max_cover_type_agg23 == "SL_shrub_live_23" ~ "Shrub Live ",
                                max_cover_type_agg23 == "SD_shrub_dead_23" ~ "Shrub Dead ",
                                max_cover_type_agg23 == "W_water_23" ~ "Water "))

# Create nodes with a group column
nodes <- data.frame(
  name = c(as.character(d_sk$max_cover_type_agg20), 
           as.character(d_sk$max_cover_type_agg23)) %>% unique()
)

# Add a group column that strips the trailing space
nodes$group = gsub(" ", "", nodes$name)

# IMPORTANT: Make sure domain and range match up correctly

# c("Tree Dead" = "#c9a628", "Tree Live" = "darkgreen", "Herbaceous & Bare" = "#ece47d",
#                                   "Shrub Live" = "#5ac45a", "Shrub Dead" = "#8e7b5f"),

my_color <- 'd3.scaleOrdinal().domain(["Herbaceous&Bare", "ShrubDead", "ShrubLive", "TreeDead", "TreeLive", "Water"]).range(["#ece47d", "#8e7b5f", "#5ac45a", "#c9a628", "darkgreen", "lightblue"]);'



# With networkD3, connection must be provided using id, not using real name like in the links dataframe.. So we need to reformat it.
d_sk$IDsource <- match(d_sk$max_cover_type_agg20, nodes$name)-1 
d_sk$IDtarget <- match(d_sk$max_cover_type_agg23, nodes$name)-1

# Make the Network
p <- sankeyNetwork(
  Links = d_sk, Nodes = nodes,
  Source = "IDsource", Target = "IDtarget", Value = "pct", sinksRight = FALSE,
  NodeID = "name", fontSize = 20,
  NodeGroup = "group",
  colourScale = my_color)
p


saveNetwork(p, file.path(TEMP_PATH, "veg-cover-transition-sankey.html"))

webshot(file.path(TEMP_PATH, "veg-cover-transition-sankey.html"),
        file.path(FIGURES_PATH, "veg-cover-transition-sankey.png"), vwidth = 1000, vheight = 600)

