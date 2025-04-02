
import os
import json
import psycopg2
from dotenv import load_dotenv

# Load environment variables for DB connection
load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

MYTH_INPUT_DIR = "out/myths"
NORMALIZED_GROUPS_FILE = os.path.join(MYTH_INPUT_DIR, "normalized_cluster_groups.json")
OUTPUT_SIGNATURES_FILE = os.path.join(MYTH_INPUT_DIR, "myth_signatures_with_labels.json")

def fetch_motif_labels(motif_ids):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    query = f"""
        SELECT motif_id, text
        FROM folklore.motif_text
        WHERE motif_id = ANY(%s)
    """
    cur.execute(query, (list(motif_ids),))
    results = dict(cur.fetchall())
    cur.close()
    conn.close()
    return results

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
    residual_motifs = set()

    for cluster in myth_data["themes"]:
        for motif in cluster["motifs"]:
            all_motifs.add(motif)
            if motif in motif_to_cluster:
                cluster_id = motif_to_cluster[motif]
                cluster_hits[cluster_id] = cluster_descriptions.get(cluster_id, "")
            else:
                residual_motifs.add(motif)

    # Get motif labels for unmatched ones
    residual_labels = fetch_motif_labels(residual_motifs)
    residual_motif_descriptions = {mid: residual_labels.get(mid, "(label not found)") for mid in residual_motifs}

    return {
        "myth": myth_data["title"],
        "filename": myth_data["filename"],
        "cluster_signature": cluster_hits,
        "residual_motifs": residual_motif_descriptions
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

    print(f"✓ Saved labeled signatures (with residual motif text) to {OUTPUT_SIGNATURES_FILE}")

if __name__ == "__main__":
    main()
