# Purpose: Explore the factors explaining the fate of dead trees

library(tidyverse)
library(networkD3)
library(randomForest)
library(ggeffects)
library(patchwork)

source("code/4_analysis-ecol/00_constants.R")

d = read_csv(file.path(COMPILED_FOR_ANALYSIS_PATH, "veg_preds_and_topo_indices.csv"))

# Filter to burned pixels, dead trees
d = d |>
  filter(max_cover_type_agg20 == "TD_tree_dead") |>
  filter(burned == 1) |>
  mutate(tree_fate = recode(max_cover_type_agg23,
                              "TD_tree_dead" = "dead",
                              "TL_tree_live" = "live",
                              "HG_herbground" = "dead",
                              "SL_shrub_live" = "live")) |>
  mutate(tree_fate_bool = ifelse(tree_fate == "live", TRUE, FALSE)) |>
  mutate(tree_fate = factor(tree_fate, levels = c("dead", "live"))) |>
  as.data.frame()

m = randomForest(tree_fate ~ tpi500 + srad + slope,
              data = d,
              importance = TRUE,
              ntree = 10000)
m
summary(m)
importance(m)

partialPlot(m, d, x.var = "tpi500", which.class = "live")


library(mgcv)

d = d |>
  mutate(tree_fate_bool = ifelse(tree_fate_bool, 1, 0))

m = gam(tree_fate_bool ~ s(tpi500) + s(srad),
        data = d,
        family = binomial(link = "logit"),
        REML = TRUE)
summary(m)

# Use emmeans for partial effects

p = ggemmeans(m,terms=c("srad"))
p_srad = plot(p) + 
  geom_rug(data = d, aes(x = srad), inherit.aes = FALSE) +
  coord_cartesian(ylim = c(0, 1)) +
  labs(title = NULL, x = "Solar radiation index", y = "Prob. of dead to live transitoin")
p_srad


p = ggemmeans(m,terms=c("tpi500"))
p_tpi = plot(p) + 
  geom_rug(data = d, aes(x = tpi500), inherit.aes = FALSE) +
  coord_cartesian(ylim = c(0, 1)) +
  labs(title = NULL, y = NULL, x =" Topographic position index") +
  # no y-axis labels
  theme(axis.text.y = element_blank(),
        axis.ticks.y = element_blank())
p_tpi

p_comb = p_srad + p_tpi

png(file.path(FIGURES_PATH, "dead-tree-fate-gam-partial-effects.png"), width = 1200, height = 600, res = 150)
p_comb
dev.off()
