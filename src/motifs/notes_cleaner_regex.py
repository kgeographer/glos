import re

# Path to the file to process
input_file_path = 'out/motifs/notes_processed/processed_notes_l.txt'
output_file_path = 'out/motifs/id_sentences_l_clean.tsv'

# Regex pattern for citations and references we want to ignore
reference_pattern = r'[A-Z][a-z]+:\s[A-Z][a-z]+|[A-Z][a-z]+:.*?[\.;]|\**Types.*?;|\**BP.*?;|\**Cox.*?;'


# Function to clean up any trailing references and citations
def clean_sentence(sentence):
  # Remove trailing references
  sentence = re.sub(reference_pattern, '', sentence).strip()
  # Strip unnecessary numbers, periods, or extra spaces
  sentence = re.sub(r'\d+\.*$', '', sentence).strip()
  return sentence


# Open the file and process it
with open(input_file_path, 'r') as infile, open(output_file_path, 'w') as outfile:
  for line in infile:
    if '\t' in line:  # Ensure there's a tab to separate motif ID and text
      motif_id, block = line.split('\t', 1)  # Split on the first tab only

      # Replace any newlines in the block with spaces for easier processing
      block = block.replace('\n', ' ').strip()

      # Split the block into sentences
      sentences = re.split(r'\. ', block)

      # Clean and filter out sentences with citations or references
      useful_sentences = [clean_sentence(s) for s in sentences if not re.search(reference_pattern, s)]

      # Join first one or two useful sentences
      useful_text = '. '.join(useful_sentences[:2]).strip() + '.'

      # Write the motif ID and the useful text to the output file
      outfile.write(f"{motif_id}\t{useful_text}\n")

print("File processing complete!")