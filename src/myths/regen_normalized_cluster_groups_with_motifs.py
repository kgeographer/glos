
import os
import json

MYTH_DIR = "out/myths"
CANDIDATE_FILE = os.path.join(MYTH_DIR, "candidate_cluster_groups.json")
NORMALIZED_FILE = os.path.join(MYTH_DIR, "normalized_cluster_groups.json")

def load_original_groups():
    with open(CANDIDATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def update_normalized_groups(original_groups, normalized_groups):
    updated = []
    for norm_group in normalized_groups:
        cluster_id = norm_group["cluster_id"]
        # Find matching candidate group by ID
        candidate_group = next(
            (group for group in original_groups if group["candidate_group_id"] == cluster_id),
            None
        )
        if not candidate_group:
            print(f"⚠️ Warning: No candidate group found for {cluster_id}")
            continue
        # Aggregate unique motif_ids from all members
        motif_ids = set()
        for member in candidate_group["members"]:
            motif_ids.update(member["motifs"])
        norm_group["motif_ids"] = sorted(motif_ids)
        updated.append(norm_group)
    return updated

def main():
    with open(NORMALIZED_FILE, "r", encoding="utf-8") as f:
        normalized_groups = json.load(f)
    original_groups = load_original_groups()

    updated = update_normalized_groups(original_groups, normalized_groups)

    with open(NORMALIZED_FILE, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2)
    print(f"✓ Regenerated normalized_cluster_groups.json with real motif_ids")

if __name__ == "__main__":
    main()
