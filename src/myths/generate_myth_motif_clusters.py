
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
# load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MYTH_INPUT_DIR = "data/myths"
MYTH_OUTPUT_DIR = "out/myths"
MODEL = "gpt-3.5-turbo"

os.makedirs(MYTH_OUTPUT_DIR, exist_ok=True)

def parse_myth_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        society = lines[0].strip()
        title = lines[1].strip()
        text = "".join(lines[2:]).strip()
    return society, title, text

def generate_prompt(society, title, text):
    return f"""
You are a folklore researcher. Given the following creation myth, identify five core conceptual themes or motifs that the story expresses. Then, for each theme, provide 3 to 5 motif IDs from Section A of the Thompson Motif Index (mythological motifs) that best match or represent the theme.

Myth Society: {society}
Myth Title: {title}

{text}

Respond in JSON format like this:
[
  {{
    "theme": "Theme label 1",
    "motifs": ["A123", "A456.1", "A789"]
  }},
  ...
]
"""

def process_myth_file(filename):
    input_path = os.path.join(MYTH_INPUT_DIR, filename)
    output_path = os.path.join(MYTH_OUTPUT_DIR, filename.replace(".txt", ".json"))

    society, title, text = parse_myth_file(input_path)
    prompt = generate_prompt(society, title, text)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        result = {
            "society": society,
            "title": title,
            "filename": filename,
            "themes": json.loads(content)
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"✓ Processed {filename}")
    except Exception as e:
        print(f"⚠️ Error processing {filename}: {e}")

def main():
    for file in os.listdir(MYTH_INPUT_DIR):
        if file.endswith(".txt"):
            process_myth_file(file)

if __name__ == "__main__":
    main()
