import csv

# Input and output file paths
input_file = 'out/atu/types_data.tsv'
output_combinations_file = 'results/atu/type_combinations.tsv'
output_ref_file = 'results/atu/type_ref.tsv'

# Open the input file for reading
with open(input_file, 'r') as infile:
  reader = csv.DictReader(infile, delimiter='\t')

  # Open output files for writing
  with open(output_combinations_file, 'w', newline='') as comb_outfile, \
    open(output_ref_file, 'w', newline='') as ref_outfile:

    # Define fieldnames for output files
    comb_writer = csv.writer(comb_outfile, delimiter='\t')
    ref_writer = csv.writer(ref_outfile, delimiter='\t')

    # Write headers for the output files
    comb_writer.writerow(['type_id', 'combinations'])
    ref_writer.writerow(['type_id', 'ref_term'])

    # Process each row in the input file
    for row in reader:
      type_id = row['type_id']
      combinations = row['combinations'].strip()
      languages = row['languages'].strip()

      # Write to combinations file if combinations are present
      if combinations:
        comb_writer.writerow([type_id, combinations])

      # Split and write languages to ref file if present
      if languages:
        for language in languages.split(','):
          ref_writer.writerow([type_id, language.strip()])

print("Files generated successfully.")