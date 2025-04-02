
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_DIR = "data/myths"
OUTPUT_DIR = "out/myths"
MODEL = "gpt-3.5-turbo"

def get_theme_clusters(text, filename):
    prompt = f"""
You are a folklore scholar analyzing a creation myth. Your task is to identify five conceptual themes in the myth and for each one, provide:
1. A short label (e.g., "Conflict between Chiefs")
2. A short paragraph (2–3 sentences) describing what the theme means in the context of the myth.
3. A set of 3–5 Thompson motif IDs (from section A) that most closely correspond to the theme. You may invent motif IDs for now, but they should be plausible.

Myth:
{text}

Return your response in JSON format with a list of five entries. Each entry should have keys: "label", "description", and "motifs".
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content

def main():
    input_file = "pm002_supreme_being.txt"
    input_path = os.path.join(INPUT_DIR, input_file)

    with open(input_path, "r") as f:
        lines = f.readlines()
        society = lines[0].strip()
        title = lines[1].strip()
        text = "".join(lines[2:]).strip()

    print(f"Analyzing: {title} ({input_file})")
    raw_response = get_theme_clusters(text, input_file)
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError:
        print("⚠️ Failed to parse response as JSON. Output was:")
        print(raw_response)
        return

    output = {
        "society": society,
        "title": title,
        "filename": input_file,
        "themes": parsed
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = input_file.replace(".txt", ".json")
    output_path = os.path.join(OUTPUT_DIR, output_file)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Saved updated cluster file to {output_path}")

if __name__ == "__main__":
    main()
