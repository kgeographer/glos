
import os
import json
from collections import defaultdict
from itertools import combinations

MYTH_OUTPUT_DIR = "out/myths"
MIN_SHARED_MOTIFS = 2  # Minimum number of shared motifs to consider a match

def load_clusters():
    all_clusters = []
    for filename in os.listdir(MYTH_OUTPUT_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(MYTH_OUTPUT_DIR, filename), "r", encoding="utf-8") as f:
                data = json.load(f)
                for i, theme_cluster in enumerate(data["themes"]):
                    cluster_id = f"{filename.replace('.json', '')}_T{i+1}"
                    all_clusters.append({
                        "id": cluster_id,
                        "theme": theme_cluster["theme"],
                        "motifs": set(theme_cluster["motifs"]),
                        "myth": data["title"]
                    })
    return all_clusters

def group_clusters(clusters):
    grouped = []
    seen = set()
    group_id = 1

    for c1, c2 in combinations(clusters, 2):
        if len(c1["motifs"].intersection(c2["motifs"])) >= MIN_SHARED_MOTIFS:
            key = frozenset([c1["id"], c2["id"]])
            if key not in seen:
                seen.add(key)
                # Try to find an existing group
                added = False
                for group in grouped:
                    group_ids = {member["id"] for member in group["members"].values()}
                    if c1["id"] in group_ids or c2["id"] in group_ids:
                        group["members"].update({c1["id"]: c1, c2["id"]: c2})
                        added = True
                        break
                if not added:
                    grouped.append({
                        "candidate_group_id": f"CG{group_id:02}",
                        "members": {c1["id"]: c1, c2["id"]: c2}
                    })
                    group_id += 1

    # Convert member dicts to lists for clean output
    for group in grouped:
        group["members"] = list(group["members"].values())

    return grouped

def main():
    clusters = load_clusters()
    grouped = group_clusters(clusters)
    output_path = os.path.join(MYTH_OUTPUT_DIR, "candidate_cluster_groups.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(grouped, f, indent=2)
    print(f"✓ Saved {len(grouped)} candidate cluster groups to {output_path}")

if __name__ == "__main__":
    main()
