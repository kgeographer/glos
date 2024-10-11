import pandas as pd
import re

# Load the data from the file
input_file = 'out/tmi/motif-culture-or-distinct.tsv'
df = pd.read_csv(input_file, sep='\t', names=['motif_id', 'culture_term'])

# Function to split culture terms that contain lists inside parentheses
def expand_culture_terms(row):
    term = row['culture_term']
    # Check for parentheses with a list inside
    match = re.search(r'\(([^)]+)\)', term)
    if match:
        # Split the list of terms inside the parentheses
        terms_in_parens = match.group(1).split(',')
        expanded_rows = []
        for t in terms_in_parens:
            # Construct new rows with each term from the list in parentheses
            new_term = re.sub(r'\([^)]+\)', f"({t.strip()})", term)  # Replace with single term
            expanded_rows.append({'motif_id': row['motif_id'], 'culture_term': new_term})
        return expanded_rows
    else:
        # If no parentheses list is found, return the original row
        return [row]

# Expand rows where necessary
expanded_data = []
for index, row in df.iterrows():
    expanded_rows = expand_culture_terms(row)
    expanded_data.extend(expanded_rows)

# Create a new DataFrame from the expanded data
expanded_df = pd.DataFrame(expanded_data)

# Save the result to a new file
output_file = 'out/tmi/motif-culture-or-expanded.tsv'
expanded_df.to_csv(output_file, sep='\t', index=False, header=False)

print(f"File saved to {output_file}")