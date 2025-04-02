
import os
import json

MYTH_INPUT_DIR = "out/myths"
NORMALIZED_GROUPS_FILE = os.path.join(MYTH_INPUT_DIR, "normalized_cluster_groups.json")
OUTPUT_SIGNATURES_FILE = os.path.join(MYTH_INPUT_DIR, "myth_signatures_with_labels.json")

def load_normalized_groups():
    with open(NORMALIZED_GROUPS_FILE, "r", encoding="utf-8") as f:
        groups = json.load(f)

    motif_to_cluster = {}
    cluster_descriptions = {}
    for group in groups:
        cluster_id = group["cluster_id"]
        label = group.get("label", "")
        cluster_descriptions[cluster_id] = label
        for motif in group.get("motif_ids", []):
            motif_to_cluster[motif] = cluster_id
    return motif_to_cluster, cluster_descriptions

def process_myth_file(filepath, motif_to_cluster, cluster_descriptions):
    with open(filepath, "r", encoding="utf-8") as f:
        myth_data = json.load(f)

    all_motifs = set()
    cluster_hits = {}
    residual_motifs = {}

    for cluster in myth_data["themes"]:
        motifs = cluster["motifs"]
        all_motifs.update(motifs)
        for motif in motifs:
            if motif in motif_to_cluster:
                cluster_id = motif_to_cluster[motif]
                cluster_hits[cluster_id] = cluster_descriptions.get(cluster_id, "")
            else:
                residual_motifs[motif] = cluster["theme"]  # Use local theme label for unmatched motifs

    return {
        "myth": myth_data["title"],
        "filename": myth_data["filename"],
        "cluster_signature": cluster_hits,
        "residual_motifs": residual_motifs
    }

def main():
    motif_to_cluster, cluster_descriptions = load_normalized_groups()

    signatures = []
    for filename in os.listdir(MYTH_INPUT_DIR):
        if filename.endswith(".json") and filename not in [
            "normalized_cluster_groups.json",
            "candidate_cluster_groups.json",
            "myth_signatures.json",
            "myth_signatures_with_labels.json"
        ]:
            filepath = os.path.join(MYTH_INPUT_DIR, filename)
            signature = process_myth_file(filepath, motif_to_cluster, cluster_descriptions)
            signatures.append(signature)

    with open(OUTPUT_SIGNATURES_FILE, "w", encoding="utf-8") as f:
        json.dump(signatures, f, indent=2)

    print(f"✓ Saved labeled signatures to {OUTPUT_SIGNATURES_FILE}")

if __name__ == "__main__":
    main()
