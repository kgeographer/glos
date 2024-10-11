import spacy

# Load spaCy's small English model
nlp = spacy.load('en_core_web_sm')


# Function to assess grammatical coherence
def is_coherent_sentence(sentence):
  doc = nlp(sentence)

  # Check if the sentence has both a subject and a verb
  has_subject = any(token.dep_ == 'nsubj' for token in doc)
  has_verb = any(token.pos_ == 'VERB' for token in doc)

  return has_subject and has_verb


# Example usage:
sentences = [
  "Halcyon builds nest on sea-cliff to escape land hazards.",
  "Wienert FFC LVI *63 (ET 266), 140 (ST 462); Halm Aesop No. 29."
]

for s in sentences:
  if is_coherent_sentence(s):
    print(f"Coherent: {s}")
  else:
    print(f"Incoherent: {s}")