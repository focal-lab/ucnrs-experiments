# %%
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from geograypher.meshes import TexturedPhotogrammetryMesh

# %%
DOWNLOADS_FOLDER = (
    "/ofo-share/repos-david/UCNRS-experiments/data/photogrammetry_products"
)
DATASET_ID = "000584"
IDS_TO_LABELS = {
    0: "BE_bare_earth",
    1: "HL_herbaceous_live",
    2: "MM_man_made_object",
    3: "SD_shrub_dead",
    4: "SL_shrub_live",
    5: "TD_tree_dead",
    6: "TL_tree_live",
    7: "W_water",
}

texture_path = f"/ofo-share/repos-david/UCNRS-experiments/data/geograypher_outputs/face_values/{DATASET_ID}.npy"
mesh_file = Path(DOWNLOADS_FOLDER, "mesh", f"mesh-internal-{DATASET_ID[3:]}.ply")

# %%
face_values = np.load(texture_path)
face_values.shape

# %%
max_value = np.max(face_values, axis=1)

plt.hist(max_value, density=True, cumulative=True, bins=200)
plt.show()

# %%
mesh = TexturedPhotogrammetryMesh(mesh_file, downsample_target=0.2)
mesh.vis()

# %%
mesh.set_texture(max_value)
mesh.vis()

# %%
from geograypher.utils.indexing import find_argmax_nonzero_value
max_class = find_argmax_nonzero_value(face_values, keepdims=False)
breakpoint()
plt.hist(max_class)
plt.show()
mesh.set_texture(max_class)
mesh.vis()


