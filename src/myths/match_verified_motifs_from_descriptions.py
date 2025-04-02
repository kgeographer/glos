
import os
import json
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI
from time import sleep

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_PARAMS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

def fetch_all_a_motifs():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT motif_id, text FROM folklore.motif_text WHERE motif_id LIKE 'A%' ORDER BY motif_id")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def chunk_motifs(motifs, size=500):
    return [motifs[i:i+size] for i in range(0, len(motifs), size)]

def build_prompt(description, motif_chunk):
    motif_lines = "\n".join([f"{m_id} - {label}" for m_id, label in motif_chunk])
    return f"""
You are a folklore scholar. Given the following thematic description from a creation myth, choose up to 3 motifs from the list that best match the description.

Theme description:
"{description}"

Motif candidates:
{motif_lines}

Return each match on its own line in the format:
MOTIF_ID - explanation (1 sentence)
Only return motifs that are clearly and directly relevant.
"""

def gpt4_match_motifs(theme_description, motif_chunks):
    selected = {}
    for i, chunk in enumerate(motif_chunks):
        print(f"→ Processing chunk {i+1}/{len(motif_chunks)}")
        prompt = build_prompt(theme_description, chunk)
        try:
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            text = response.choices[0].message.content
            for line in text.split("\n"):
                if "-" in line:
                    parts = line.split("-", 1)
                    motif_id = parts[0].strip()
                    justification = parts[1].strip()
                    if motif_id not in selected:
                        selected[motif_id] = justification
        except Exception as e:
            print(f"⚠️ Error in chunk {i+1}: {e}")
            sleep(5)
    return selected

def main():
    input_path = "out/myths/pm002_supreme_being.json"
    with open(input_path, "r") as f:
        data = json.load(f)
        themes = data["themes"]["themes"] if "themes" in data["themes"] else data["themes"]

    all_motifs = fetch_all_a_motifs()
    motif_chunks = chunk_motifs(all_motifs)

    results = []

    for theme in themes:
        print(f"🔍 Matching motifs for theme: {theme['label']}")
        description = theme["description"]
        matches = gpt4_match_motifs(description, motif_chunks)
        results.append({
            "theme_label": theme["label"],
            "description": description,
            "matched_motifs": [{"motif_id": mid, "justification": just} for mid, just in matches.items()]
        })

    os.makedirs("out/myths/verified", exist_ok=True)
    output_path = "out/myths/verified/pm002_supreme_being_motif_matches.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Saved motif matches to {output_path}")

if __name__ == "__main__":
    main()
