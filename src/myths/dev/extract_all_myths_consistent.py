"""
Script: extract_all_myths_consistent.py
Purpose: Batch extraction of entities, events, and relations from all myth text files.
Processes files in data/myths/*.txt and outputs consistent JSON-LD to out/myths/jsonld_consistent/
Handles flat RDF-style assertions and merges chunked output.
"""

import os
import json
import time
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHUNK_SIZE = 12000
SLEEP_SECONDS = 2

SYSTEM_PROMPT = (
    "You are a knowledge extraction engine trained in world mythology. "
    "Given the full text of a myth, extract a structured JSON-LD representation with a single top-level key: 'assertions'. "
    "Each assertion must be an RDF-style node with '@id', '@type', and relevant properties. "
    "Use IDs like 'entity1', 'event2', 'relation3'. Do not wrap objects under keys like 'entity'. "
    "Use consistent ID formats and return only raw JSON (no Markdown)."
)

input_dir = Path("data/myths")
output_dir = Path("out/myths/jsonld_consistent")
output_dir.mkdir(parents=True, exist_ok=True)

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

def renumber_flat_assertions(assertions, offset):
    id_map = {}
    new_assertions = []
    updated_count = 0

    for assertion in assertions:
        if "@id" not in assertion or "@type" not in assertion:
            continue

        original_id = assertion["@id"]
        match = re.match(r"^(entity|event|relation)(\d+)$", original_id)
        if match:
            prefix, number = match.groups()
            new_id = f"{prefix.lower()}{int(number) + offset}"
            id_map[original_id] = new_id
            assertion["@id"] = new_id
            updated_count += 1

        for role in ["agent", "patient", "subject", "object"]:
            if role in assertion and assertion[role] in id_map:
                assertion[role] = id_map[assertion[role]]

        new_assertions.append(assertion)

    return new_assertions, updated_count

def merge_assertions(chunks):
    merged = {
        "@context": "http://example.org/context/myth-v1.jsonld",
        "assertions": []
    }
    offset = 0
    for i, chunk in enumerate(chunks):
        try:
            data = json.loads(chunk)
            assertions = data.get("assertions", [])
            fixed, count = renumber_flat_assertions(assertions, offset)
            offset += count
            merged["assertions"].extend(fixed)
        except Exception as e:
            print(f"⚠️ Error parsing chunk {i+1}: {e}")
    return merged

def process_file(file_path):
    print(f"🔍 Processing {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    output_json = output_dir / file_path.with_suffix(".jsonld").name
    output_txt = output_dir / (file_path.stem + "_raw.txt")
    # output_txt = output_dir / file_path.with_suffix("_raw.txt").name

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
        print(f"🟡 Processing in chunks...")
        chunks = chunk_text(text, CHUNK_SIZE)
        responses = []
        for i, chunk in enumerate(chunks):
            print(f"  🔄 Chunk {i+1}/{len(chunks)}")
            result = query_llm(chunk)
            if result:
                responses.append(result)
                with open(output_txt.with_name(output_txt.stem + f"_chunk{i+1}.txt"), "w", encoding="utf-8") as temp:
                    temp.write(result)
            else:
                print(f"⚠️ No response for chunk {i+1}")
            time.sleep(SLEEP_SECONDS)
        merged = merge_assertions(responses)
        with open(output_json, "w", encoding="utf-8") as out_file:
            json.dump(merged, out_file, indent=2)
        print(f"✅ Merged JSON-LD saved to {output_json}")

def process_all_files():
    all_txt_files = sorted(input_dir.glob("*.txt"))
    for file_path in all_txt_files:
        process_file(file_path)

if __name__ == "__main__":
    process_all_files()
