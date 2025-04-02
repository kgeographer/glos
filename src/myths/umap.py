import pandas as pd

# Load the conceptual profile vectors CSV
df = pd.read_csv("out/myths/Conceptual_Profile_Vectors.csv")

# Extract the numeric profile matrix (excluding sourceFile column)
profile_matrix = df.drop(columns=["sourceFile"])

from umap import UMAP

reduced = UMAP(n_components=2, random_state=42).fit_transform(profile_matrix)

import matplotlib.pyplot as plt

# Optional: load the original myth labels for context
labels = df["sourceFile"].tolist()

# Plot UMAP results
plt.figure(figsize=(8, 6))
for i, label in enumerate(labels):
    x, y = reduced[i]
    plt.scatter(x, y)
    plt.text(x + 0.01, y, label.split("_")[0].upper(), fontsize=9)

plt.title("2D UMAP Projection of Conceptual Profiles")
plt.xlabel("UMAP1")
plt.ylabel("UMAP2")
plt.grid(True)
plt.tight_layout()
plt.show()