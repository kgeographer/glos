# %% Combine all notes files into a single file
import os

input_directory = 'out/motifs/notes_processed/'
output_file = 'out/motifs/notes_combined.tsv'

with open(output_file, 'w') as outfile:
    for filename in os.listdir(input_directory):
        if filename.startswith('ids_sentences_') and filename.endswith('.txt'):
            with open(os.path.join(input_directory, filename), 'r') as infile:
                outfile.write(infile.read())

# %% Clean the combined file
import re

# Define patterns
reference_pattern = r'your_reference_regex_here'
whitespace_pattern = r'\s+'
special_char_pattern = r'[^a-zA-Z0-9\s.,;:?!\'"-]'

# Define patterns to remove specific strings and everything that follows them on the same line
patterns_to_remove = [
    r' S\. Am\..*',
    r' N\. Am\..*',
    r' Am\..*',
    r' cf\..*',
    r' Cf\..*',
    r' f\..*',
    r' Calif\..*'
]


def clean_text(text):
    # Remove references
    text = re.sub(reference_pattern, '', text)
    # Replace multiple spaces with a single space
    text = re.sub(whitespace_pattern, ' ', text)
    # Remove special characters except common punctuation
    text = re.sub(special_char_pattern, '', text)
    # Remove specific patterns and everything that follows them on the same line
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text)
    # Remove instances of "- " (hyphen followed by space)
    text = re.sub(r'-\s+', '', text)

    return text.strip()

# Read combined file
combined_file = 'out/motifs/notes_combined.tsv'
cleaned_file = 'out/motifs/notes_cleaned.tsv'

with open(combined_file, 'r') as infile, open(cleaned_file, 'w') as outfile:
    for line in infile:
        motif_id, text = line.split('\t')
        cleaned_text = clean_text(text)
        outfile.write(f"{motif_id}\t{cleaned_text}\n")