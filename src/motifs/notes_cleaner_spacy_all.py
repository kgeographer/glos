import spacy
import os

# Load the spaCy English model
nlp = spacy.load('en_core_web_sm')

# Input and output directories
input_directory = 'out/motifs/notes_processed/'
output_directory = 'out/motifs/notes_processed/'

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

# Function to process a single file and filter coherent sentences
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

# Function to process all files in the specified folder
def process_all_notes(input_directory, output_directory):
    # List all files matching the pattern 'processed_notes_*.txt'
    for filename in os.listdir(input_directory):
        if filename.startswith('processed_notes_') and filename.endswith('.txt'):
            file_path = os.path.join(input_directory, filename)
            print(f"Processing {filename}...")

            # Process the file
            filtered_results = process_notes(file_path)

            # Write the filtered results to the corresponding output file
            output_filename = f"ids_sentences_{filename.split('_')[-1]}"
            output_file_path = os.path.join(output_directory, output_filename)

            with open(output_file_path, 'w') as out_file:
                for line in filtered_results:
                    out_file.write(f"{line}\n")

            print(f"Filtered sentences with motif IDs written to {output_file_path}")

# Run the function to process all notes files
process_all_notes(input_directory, output_directory)