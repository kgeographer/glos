import pandas as pd
import difflib

# Load the file containing duplicate motif IDs
file_path = 'out/motifs/notes_duplicate_ids.tsv'
df = pd.read_csv(file_path, sep='\t', header=None, names=['MotifID', 'Description'])

# Ensure the Description column is of string type and handle missing values
df['Description'] = df['Description'].fillna('').astype(str)

# Remove rows where Description is empty
df = df[df['Description'].str.strip() != '']

# Function to combine and deduplicate similar sentences
def combine_sentences(group):
    # Split descriptions into sentences and add them to a list
    sentences = []
    for desc in group['Description']:
        sentences.extend([s.strip() for s in desc.split('. ') if s.strip()])

    # Function to check similarity between sentences
    def are_similar(s1, s2):
        # Get a similarity score between 0 and 1
        return difflib.SequenceMatcher(None, s1, s2).ratio() > 0.75  # Adjust threshold as needed

    # Deduplicate similar sentences by keeping the longer one or combining complementary info
    final_sentences = []
    while sentences:
        current = sentences.pop(0)
        similar_found = False
        for i, sent in enumerate(final_sentences):
            if are_similar(current, sent):
                if len(current) > len(sent):
                    final_sentences[i] = current
                similar_found = True
                break
        if not similar_found:
            final_sentences.append(current)

    # Join the unique sentences back into a single string
    return '. '.join(sorted(set(final_sentences))) + '.'  # Ensure it ends with a period

# Group by MotifID and combine/deduplicate sentences
df_cleaned = df.groupby('MotifID').apply(combine_sentences).reset_index()

# Rename columns
df_cleaned.columns = ['MotifID', 'CombinedDescription']

# Save the cleaned result
output_path = 'out/motifs/notes_combined_sentences.tsv'
df_cleaned.to_csv(output_path, sep='\t', index=False)

print(f"File saved to {output_path}")
