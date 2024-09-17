import re
import pandas as pd

# Load sorted motif IDs that start with 'A'
def load_sorted_motif_ids(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines() if line.startswith('A')]

# Parse the notes file and associate motifs with their text blocks
def parse_notes_with_blocks(notes_file, sorted_motif_ids):
    with open(notes_file, 'r') as file:
        notes_text = file.read()

    # Initialize list to store results
    motif_blocks = []

    # Loop through each motif ID that starts with 'A'
    for i, motif_id in enumerate(sorted_motif_ids):
        # Use regex to find the motif ID at the beginning of a line
        current_id_position = re.search(rf'^{motif_id}\b', notes_text, flags=re.MULTILINE)

        # If the motif ID is not found at the beginning of a line, skip it
        if not current_id_position:
            continue

        current_id_position = current_id_position.start()

        # Determine the next motif ID in the sorted list to find the end of the block
        next_id_position = len(notes_text)  # Default to the end of the file
        if i + 1 < len(sorted_motif_ids):
            next_motif_id = sorted_motif_ids[i + 1]

            # Ensure next motif ID belongs to 'A' section and also appears at the beginning of a line
            next_id_match = re.search(rf'^{next_motif_id}\b', notes_text, flags=re.MULTILINE)
            if next_motif_id.startswith('A') and next_id_match:
                next_id_position = next_id_match.start()

        # Extract the text block between the current and next motif IDs
        block = notes_text[current_id_position + len(motif_id):next_id_position].strip()

        # Replace newlines with spaces to form a single block of text
        block = re.sub(r'\s+', ' ', block)

        # Strip leading period and space
        block = block.lstrip('. ')

        # Add the motif and its block to the result list
        motif_blocks.append((motif_id, block))

    return motif_blocks

# Save the extracted motifs and blocks to TSV
def save_motif_blocks_to_tsv(motif_blocks, output_file):
    df = pd.DataFrame(motif_blocks, columns=['ID', 'Block'])
    df.to_csv(output_file, sep='\t', index=False)
    print(f"Motif blocks extracted and saved to {output_file} in TSV format.")

# Paths
sorted_motif_file = 'data/motifs/motif_ids_sorted.txt'
notes_file = 'data/motifs/notes_a.txt'
output_file = 'out/motifs/motif_blocks_notes_a.tsv'

# Load sorted motif IDs that start with 'A'
sorted_motif_ids = load_sorted_motif_ids(sorted_motif_file)

# Parse the notes file and extract motif blocks
motif_blocks = parse_notes_with_blocks(notes_file, sorted_motif_ids)

# Save the result to TSV
save_motif_blocks_to_tsv(motif_blocks, output_file)
