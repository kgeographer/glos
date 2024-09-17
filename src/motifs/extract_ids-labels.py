import re
import os

# Path to your directory containing notes files
data_directory = 'data/motifs/notes/'

# Get all notes files in the directory
notes_files = [f for f in os.listdir(data_directory) if re.match(r'notes_.*\.txt', f)]

# Regex pattern to match motif IDs
pattern = r'[A-Z]\d+(?:\.\d+)*\.'

# Initialize a set to keep track of all distinct motif IDs across all files
all_distinct_motif_ids = set()

# Loop through the files to open them, find motif IDs, and print the count
for notes_file in notes_files:
  file_path = os.path.join(data_directory, notes_file)

  try:
    with open(file_path, 'r') as file:
      text = file.read()
      # Find all motif IDs in the text
      motif_ids = re.findall(pattern, text)
      distinct_motif_ids = set(motif_ids)  # Get distinct motif IDs for this file
      all_distinct_motif_ids.update(distinct_motif_ids)  # Add to the global set

      motif_count = len(distinct_motif_ids)  # Count the number of distinct motif IDs
      print(f"File: {notes_file} | Found {motif_count} distinct motif IDs")

  except Exception as e:
    print(f"Failed to open {notes_file}. Error: {e}")

# Print the total number of distinct motif IDs found across all files
print(f"\nTotal distinct motif IDs found across all files: {len(all_distinct_motif_ids)}")
