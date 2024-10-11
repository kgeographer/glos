import re
import os

# Path to the directory containing the notes files
data_directory = 'data/motifs/'

# Load the existing detailed synopsis to check for already accounted motifs
with open(os.path.join(data_directory, 'detailed_synopsis_all.txt'), 'r') as file:
    existing_synopsis = file.read()

# Regex pattern to match motif IDs and descriptions
# pattern = r'(A\d+(?:\.\d+)*\.)\s*(.*?)(?=\sA\d+|\Z)'
pattern = r'([A-Z]\d+(?:\.\d+)*\.)\s*(.*?)(?=\s[A-Z]\d+|\Z)'

# Helper function to check if a sentence contains a reference (based on the presence of a colon)
def is_reference(text):
    return ':' in text

# Helper function to process a description that may contain multiple motif IDs
def process_multiple_motifs(description):
    """Process a description that may contain multiple motif IDs."""
    # parts = re.split(r'(A\d+(?:\.\d+)*\.)', description)
    parts = re.split(r'([A-Z]\d+(?:\.\d+)*\.)', description)
    parts = [part.strip() for part in parts if part.strip()]
    result = []
    for i in range(0, len(parts), 2):
        if i + 1 < len(parts):
            result.append((parts[i], parts[i + 1]))
    return result

# Function to process a single file
def process_notes_file(file_path, output_file):
    with open(file_path, 'r') as file:
        notes = file.read()

    # Extract motif IDs and descriptions from the notes file
    new_motifs = re.findall(pattern, notes)

    # List to collect new motifs to write to a file
    collected_motifs = []

    for motif_id, description1 in new_motifs:
        motif_id_clean = motif_id.rstrip('.')

        # If motif ID is not in the existing synopsis
        if motif_id_clean not in existing_synopsis:
            processed = process_multiple_motifs(description1)

            if processed:
                for id_part, desc_part in processed:
                    if not is_reference(desc_part):
                        desc_part_clean = re.sub(r'\s*\(cf\.?\s*', '', desc_part, flags=re.IGNORECASE).strip()
                        collected_motifs.append((id_part, desc_part_clean))
            else:
                if not is_reference(description1.strip()):
                    description_clean = re.sub(r'\s*\(cf\.?\s*', '', description1.strip(), flags=re.IGNORECASE).strip()
                    collected_motifs.append((motif_id_clean, description_clean))

    # Write the results to an output file
    with open(output_file, 'w') as out_file:
        for motif_id, description in collected_motifs:
            out_file.write(f"{motif_id}\t{description}\n")

# Function to process multiple files from the directory
def process_multiple_files(data_directory, num_files):
    # List all files matching the pattern 'notes_*.txt'
    notes_files = [f for f in os.listdir(data_directory) if re.match(r'notes_.*\.txt', f)]
    notes_files = sorted(notes_files)[:num_files]  # Process only the specified number of files

    for notes_file in notes_files:
        file_path = os.path.join(data_directory, notes_file)
        output_file = os.path.join('out/motifs', f'new_motifs_{notes_file.split("_")[1].split(".")[0]}.txt')
        print(f"Processing {notes_file}...")
        process_notes_file(file_path, output_file)
        print(f"Finished processing {notes_file}, results saved to {output_file}")

# Specify the number of files to process (adjust this number as needed)
num_files_to_process = 3
process_multiple_files(data_directory, num_files_to_process)
