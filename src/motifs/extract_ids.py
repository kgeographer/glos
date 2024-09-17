# %% extract all motif IDs form notes files
# then convert to tuples and sort
import re
import os

# Path to your directory containing notes files
data_directory = 'data/motifs/notes/'

# Function to extract motif identifiers
def extract_motif_identifiers(file_path):
    # Pattern to match motif IDs w/any # of decimal points
    pattern = r'[A-Z]\d+(?:\.\d+)*'

    with open(file_path, 'r') as file:
        text = file.read()

    # Find all motif IDs in the text
    return re.findall(pattern, text)

# Get all motif identifiers across all files
all_motif_ids = []
notes_files = [f for f in os.listdir(data_directory) if re.match(r'notes_.*\.txt', f)]

for notes_file in notes_files:
    file_path = os.path.join(data_directory, notes_file)
    all_motif_ids += extract_motif_identifiers(file_path)

# Remove duplicates
all_motif_ids = list(set(all_motif_ids))

# Output the extracted motifs to a file for review (optional)
with open('out/motifs/extracted_motif_ids.txt', 'w') as out_file:
    for motif_id in all_motif_ids:
        out_file.write(f"{motif_id}\n")

# %% convert all_motif_ids[] to numerical tuples, sort, save to motif_ids_sorted.txt
def convert_to_tuple(motif_id):
    letter = motif_id[0]  # 'A', 'B', etc.
    numbers = motif_id[1:].split('.')  # Split on the decimal points
    return (letter, tuple(int(num) for num in numbers))

# Convert all motif IDs to numerical tuples
motif_tuples = [convert_to_tuple(motif_id) for motif_id in all_motif_ids]

# Sort the motif IDs numerically
sorted_motif_tuples = sorted(motif_tuples)

# Convert the sorted tuples back to their original form
sorted_motif_ids = []
for letter, numbers in sorted_motif_tuples:
    sorted_motif_ids.append(f"{letter}{'.'.join(map(str, numbers))}")

# Output the sorted motifs to a file for review (optional)
with open('out/motifs/motif_ids_sorted.txt', 'w') as out_file:
    for motif_id in sorted_motif_ids:
        out_file.write(f"{motif_id}\n")