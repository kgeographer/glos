# %% imports and helper functions
import re


# Step 1: Clean the detailed synopsis (remove range lines and keep individual IDs)
def clean_detailed_synopsis(input_file):
  cleaned_motifs = {}  # Use a dictionary to store motif IDs and their descriptions

  # Read the detailed synopsis from the input file
  with open(input_file, 'r') as file:
    lines = file.readlines()

  # Process each line
  for line in lines:
    # Remove lines that contain ranges (e.g., "A100-A499")
    if re.search(r'\d+-\d+', line):
      continue

    # Keep lines with individual motif IDs (e.g., "A100. Deity")
    match = re.search(r'^(A\d+(\.\d+)*?)\.\s(.+)', line)
    if match:
      motif_id = match.group(1)  # Extract the motif ID
      description = match.group(3).strip()  # Extract the description
      cleaned_motifs[motif_id] = description  # Add motif ID and description to the dictionary

  return cleaned_motifs


# Step 2: Extract missing motif IDs from the detailed notes
def extract_missing_motifs(notes, existing_motifs):
  missing_motifs = {}

  # Regex to capture motif IDs and their descriptions (handles multiple decimals)
  # Match any motif ID starting with A, followed by numbers and decimals, then capture the description
  motif_pattern = r'(A\d+(?:\.\d+)*?)\.\s(.*?)(?=\sA\d+|\Z)'

  # Find all matches in the notes
  matches = re.findall(motif_pattern, notes, re.DOTALL)

  # Process each match
  for match in matches:
    motif_id = match[0].strip()  # Motif ID (e.g., "A35.3.2")
    description = match[1].strip().replace('\n', ' ')  # Extract and clean the description

    # If the motif ID is not in the existing detailed synopsis, it is missing
    if motif_id not in existing_motifs:
      missing_motifs[motif_id] = description

  return missing_motifs


# Step 3: Backfill the detailed synopsis with missing motifs
def backfill_detailed_synopsis(existing_motifs, missing_motifs, output_file):
  with open(output_file, 'w') as file:
    # First, write the existing detailed synopsis motifs
    for motif, description in sorted(existing_motifs.items()):
      file.write(f"{motif}. {description}\n")

    # Now, append the missing motifs
    for motif, description in sorted(missing_motifs.items()):
      file.write(f"{motif}. {description}\n")


# %% Step 1: Load and clean the detailed synopsis for letter A
input_synopsis_file = 'data/motifs/detailed_synopsis_A.txt'
cleaned_motifs = clean_detailed_synopsis(input_synopsis_file)

# %% Step 2: Process a chunk of notes and extract missing motifs
notes = """
A0. Creator. For a general bibliography of creation myths, see Alexander N. Am. 278 n. 15. ...
A1. First instance of creator. An additional example of the motif.
A151. Special nature of god.
A610. Creation of universe by creator. A631. Pre-existing world of gods above.
A810.1. God and devil fly together over primeval water. A830. Creation of earth by creator.
A923. Ocean from creator's sweat. A1187. Creator appoints chief for each class of created things: Lucifer for demons, Zion for mountains, etc.
A1210. Creation of man by creator.
A35.3.2. God speaks to creator. A35.3.3. Creator listens to god.
"""
missing_motifs = extract_missing_motifs(notes, cleaned_motifs)

# %% Step 3: Backfill the detailed synopsis with the missing motifs
output_file = 'out/motifs/backfilled_detailed_synopsis_A.txt'
backfill_detailed_synopsis(cleaned_motifs, missing_motifs, output_file)

# %% Print missing motifs for inspection
print("Missing motifs extracted from notes:")
for motif, description in missing_motifs.items():
  print(f"{motif}: {description}")