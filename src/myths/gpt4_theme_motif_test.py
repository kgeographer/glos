
import os
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_PARAMS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

def fetch_first_n_motifs(n=500):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute(f"SELECT motif_id, text FROM folklore.motif_text WHERE motif_id LIKE 'A%' ORDER BY motif_id LIMIT {n}")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def build_prompt(theme, motifs):
    motif_block = "\n".join([f"{mid} - {text}" for mid, text in motifs])
    return f"""
You are a folklore scholar with access to the Thompson Motif Index (mythological section A). Your task is to identify motifs from a provided list that best match a given theme.

Theme: "{theme}"

From the list of motifs below, select up to 5 that most closely correspond to this theme. Only choose motifs that clearly relate to the concept. Return their IDs and a brief justification.

Motif candidates:
{motif_block}
"""

def count_tokens(text, model="gpt-4-1106-preview"):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def main():
    theme = "Conflict between Chiefs"
    motifs = fetch_first_n_motifs(500)
    prompt = build_prompt(theme, motifs)
    input_tokens = count_tokens(prompt)

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    output = response.choices[0].message.content
    output_tokens = count_tokens(output)
    total_tokens = input_tokens + output_tokens
    cost = (input_tokens * 0.01 + output_tokens * 0.03) / 1000  # $ per 1K tokens

    print("\n=== GPT-4 RESPONSE ===\n")
    print(output)
    print("\n=== TOKEN USAGE ===")
    print(f"Input tokens: {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Total tokens: {total_tokens}")
    print(f"Estimated cost: ${cost:.4f}")

if __name__ == "__main__":
    main()
