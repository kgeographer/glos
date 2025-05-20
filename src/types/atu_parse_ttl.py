import rdflib
import csv
import re

# Initialize graph and load TTL data
g = rdflib.Graph()
input_file = 'data/atu/tmi_atu5_sw4.ttl'
g.parse(input_file, format='ttl')

# Define namespaces if needed (you might need to adjust this based on the actual TTL file)
namespace = rdflib.Namespace("http://www.semanticweb.org/tonka/ontologies/2015/5/tmi-atu-ontology#")
rdf = rdflib.RDF
rdfs = rdflib.RDFS

# Output file path
output_file = 'out/motifs/atu_types_sections.tsv'


# Function to extract text between double quotes
def extract_label(label_literal):
  # Convert the label_literal to a string and use regex to extract the text inside double quotes
  match = re.search(r'\"(.*?)\"', str(label_literal))
  if match:
    return match.group(1)
  return str(label_literal)


# Prepare TSV output
with open(output_file, 'w', newline='', encoding='utf-8') as tsvfile:
  writer = csv.writer(tsvfile, delimiter='\t')
  # Write header
  writer.writerow(['type_id', 'label', 'text'])

  # Query all instances of rdf:type :Type
  for subj in g.subjects(rdf.type, namespace.Type):
    # Extract the type_id
    type_id = subj.split("#")[-1]

    # Extract the label (use regex to extract the text within double quotes)
    label_literal = g.value(subj, rdfs.label)
    if label_literal:
      label = extract_label(label_literal)
    else:
      label = ""

    # Extract the text (rdfs:isDefinedBy value)
    text_literal = g.value(subj, rdfs.isDefinedBy)
    if text_literal:
      text = str(text_literal)
    else:
      text = ""

    # Write to the TSV file
    writer.writerow([type_id, label, text])

print(f"Finished parsing. Output saved to {output_file}")