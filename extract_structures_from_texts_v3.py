"""
Script: extract_structures_from_texts_v3.py
Purpose: Extract consistent structured representations (JSON-LD) from myth text files.
Features:
- Applies LLM extraction using GPT-4-turbo
- Chunks long myths exceeding token limits
- Merges chunks into a consistent single output
- Ensures uniform JSON-LD structure under "assertions" key

Input:  data/myths/*.txt
Output: out/myths/jsonld_consistent/*.jsonld
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration
input_dir = Path("data/myths/")
output_dir = Path("out/myths/jsonld_consistent/")
output_dir.mkdir(parents=True, exist_ok=True)
CHUNK_SIZE = 3000  # characters; adjust for safety under token limits
SLEEP_SECONDS = 2

SYSTEM_PROMPT = (
    "You are a knowledge extraction engine trained in world mythology. "
    "Given the full text of a myth, extract a structured JSON-LD representation with a single top-level key: 'assertions'. "
    "Include uniquely identified entities, events, and relations. Use the keys 'entity', 'event', or 'relation'. "
    "Entity objects should include '@id', 'type', and 'name' where applicable. "
    "Event objects should include '@id', 'type', and optional role fields like 'agent' and 'patient'. "
    "Relation objects should include 'type', 'subject', and 'object'."
)

def chunk_text(text, chunk_size):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def query_llm(text):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        response_format="json"
    )
    return response.choices[0].message.content

def merge_assertions(chunks):
    merged = {"@context": "http://example.org/myth/context", "assertions": []}
    for chunk in chunks:
        data = json.loads(chunk)
        if "assertions" in data:
            merged["assertions"].extend(data["assertions"])
    return merged

def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    if len(text) <= CHUNK_SIZE:
        print(f"Processing {file_path.name} as single chunk...")
        output = query_llm(text)
        return json.loads(output)
    else:
        print(f"Processing {file_path.name} in chunks...")
        chunks = chunk_text(text, CHUNK_SIZE)
        responses = []
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}/{len(chunks)}")
            responses.append(query_llm(chunk))
            time.sleep(SLEEP_SECONDS)
        return merge_assertions(responses)

def main():
    for file_path in input_dir.glob("*.txt"):
        myth_id = file_path.stem
        output_path = output_dir / f"{myth_id}.jsonld"
        if output_path.exists():
            print(f"Skipping {myth_id}, already processed.")
            continue
        try:
            result = process_file(file_path)
            with open(output_path, "w", encoding="utf-8") as out_file:
                json.dump(result, out_file, indent=2)
            print(f"Saved {output_path.name}")
        except Exception as e:
            print(f"Error processing {myth_id}: {e}")

if __name__ == "__main__":
    main()
