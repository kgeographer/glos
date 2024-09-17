import re
import os

# Path to your directory containing notes files
data_directory = 'data/motifs/notes/'


# Function to process a file and extract motif IDs and their following text
def process_notes_file(file_path):
  # Regex pattern to match motif IDs (ensures they end with a period)
  pattern = r'[A-Z]\d+(?:\.\d+)*\.'

  # Read the file and replace newlines with spaces
  with open(file_path, 'r') as file:
    text = file.read().replace('\n', ' ')

  # Find all motif IDs and the text that follows each
  results = []
  matches = list(re.finditer(pattern, text))

  for i, match in enumerate(matches):
    motif_id = match.group().strip()  # Get the motif ID
    # Get the text from the current motif ID to the next one
    start = match.end()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
    block_text = text[start:end].strip()

    # Remove leading ". " if it exists
    if block_text.startswith('. '):
      block_text = block_text[2:].strip()

    # Append the motif ID and its associated text
    results.append(f"{motif_id}\t{block_text}")

  return results


# Process all notes files in the directory
notes_files = [f for f in os.listdir(data_directory) if re.match(r'notes_.*\.txt', f)]

for notes_file in notes_files:
  file_path = os.path.join(data_directory, notes_file)
  result_lines = process_notes_file(file_path)

  # Generate a unique output file for each notes file
  output_file = f'out/motifs/notes_processed/processed_{notes_file.split(".")[0]}.txt'
  with open(output_file, 'w') as out_file:
    for line in result_lines:
      out_file.write(f"{line}\n")

  print(f"Processing complete for {notes_file}. Output saved to {output_file}")
  