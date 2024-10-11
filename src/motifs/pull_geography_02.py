import json
import re

# Load the JSON data
with open('data/tmi/tmi.json', 'r') as f:
  data = json.load(f)

output_file = 'out/tmi/ref_loc.tsv'
distinct_references_file = 'out/tmi/distinct_references.txt'

# Regular expression to capture references (terms followed by a colon or in parentheses)
reference_pattern = re.compile(r'(\b[A-Za-z\s\'\.-]+)(?:\s*\(([^)]+)\))?:')

distinct_references_set = set()  # Set to hold all distinct references

with open(output_file, 'w') as out_f:
  out_f.write("MOTIF ID\tLOCATIONS\tREFERENCES\tDESCRIPTION\n")

  for entry in data:
    motif_id = entry.get('motif', '')
    locations = entry.get('locations', [])
    description = entry.get('additional_description', '')
    references = entry.get('references', '')

    if references:  # Only process if references exist
      # Extract references using the pattern
      extracted_references = reference_pattern.findall(references)

      # Clean and normalize extracted references
      cleaned_references = []
      for ref_tuple in extracted_references:
        main_term = ref_tuple[0].strip()
        if ref_tuple[1]:  # If there's a value in parentheses
          main_term += f" ({ref_tuple[1].strip()})"
        cleaned_references.append(main_term)
        distinct_references_set.add(main_term)  # Add to the distinct references set

      # Sort locations and references
      locations = sorted(locations)
      cleaned_references = sorted(cleaned_references)

      # Write the row to the output file
      out_f.write(f"{motif_id}\t{', '.join(locations)}\t{', '.join(cleaned_references)}\t{description}\n")

# Write the distinct references to a separate file
with open(distinct_references_file, 'w') as distinct_f:
  for ref in sorted(distinct_references_set):
    distinct_f.write(f"{ref}\n")

print("Output written to:", output_file)
print("Distinct references written to:", distinct_references_file)
