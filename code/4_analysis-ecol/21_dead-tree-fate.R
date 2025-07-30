# Purpose: Explore the factors explaining the fate of dead trees

library(tidyverse)
library(networkD3)
library(randomForest)

source("code/4_analysis-ecol/00_constants.R")

d = read_csv(file.path(COMPILED_FOR_ANALYSIS_PATH, "veg_preds_and_topo_indices.csv"))

# Filter to dead trees
d = d |>
  filter(max_cover_type_agg20 == "TD_tree_dead") |>
  mutate(tree_fate = recode(max_cover_type_agg23,
                              "TD_tree_dead" = "dead",
                              "TL_tree_live" = "live",
                              "HG_herbground" = "dead",
                              "SL_shrub_live" = "live")) |>
  mutate(tree_fate_bool = ifelse(tree_fate == "live", TRUE, FALSE)) |>
  mutate(tree_fate = factor(tree_fate, levels = c("dead", "live"))) |>
  as.data.frame()

m = randomForest(tree_fate ~ tpi500 + hli + slope,
              data = d,
              importance = TRUE,
              ntree = 1000)
m
importance(m)

partialPlot(m, d, x.var = "tpi500", which.class = "live")


library(mgcv)

m = gam(tree_fate_bool ~ s(tpi500) + s(srad),
        data = d,
        family = binomial(link = "logit"))
summary(m)

# Use emmeans for partial effects
