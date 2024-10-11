import spacy
import re
import os

# Load the spaCy English model
nlp = spacy.load('en_core_web_sm')

# Input and output directories
input_directory = 'data/motifs/notes_piped/'
output_directory = 'out/motifs/graph/'
log_file_path = os.path.join(output_directory, 'skipped_lines_log.txt')

# List of already processed letters
processed_letters = ['A', 'B', 'C']  # Add letters here as they get processed

# Regex to extract motif IDs
motif_id_pattern = r'\|([A-Z]\d+(?:\.\d+)*\.)\s*'
motif_in_text_pattern = r'([A-Z]\d+(?:\.\d+)*\.)'  # To find other motif IDs in text

# Function to determine if a sentence is coherent
def is_coherent(sentence):
    symbol_count = sum(1 for char in sentence if not char.isalnum() and char not in [' ', '.'])
    digit_count = sum(1 for char in sentence if char.isdigit())
    word_count = len(sentence.split())
    return symbol_count <= word_count * 0.3 and digit_count <= word_count * 0.3

# Function to capture the first phrase, even if it doesn't end in a period
def capture_first_phrase(text):
    first_phrase_match = re.search(r'[^.]+\.', text)  # Find text ending in a period
    if first_phrase_match:
        return first_phrase_match.group(0).strip()
    else:
        return text.strip()  # If no period found, capture the whole line as the first phrase

# Function to process a single file and filter coherent sentences
def process_notes(file_path, log_file):
    node_output = []
    edge_output = []
    total_lines = 0
    processed_lines = 0
    skipped_lines = 0

    with open(file_path, 'r') as file:
        for line in file:
            total_lines += 1
            motif_match = re.match(motif_id_pattern, line)
            if motif_match:
                motif_id = motif_match.group(1).strip()  # Extract motif ID
                text = line[motif_match.end():].strip()  # Rest of the line after motif ID

                # Capture the first phrase after motif ID
                first_phrase = capture_first_phrase(text)

                # Process the block of text with spaCy
                doc = nlp(text)

                # Collect coherent sentences
                coherent_sentences = []
                for sent in doc.sents:
                    sentence_text = sent.text.strip()
                    if is_coherent(sentence_text):
                        coherent_sentences.append(sentence_text)

                # Avoid adding the first phrase if it's already part of coherent_sentences
                if first_phrase:
                    if not coherent_sentences or first_phrase != coherent_sentences[0]:
                        all_sentences = [first_phrase] + coherent_sentences
                    else:
                        all_sentences = coherent_sentences
                else:
                    all_sentences = coherent_sentences

                if all_sentences:
                    processed_lines += 1
                    node_output.append(f"{motif_id}\t{' '.join(all_sentences)}")
                else:
                    skipped_lines += 1
                    log_file.write(f"Skipped line for Motif ID {motif_id}: No coherent sentences. Original line: {line.strip()}\n")

                # Find motif IDs in the text for creating edges
                related_motifs = re.findall(motif_in_text_pattern, text)
                for related_id in related_motifs:
                    if related_id != motif_id:  # Avoid self-referencing edges
                        edge_output.append(f"{motif_id}\t{related_id}")  # Source on the left, referenced on the right

            else:
                skipped_lines += 1
                log_file.write(f"Skipped line {total_lines}: No valid motif ID found. Original line: {line.strip()}\n")

    print(f"File processed: {file_path}")
    print(f"Total lines: {total_lines}, Processed: {processed_lines}, Skipped: {skipped_lines}")
    return node_output, edge_output

# Function to process all files in the specified folder
def process_all_notes(input_directory, output_directory, processed_letters):
    node_output_file = os.path.join(output_directory, 'nodes_motifs.tsv')
    edge_output_file = os.path.join(output_directory, 'edges_motifs.tsv')

    with open(node_output_file, 'a') as node_file, open(edge_output_file, 'a') as edge_file, open(log_file_path, 'a') as log_file:
        for filename in os.listdir(input_directory):
            if filename.endswith('_piped_1line.txt'):
                letter = filename[6].upper()  # Assuming filenames like 'notes_A_piped_1line.txt'

                # Skip files where the first letter has already been processed
                if letter in processed_letters:
                    print(f"Skipping file {filename} (already processed)")
                    continue

                file_path = os.path.join(input_directory, filename)
                print(f"Processing file: {file_path}")

                # Process the file
                nodes, edges = process_notes(file_path, log_file)

                # Write results to node and edge files
                for node in nodes:
                    node_file.write(f"{node}\n")
                for edge in edges:
                    edge_file.write(f"{edge}\n")


# Run the function to process all notes files
process_all_notes(input_directory, output_directory, processed_letters)
