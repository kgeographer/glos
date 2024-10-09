import json
import re
import os

# File paths
input_file = 'data/tmi/tmi.json'
output_file = 'out/tmi/ref_loc.tsv'

# Refined Regex to match patterns like "<location>: <rest of reference>", capturing location and optional parenthetical part
location_pattern = r'([A-Za-z\.\s\-\'\(\)]+)(?:\s*\(([^)]+)\))?:'


# Function to extract locations and references based on the refined regex pattern
def extract_locations_and_references(tmi_data):
  results = []
  for entry in tmi_data:
    motif = entry.get('motif', '')
    locations = sorted(entry.get('locations', []))  # Alphabetically sort locations
    description = entry.get('description', '')

    # Process the "references" field only if it exists
    references_field = entry.get('references', '')
    if references_field:
      references = []

      # Find all matches in the references section
      for match in re.finditer(location_pattern, references_field):
        location = match.group(1).strip()
        # If there's a parenthetical part, include that as well
        if match.group(2):
          location += f" ({match.group(2).strip()})"
        references.append(location)

      references = sorted(references)  # Alphabetically sort references

      # Append to results if there are references
      if references:
        results.append([motif, ', '.join(locations), ', '.join(references), description])

  return results


# Function to write the output to TSV
def write_to_tsv(data, output_file):
  with open(output_file, 'w') as f:
    f.write("MOTIF_ID\tLOCATIONS\tREFERENCES\tDESCRIPTION\n")  # Headers
    for row in data:
      f.write("\t".join(row) + "\n")


# Read the JSON input file
with open(input_file, 'r') as infile:
  tmi_data = json.load(infile)

# Extract the locations and references
extracted_data = extract_locations_and_references(tmi_data)

# Write the results to a TSV file
write_to_tsv(extracted_data, output_file)

print(f"Extraction complete. Data written to {output_file}.")
