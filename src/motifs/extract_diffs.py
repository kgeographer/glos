import re
import os

# Path to your directory containing notes files
data_directory = 'data/motifs/'

# Function to extract motif identifiers using the original pattern
def extract_motifs_original(file_path):
    pattern = r'[A-Z]\d+(?:\.\d+)*'
    with open(file_path, 'r') as file:
        text = file.read()
    return re.findall(pattern, text)

# Function to extract motif identifiers using the updated pattern
def extract_motifs_updated(file_path):
    pattern = r'[A-Z]\d+(?:\.\d+)*\.'
    with open(file_path, 'r') as file:
        text = file.read()
    return re.findall(pattern, text)

# Get motif identifiers from all files using both patterns
original_motif_ids = []
updated_motif_ids = []
notes_files = [f for f in os.listdir(data_directory) if re.match(r'notes_.*\.txt', f)]

for notes_file in notes_files:
    file_path = os.path.join(data_directory, notes_file)
    original_motif_ids += extract_motifs_original(file_path)
    updated_motif_ids += extract_motifs_updated(file_path)

# Remove duplicates
original_motif_ids = list(set(original_motif_ids))
updated_motif_ids = list(set(updated_motif_ids))

# Find differences between the two results
only_in_original = set(original_motif_ids) - set(updated_motif_ids)
only_in_updated = set(updated_motif_ids) - set(original_motif_ids)

# Output the results to compare
with open('out/motifs/diff_only_in_original.txt', 'w') as out_file:
    for motif_id in only_in_original:
        out_file.write(f"{motif_id}\n")

with open('out/motifs/diff_only_in_updated.txt', 'w') as out_file:
    for motif_id in only_in_updated:
        out_file.write(f"{motif_id}\n")

print(f"Found {len(only_in_original)} IDs only in original pattern.")
print(f"Found {len(only_in_updated)} IDs only in updated pattern.")