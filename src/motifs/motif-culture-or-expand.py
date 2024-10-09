import pandas as pd
import re

# Load the data from the file
input_file = 'out/tmi/motif-culture-or-distinct.tsv'
df = pd.read_csv(input_file, sep='\t', names=['motif_id', 'culture_term'])

# Add an index column to preserve the order of the rows
df['original_order'] = df.index

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
            expanded_rows.append([row['motif_id'], new_term, row['original_order']])
        return expanded_rows
    else:
        # If no parentheses list is found, return the original row
        return [[row['motif_id'], row['culture_term'], row['original_order']]]

# Expand rows where necessary
expanded_data = []
for index, row in df.iterrows():
    expanded_rows = expand_culture_terms(row)
    expanded_data.extend(expanded_rows)

# Create a new DataFrame from the expanded data, maintaining the original order
expanded_df = pd.DataFrame(expanded_data, columns=['motif_id', 'culture_term', 'original_order'])

# Remove less specific terms (i.e., rows without parentheses) if more specific ones exist
def filter_more_specific(group):
    # If there are any terms with parentheses, remove the ones without parentheses
    has_specific_term = group['culture_term'].str.contains(r'\(').any()
    if has_specific_term:
        return group[group['culture_term'].str.contains(r'\(')]
    return group

# Group by motif_id and apply filtering
filtered_df = expanded_df.groupby('motif_id').apply(filter_more_specific).reset_index(drop=True)

# Sort back to the original order
filtered_df = filtered_df.sort_values(by='original_order').drop(columns=['original_order'])

# Save the result to a new file
output_file = 'out/tmi/motif-culture-or-expanded.tsv'
filtered_df.to_csv(output_file, sep='\t', index=False, header=False)

print(f"File saved to {output_file}")
