import re
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import SKOS, RDF

def parse_id(id_str):
    match = re.match(r'([A-Z])(\d+)(-([A-Z])(\d+))?', id_str)
    if match:
        start = int(match.group(2))
        end = int(match.group(5)) if match.group(5) else start
        return (start, end)
    return None

def parse_motifs(text):
    lines = text.split('\n')
    hierarchy = {}
    stack = []

    for line in lines:
        if not line.strip():
            continue

        parts = line.split('. ', 1)
        if len(parts) != 2:
            continue

        id_str, label = parts
        id_range = parse_id(id_str)
        if id_range is None:
            continue

        while stack and not (stack[-1][0] <= id_range[0] and id_range[1] <= stack[-1][1]):
            stack.pop()

        entry = {'id': id_str, 'label': label, 'children': {}}
        if stack:
            stack[-1][2]['children'][id_str] = entry
        else:
            hierarchy[id_str] = entry

        stack.append((id_range[0], id_range[1], entry))

    return hierarchy

def generate_skos(hierarchy):
    g = Graph()
    skos = Namespace("http://www.w3.org/2004/02/skos/core#")
    folklore = Namespace("http://example.org/folklore/")

    g.bind("skos", SKOS)
    g.bind("motifs", folklore)

    def add_concept(id_str, label, parent=None):
        concept_id = re.sub(r'[^A-Za-z0-9]+', '_', id_str).lower()
        concept = folklore[concept_id]
        g.add((concept, RDF.type, SKOS.Concept))
        g.add((concept, SKOS.prefLabel, Literal(f"{id_str}. {label}")))
        if parent:
            g.add((concept, SKOS.broader, parent))
            g.add((parent, SKOS.narrower, concept))
        print(f"Added concept: {id_str}. {label}, Parent: {parent}")
        return concept

    def process_level(data, parent=None):
        for id_str, entry in data.items():
            concept = add_concept(id_str, entry['label'], parent)
            if entry['children']:
                process_level(entry['children'], concept)

    process_level(hierarchy)
    return g

def generate_edge_list(hierarchy):
    edges = []

    def process_level(data, parent=None):
        for id_str, entry in data.items():
            if parent:
                edges.append((f"{id_str}. {entry['label']}", parent))
            if entry['children']:
                process_level(entry['children'], f"{id_str}. {entry['label']}")

    process_level(hierarchy)
    return edges

# Example usage
text = """A0-A99. Creator
A0. Creator
A10. Nature of the creator
A100-A499. GODS
A100-A199. The gods in general
A100. Deity"""

hierarchy = parse_motifs(text)
print("Parsed hierarchy:")
print(hierarchy)

skos_graph = generate_skos(hierarchy)
edge_list = generate_edge_list(hierarchy)

# Print SKOS (in Turtle format)
print("\nSKOS Representation:")
print(skos_graph.serialize(format="turtle"))

# Print edge list
print("\nEdge List:")
for edge in edge_list:
    print(f"{edge[0]} <has_parent> {edge[1]}")