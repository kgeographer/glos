
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

GROUPS_FILE = "out/myths/candidate_cluster_groups.json"
OUTPUT_FILE = "out/myths/normalized_cluster_groups.json"
MODEL = "gpt-4"

def build_prompt(group):
    prompt = [
        {"role": "system", "content": "You are a folklore analyst helping to normalize thematic motif clusters in mythological stories."},
        {"role": "user", "content": f"""
Each of the following entries is a theme cluster from a myth, associated with motif IDs from the Thompson Motif Index (mythological section). These clusters were grouped together because they share overlapping motifs.

Please do the following:
1. Provide a short, consistent label that summarizes the shared theme.
2. Write a brief explanation (2–3 sentences) that describes why these motifs belong together conceptually, and how the variation in theme labels might reflect different narrative emphases.

Return your answer in JSON with keys:
- "cluster_id": matching the provided group ID
- "label": your chosen normalized theme label
- "description": your explanation

Here is the group:

Group ID: {group["candidate_group_id"]}

Clusters:
"""}
    ]
    for member in group["members"]:
        member_str = f"- Theme: {member['theme']}\n  Motifs: {', '.join(member['motifs'])}\n  Myth: {member['myth']}"
        prompt.append({"role": "user", "content": member_str})
    return prompt

def process_group(group):
    prompt = build_prompt(group)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=prompt,
            temperature=0.5
        )
        content = response.choices[0].message.content
        print(f"✓ Normalized {group['candidate_group_id']}")
        return json.loads(content)
    except Exception as e:
        print(f"⚠️ Error with {group['candidate_group_id']}: {e}")
        return None

def main():
    with open(GROUPS_FILE, "r", encoding="utf-8") as f:
        groups = json.load(f)

    results = []
    for group in groups:
        result = process_group(group)
        if result:
            results.append(result)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"✓ Saved normalized cluster labels to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
