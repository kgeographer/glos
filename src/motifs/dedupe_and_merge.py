import pandas as pd

# Paths to the master and deduplicated files
master_file_path = 'out/motifs/notes_cleaned_deduped1.tsv'
deduped_file_path = 'out/motifs/notes_combined_sentences.tsv'
output_file_path = 'out/motifs/notes_master_updated.tsv'

# Load the master file and the deduplicated file
master_df = pd.read_csv(master_file_path, sep='\t', header=None, names=['MotifID', 'Description'])
deduped_df = pd.read_csv(deduped_file_path, sep='\t', header=None, names=['MotifID', 'CombinedDescription'])

# Remove all rows from master that have motif IDs present in the deduplicated file
master_df = master_df[~master_df['MotifID'].isin(deduped_df['MotifID'])]

# Concatenate the cleaned deduplicated data into the master dataframe
final_df = pd.concat([master_df, deduped_df])

# Sort the final dataframe by MotifID (optional, for easier reading)
final_df = final_df.sort_values(by='MotifID')

# Write the updated master file to a new output file
final_df.to_csv(output_file_path, sep='\t', index=False, header=False)

print(f"Master file updated and saved to {output_file_path}")
