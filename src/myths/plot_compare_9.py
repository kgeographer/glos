import pandas as pd
from sklearn.decomposition import PCA
from umap import UMAP
import matplotlib.pyplot as plt

# Load your conceptual profiles
df = pd.read_csv("out/myths/Conceptual_Profile_Vectors.csv")
labels = df["sourceFile"].tolist()
profile_matrix = df.drop(columns=["sourceFile"])

# Run PCA and UMAP
pca_coords = PCA(n_components=2).fit_transform(profile_matrix)
umap_coords = UMAP(n_components=2, random_state=42).fit_transform(profile_matrix)

# Plot side-by-side
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# PCA
axes[0].set_title("PCA Projection")
for i, label in enumerate(labels):
    x, y = pca_coords[i]
    axes[0].scatter(x, y)
    axes[0].text(x + 0.01, y, label.split("_")[0].upper(), fontsize=9)
axes[0].set_xlabel("PC1")
axes[0].set_ylabel("PC2")
axes[0].grid(True)

# UMAP
axes[1].set_title("UMAP Projection")
for i, label in enumerate(labels):
    x, y = umap_coords[i]
    axes[1].scatter(x, y)
    axes[1].text(x + 0.01, y, label.split("_")[0].upper(), fontsize=9)
axes[1].set_xlabel("UMAP1")
axes[1].set_ylabel("UMAP2")
axes[1].grid(True)

plt.tight_layout()
plt.show()