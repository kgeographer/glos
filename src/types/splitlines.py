import re

input_file = 'out/atu/tale_motif.txt'
output_file = 'out/atu/tale_motif_split.txt'


def split_keys_and_entries(input_file, output_file):
  # Pattern for double entries (two key-value pairs on the same line)
  double_entry_pattern = re.compile(r'^(.*?:.*?\.)\s+(.*:.*\.)$')

  # Updated pattern for multiple keys, allowing letters, digits, and asterisks
  multiple_key_pattern = re.compile(r'^([\w\*]+(?:,\s*[\w\*]+)*)\s*:\s*(.+)$')

  with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
      # First, handle double entries
      match = double_entry_pattern.match(line.strip())
      if match:
        lines_to_process = [match.group(1), match.group(2)]
      else:
        lines_to_process = [line.strip()]

      # Then, handle multiple keys for each resulting line
      for entry in lines_to_process:
        key_match = multiple_key_pattern.match(entry)
        if key_match:
          keys = re.split(r',\s*', key_match.group(1))
          value = key_match.group(2)
          for key in keys:
            outfile.write(f"{key.strip()}: {value}\n")
        else:
          outfile.write(f"{entry}\n")


# Usage
split_keys_and_entries(input_file, output_file)
