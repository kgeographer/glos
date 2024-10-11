# %%
# Path to the cleaned file
input_file = 'out/motifs/notes_cleaned.tsv'
output_file = 'out/motifs/notes_cleaned_deduped1.tsv'

# Function to remove exact duplicates
def remove_exact_duplicates(input_file, output_file):
    with open(input_file, 'r') as infile:
        lines = infile.readlines()

    # Use a set to remove duplicate lines
    unique_lines = set(lines)

    # Write the unique lines to the output file
    with open(output_file, 'w') as outfile:
        outfile.writelines(unique_lines)

    print(f"Removed duplicates. Original lines: {len(lines)}, Unique lines: {len(unique_lines)}")

# Run the function to remove exact duplicates
remove_exact_duplicates(input_file, output_file)

# %% pull out duplicated motif IDs
from collections import defaultdict

# Path to the cleaned file without exact duplicates
input_file = 'out/motifs/notes_cleaned_deduped1.tsv'
duplicates_output_file = 'out/motifs/notes_duplicate_ids.tsv'

# Function to find duplicated motif IDs
def find_duplicates(input_file, duplicates_output_file):
    motif_dict = defaultdict(list)

    # Read the file and group lines by motif ID
    with open(input_file, 'r') as infile:
        for line in infile:
            if '\t' in line:
                motif_id, text = line.split('\t', 1)
                motif_dict[motif_id].append(line)

    # Find motif IDs with duplicates and write them to a new file
    with open(duplicates_output_file, 'w') as outfile:
        for motif_id, lines in motif_dict.items():
            if len(lines) > 1:  # Only include duplicates
                outfile.writelines(lines)

    print(f"Duplicated motif IDs written to {duplicates_output_file}")

# Run the function to extract duplicated motif IDs
find_duplicates(input_file, duplicates_output_file)