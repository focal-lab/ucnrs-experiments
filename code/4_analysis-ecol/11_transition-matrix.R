# Purpose: Conctruct a veg cover transition visualization

# NOTE: On linux I had to set the env var export OPENSSL_CONF="" to get webshot to work:
# Sys.setenv(OPENSSL_CONF = "")
Sys.setenv(OPENSSL_CONF = "")

library(tidyverse)
library(networkD3)
library(webshot)

source("code/4_analysis-ecol/00_constants.R")

# COVER_TYPES = c("HG_herbground", "SD_shrub_dead", "SL_shrub_live", "TD_tree_dead", "TL_tree_live", "W_water")
# COVER_TYPES = c(COVER_TYPES, "BE_bare_earth", "HL_herbaceous_live", "HD_herbaceous_dead", "MM_man_made_object") # Add a layer for whether there are any veg preds in the pixel

d_all = read_csv(file.path(COMPILED_FOR_ANALYSIS_PATH, "veg_preds_and_topo_indices_highres.csv"))

# Filter to burned only
d = d_all |>
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



# Now as a transition matrix

# One panel for burned and one for unburned. The rows are the 2020 (pre-fire)
# cover type and the columns are the 2023 (post-fire) cover type. Cell shading is
# the proportion of that panel's 2020 class that became each 2023 class (i.e.,
# rows sum to 100% within a panel), which is the transition probability. The cell
# labels are the number of 3 m pixels making the transition.

COVER_LABELS = c("TL_tree_live" = "Tree Live",
                 "TD_tree_dead" = "Tree Dead",
                 "SL_shrub_live" = "Shrub Live",
                 "SD_shrub_dead" = "Shrub Dead",
                 "HG_herbground" = "Herbaceous & Bare",
                 "W_water" = "Water")

d_mat = d_all |>
  group_by(burned, max_cover_type_agg20, max_cover_type_agg23) |>
  summarise(n = n(), .groups = "drop") |>
  mutate(burned = factor(ifelse(burned == 1, "Burned", "Unburned"),
                         levels = c("Burned", "Unburned")),
         cover20 = factor(recode(max_cover_type_agg20, !!!COVER_LABELS),
                          levels = COVER_LABELS),
         cover23 = factor(recode(max_cover_type_agg23, !!!COVER_LABELS),
                          levels = COVER_LABELS)) |>
  # Fill in the combinations that never occurred so both panels share a full,
  # identical matrix
  complete(burned, cover20, cover23, fill = list(n = 0)) |>
  group_by(burned, cover20) |>
  # A cover type absent from a panel's 2020 map has no transition probabilities
  mutate(n_row = sum(n),
         pct_row = ifelse(n_row == 0, 0, n / n_row * 100)) |>
  ungroup()

p_mat = ggplot(d_mat, aes(x = cover23, y = fct_rev(cover20), fill = pct_row)) +
  facet_wrap(vars(burned), strip.position = "top") +
  geom_tile(color = "white", linewidth = 1) +
  geom_text(aes(label = format(n, big.mark = ",", trim = TRUE),
                color = pct_row > 50),
            size = 2.8) +
  scale_fill_gradient(low = "#f7f7f4", high = "#2b5c3f",
                      limits = c(0, 100),
                      name = "% of\nearly (2020)\nclass") +
  scale_color_manual(values = c("TRUE" = "white", "FALSE" = "gray20"), guide = "none") +
  scale_x_discrete(position = "top",
                   labels = function(x) str_wrap(x, width = 10),
                   expand = expansion(add = 0.5)) +
  scale_y_discrete(labels = function(x) str_wrap(x, width = 10),
                   expand = expansion(add = 0.5)) +
  labs(x = "Late cover type (2023)", y = "Early cover type (2020)") +
  coord_fixed() +
  theme_minimal(base_size = 12) +
  theme(panel.grid = element_blank(),
        panel.spacing = unit(20, "pt"),
        # Keep the panel titles above the column labels, not between them and the cells
        strip.placement = "outside",
        strip.text = element_text(size = 13, margin = margin(b = 8)),
        axis.title.x = element_text(margin = margin(b = 10)),
        axis.title.y = element_text(margin = margin(r = 10)),
        axis.text = element_text(color = "gray20"),
        # Bottom-align the (variably wrapped) column labels against the cells
        axis.text.x.top = element_text(vjust = 0, margin = margin(b = 5)),
        legend.title = element_text(size = 10),
        legend.key.height = unit(35, "pt"))
p_mat

png(file.path(FIGURES_PATH, "veg-cover-transition-matrix.png"), width = 2900, height = 1400, res = 200)
print(p_mat)
dev.off()
