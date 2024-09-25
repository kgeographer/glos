import re
import os

# Input and output paths
input_files = ['data/atu/Uther_vol1_clean01.txt', 'data/atu/Uther_vol2_clean01.txt']
output_file = 'out/atu/types_data.tsv'
geo_ethnic_file = 'data/atu/geo_ethnic.txt'

# Function to load the languages/ethnicities list from a file
def load_geo_ethnic_list(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
        return eval(content)  # Convert the string representation of the list into an actual Python list

# Load the list of geographical and ethnic terms (languages)
languages_list = load_geo_ethnic_list(geo_ethnic_file)

# Regex pattern to match combinations, stopping at the next section (e.g., "Remarks:", "Literature/Variants:", etc.)
combinations_pattern = r"Combinations:\s*(.*?)\n(?:\w+:\s|$)"  # Stop at section headers

# Regex pattern to match valid combination IDs (numbers with optional letters and asterisks)
combination_id_pattern = r'\b\d+[A-Z]*\**\b'

# Create a regex pattern for matching languages
languages_pattern = r'\b(?:' + '|'.join(re.escape(lang) for lang in languages_list) + r')\b'

# Updated pattern to capture type IDs (digits followed by optional letters or asterisks)
type_id_pattern = r'\|(\d+[A-Z]*\**)'  # Properly capturing asterisks in type ID

# Function to process a block of text for combinations and languages
def process_entry(entry):
    type_id_match = re.search(type_id_pattern, entry)  # Match type ID with letters/asterisks
    type_id = type_id_match.group(1) if type_id_match else None

    # Extract combinations
    combinations_match = re.search(combinations_pattern, entry, re.DOTALL)
    if combinations_match:
        combinations_text = combinations_match.group(1).strip()
        combinations = re.findall(combination_id_pattern, combinations_text)
    else:
        combinations = []

    # Extract languages and convert to set to ensure uniqueness
    languages_match = set(re.findall(languages_pattern, entry))

    return type_id, combinations, languages_match

# Process all files
with open(output_file, 'w') as out_file:
    out_file.write("type_id\tcombinations\tlanguages\n")  # Write headers

    for input_file in input_files:
        with open(input_file, 'r') as file:
            text = file.read()

        # Split text into individual entries using the pipe-prefixed type IDs
        entries = re.split(r'(?=\|\d+[A-Z]*\**)', text)

        for entry in entries:
            type_id, combinations, languages = process_entry(entry)

            if type_id:  # Only process valid entries
                combinations_str = ','.join(combinations)
                languages_str = ','.join(sorted(languages))  # Sort the set to ensure consistent output order
                out_file.write(f"{type_id}\t{combinations_str}\t{languages_str}\n")
                print(f"Processed type {type_id}: {len(combinations)} combinations, {len(languages)} unique languages")
