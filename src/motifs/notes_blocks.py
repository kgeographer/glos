import re

# Sample snippet of text for testing
sample_text = """
A1201. Man created to rule the earth. Africa (Fang): Trilles 131.
A1205. Unacceptable gods as first inhabitants of earth. Hawaii: Beck-
with Myth 60.
A1210. Creation of man by creator. *Dh I 89. - Irish myth: Cross; Greek: *Grote I 71; Spanish Exempla: Keller; Lithuanian: Balys In- dex No. 3030; India: Thompson-Balys; Chinese: Werner 81. Maori: Dixon 23, 26; Easter Is.: Métraux Ethnology 312; Hawaiian, Tahitan: Dixon 26; Aztec: Alexander Lat. Am. 92; S. Am. Indian (Cashinawa): Métraux BBAE CXLIII (3) 684, (Tucuna): Nimuendajú ibid. 724; Africa (Fjort): Dennett 105, (Ibo of Nigeria): Basden 282, (Ekoi): Talbot 373.
A1614.5 A0. Creator. A141.1. God makes automata and vivifies them. Negroes made from left-over scraps at creation. G312.5. Fierce flesh- eating creatures made by creator in fit of anger.
A1211. Man made from creator's body. India: Thompson-Balys.
A614. Universe from parts of creator's body.
A1211.0.1. Man springs into existence from deity's body by his mere thinking. India: Thompson-Balys.
New
A1211.1. Man from dirt mixed with creator's blood. Eitrem Opferritus und Voropfer der Griechen und Römer (Skrifter Akad. Oslo 1914 No. 1 426). Gaster Oldest Stories 69; Babylonian: Spence 81. Britain: Dixon 107 (figures drawn on ground and sprinkled with creator's blood).
A1211.2. Man from sweat of creator. Dh I 113; Lithuanian: Balys Legends No. 33. Persian: Carnoy 293.
"""

# Regex pattern to match motif IDs and blocks of text
motif_pattern = r'([A-Z]\d+(?:\.\d+)*\.)\s*(.*?)((?=[A-Z]\d+)|\Z)'


# Function to process the sample text and extract motifs and their blocks
def extract_motifs_and_blocks(text):
  # Replace line breaks with spaces to handle multiline descriptions
  text = text.replace('\n', ' ')

  # Find all motif matches using the regex
  matches = re.findall(motif_pattern, text, re.DOTALL)

  # Store results as a list of (motif ID, block)
  results = []

  for match in matches:
    motif_id = match[0].strip()
    block = match[1].strip()
    results.append((motif_id, block))

  return results


# Extract motifs and their blocks from the sample text
motif_blocks = extract_motifs_and_blocks(sample_text)

# Display the results for inspection
for motif_id, block in motif_blocks:
  print(f"ID: {motif_id}")
  print(f"Block: {block}")
  print('-' * 40)