import spacy

# Load the spaCy English model
nlp = spacy.load('en_core_web_sm')

# Path to the file to process
file_path = 'out/motifs/notes_processed/processed_notes_l.txt'


# Function to determine if a sentence is coherent
def is_coherent(sentence):
  # Check if the sentence has too many symbols or digits, which suggests it's a reference or citation
  symbol_count = sum(1 for char in sentence if not char.isalnum() and char not in [' ', '.'])
  digit_count = sum(1 for char in sentence if char.isdigit())
  word_count = len(sentence.split())

  # A simple heuristic: if the sentence is mostly symbols or digits, it's likely not a coherent sentence
  if symbol_count > word_count * 0.3 or digit_count > word_count * 0.3:
    return False
  return True


# Function to process the file and filter coherent sentences
def process_notes(file_path):
  filtered_output = []

  # Open and read the file
  with open(file_path, 'r') as file:
    for line in file:
      # Split the line into the motif ID and the block of text
      if '\t' in line:
        motif_id, text = line.split('\t', 1)

        # Process the block of text with spaCy
        doc = nlp(text)

        # Collect coherent sentences
        coherent_sentences = []
        for sent in doc.sents:
          sentence_text = sent.text.strip()
          if is_coherent(sentence_text):
            coherent_sentences.append(sentence_text)

        # Combine motif ID with filtered sentences (join coherent sentences into a single string)
        if coherent_sentences:
          filtered_output.append(f"{motif_id}\t{' '.join(coherent_sentences)}")

  return filtered_output


# Run the function to process notes
filtered_results = process_notes(file_path)

# Output the filtered results to a TSV file
output_file_path = 'out/motifs/id_sentences_filtered_l.tsv'

with open(output_file_path, 'w') as out_file:
  for line in filtered_results:
    out_file.write(f"{line}\n")

print(f"Filtered sentences with motif IDs written to {output_file_path}")
