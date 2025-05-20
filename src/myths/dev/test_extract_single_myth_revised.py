"""
Script: test_extract_single_myth_revised.py
Purpose: Extract structured RDF-style JSON-LD from a single myth using a revised, stricter prompt.
"""

import os
import json
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables for OpenAI API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Constants
CHUNK_SIZE = 12000
SLEEP_SECONDS = 2
input_file = Path("data/myths/pm007_how_zambe_created.txt")
output_dir = Path("out/myths/jsonld_consistent")
output_json = output_dir / "pm007_how_zambe_created_revised.jsonld"
output_txt = output_dir / "pm007_how_zambe_created_revised_raw.txt"
output_dir.mkdir(parents=True, exist_ok=True)

# Revised prompt for improved consistency
SYSTEM_PROMPT = """
You are a structured data extraction engine trained in world mythology. Your task is to extract a clean, semantically consistent RDF-style JSON-LD structure from the full text of a myth.

Your output MUST follow these rules:
1. The top-level key should be "assertions", containing an array of RDF-style nodes.
2. Each assertion must have an "@id", an "@type", and appropriate properties.
3. All event types must end in "Event" (e.g., CreationEvent, DistributionEvent, EncounterEvent).
4. All roles must be selected from the standard set: "agent", "patient", "subject", "object". Do not invent new role names like "creator", "distributor", or "transformer".
5. Use IDs like "entity1", "event1", "relation1"—do not prefix IDs with class names or colons.
6. If you must refer to a result or consequence, use a relation such as "hasResultingState" with a clearly named entity or string value.
7. Use consistent, lowercase IDs scoped to the document.

Return only the JSON-LD data, no explanations or markdown formatting.

Begin by analyzing the myth and identify all distinct entities, events, and relationships. Then encode them using the above rules.
"""

def chunk_text(text, chunk_size):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def query_llm(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ]
        )
        content = response.choices[0].message.content.strip()
        return clean_response(content)
    except Exception as e:
        print(f"❌ Error querying LLM: {e}")
        return None

def clean_response(raw):
    match = re.match(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    return match.group(1).strip() if match else raw.strip()

def process_single_file():
    print(f"🔍 Reading {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    if len(text) <= CHUNK_SIZE:
        print(f"🟢 Processing as single chunk...")
        response = query_llm(text)
        if response:
            with open(output_txt, "w", encoding="utf-8") as temp:
                temp.write(response)
            try:
                data = json.loads(response)
                data["@context"] = "http://example.org/context/myth-v1.jsonld"
                with open(output_json, "w", encoding="utf-8") as out_file:
                    json.dump(data, out_file, indent=2)
                print(f"✅ JSON-LD saved to {output_json}")
            except Exception as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"📝 Raw output saved to {output_txt}")
    else:
        print("Myth is too long for this test script. Use a chunked processor.")

if __name__ == "__main__":
    process_single_file()
