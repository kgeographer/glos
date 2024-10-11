import csv

# File paths
ref_loc_file = 'out/tmi/ref_loc.tsv'
cultural_terms_file = 'out/tmi/cultural_terms.txt'
output_file = 'out/tmi/motif_culture.tsv'

# Load cultural terms
with open(cultural_terms_file, 'r', encoding='utf-8') as f:
  cultural_terms = [line.strip() for line in f.readlines() if line.strip()]

# Open the ref_loc file and process
with open(ref_loc_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', newline='',
                                                               encoding='utf-8') as outfile:
  reader = csv.DictReader(infile, delimiter='\t')
  writer = csv.writer(outfile, delimiter='\t')

  # Write header for the output file
  writer.writerow(['motif_id', 'culture_term'])

  # Loop through each row in ref_loc.tsv
  for row in reader:
    motif_id = row['MOTIF ID']
    references = row['REFERENCES']

    # Check if any cultural term appears in the REFERENCES column
    for term in cultural_terms:
      if term in references:
        # Write a new row for each matching cultural term
        writer.writerow([motif_id, term])

print(f"Data successfully written to {output_file}")
