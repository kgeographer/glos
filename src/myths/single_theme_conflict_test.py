
import os
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken
import json
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

def build_prompt(theme, motif_chunk):
    motif_lines = "\n".join([f"{m_id} - {label}" for m_id, label in motif_chunk])
    return f"""
You are a folklore scholar with access to the Thompson Motific Index (mythological section A). Your task is to identify motifs from a provided list that best match a given theme.

Theme: "{theme}"

From the list of motifs below, select up to 5 that most closely correspond to this theme. Only choose motifs that clearly relate to the concept. Return their motif IDs and a one-line justification for each.

Motif candidates:
{motif_lines}
"""

def count_tokens(text, model="gpt-4-1106-preview"):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def gpt4_select_motifs(theme, motif_chunks):
    selected = {}
    for i, chunk in enumerate(motif_chunks):
        print(f"→ Processing chunk {i+1}/{len(motif_chunks)}")
        prompt = build_prompt(theme, chunk)
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
                    label = parts[1].strip()
                    if motif_id not in selected:
                        selected[motif_id] = label
        except Exception as e:
            print(f"⚠️ Error in chunk {i+1}: {e}")
            sleep(5)
    return selected

def main():
    theme = "Conflict between Chiefs"
    all_motifs = fetch_all_a_motifs()
    motif_chunks = chunk_motifs(all_motifs)

    print(f"📚 Theme: {theme}")
    print(f"🧩 Chunks to process: {len(motif_chunks)}")

    results = gpt4_select_motifs(theme, motif_chunks)

    output = {
        "theme": theme,
        "verified_motifs": [{"motif_id": mid, "label": label} for mid, label in results.items()]
    }

    output_path = "out/myths/verified/single_theme_conflict_between_chiefs.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Saved results to {output_path}")

if __name__ == "__main__":
    main()
