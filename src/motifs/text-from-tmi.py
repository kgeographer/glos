import json
import csv

# File paths
input_json_path = 'data/tmi/tmi.json'
output_tsv_path = 'out/tmi/motif_text.tsv'

# Load the JSON data
with open(input_json_path, 'r') as f:
  json_data = json.load(f)

# Open TSV file for writing
with open(output_tsv_path, 'w', newline='', encoding='utf-8') as tsv_file:
  writer = csv.writer(tsv_file, delimiter='\t')

  # Write header row
  writer.writerow(['rownum', 'motif_id', 'text'])

  # Initialize row number
  rownum = 1

  # Iterate through the JSON records and write to the TSV file
  for entry in json_data:
    motif_id = entry.get('motif', "")
    description = entry.get('description', "")
    additional_description = entry.get('additional_description', "")

    # Concatenate description and additional_description if additional_description exists
    text = description
    if additional_description.strip():
      # Ensure there is not an extra period if description already ends with one
      if description.endswith('.'):
        text = f"{description} {additional_description}"
      else:
        text = f"{description}. {additional_description}"

    # Write the row to the TSV file
    writer.writerow([rownum, motif_id, text])
    rownum += 1

print("File has been generated successfully.")
