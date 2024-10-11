import re

# Sample data: A list of motif IDs and labels (could be read from a file)
motifs = [
    "A15.3.1\tOld man with staff as creator (cf.",
    "A15.4\tArtisan as creator.",
    "A15.4.1\tPotter as creator. India: Thompson-Balys.",
    "A1611.5.4.3\tOrigin of the Tuatha Dé Danann.",
    "A162.1.0.1\tRecurrent battle.",
    "A18.1\tCreator with dragon's head. Chinese: Werner 77.",
    "A18.2\tCreator with two horns on head. Chinese: Werner 76.",
    "A"
]

# Function to split the motif into parts for sorting
def split_motif(motif_id):
    # Match alphabetic prefix and numeric parts
    match = re.match(r"([A-Za-z]+)([0-9.]+)", motif_id)
    if match:
        prefix = match.group(1)
        numeric_part = match.group(2).split('.')
        # Convert numeric parts to integers for correct sorting
        numeric_part = [int(n) for n in numeric_part]
        return (prefix, numeric_part)
    else:
        # If no numbers, just return the motif as-is (for cases like "A")
        return (motif_id, [])

# Sort motifs by splitting and sorting based on prefix and numeric parts
sorted_motifs = sorted(motifs, key=lambda x: split_motif(x.split("\t")[0]))

# Output the sorted motifs
for motif in sorted_motifs:
    print(motif)