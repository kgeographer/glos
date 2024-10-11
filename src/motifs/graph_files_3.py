# %% imports and helpers
import re
import csv
import networkx as nx
from networkx.algorithms.lowest_common_ancestors import lowest_common_ancestor


def generate_skos(hierarchy):
  skos_lines = []
  base_uri = "http://example.org/motifs/"

  def process_level(data, parent=None):
    for id_str, entry in data.items():
      concept_uri = f"<{base_uri}{id_str}>"
      skos_lines.append(f"{concept_uri} a skos:Concept ;")
      skos_lines.append(f"    skos:prefLabel \"{entry['label']}\" ;")

      if parent:
        parent_uri = f"<{base_uri}{parent['id']}>"
        skos_lines.append(f"    skos:broader {parent_uri} ;")

      # Add narrower relationship if it has a parent
      if parent:
        parent_uri = f"<{base_uri}{parent['id']}>"
        skos_lines.append(f"    {parent_uri} skos:narrower {concept_uri} ;")

      # End the block of triples with a single period.
      skos_lines[-1] = skos_lines[-1].rstrip(';') + " ."

      if entry['children']:
        process_level(entry['children'], entry)

  process_level(hierarchy)

  with open('out/motifs/motifs_skos.ttl', 'w', encoding='utf-8') as f:
    f.write("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n\n")
    f.write("\n".join(skos_lines))

def parse_id(id_str):
    # Treat single letters as a separate section header, not a range
    if len(id_str) == 1 and id_str.isalpha():
        return (float('-inf'), float('inf'))  # Treat single letters as spanning the entire range
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
    current_section = None  # Track the current section (L, M, etc.)

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

        # Check if it's a new section (e.g., 'L.' or 'M.')
        if len(id_str) == 1 and id_str.isalpha():
            current_section = id_str.rstrip('.')
            entry = {'id': current_section, 'label': label, 'children': {}}
            hierarchy[current_section] = entry
            stack = [(float('-inf'), float('inf'), entry)]  # Reset the stack for a new section
            continue

        # Ensure all motifs are within their section and don't create cross-section edges
        while stack and not (stack[-1][0] <= id_range[0] and id_range[1] <= stack[-1][1]):
            stack.pop()

        entry = {'id': id_str.rstrip('.'), 'label': label, 'children': {}}
        if stack:
            stack[-1][2]['children'][id_str] = entry
        else:
            hierarchy[id_str] = entry

        stack.append((id_range[0], id_range[1], entry))

    return hierarchy

def generate_tsv_files(hierarchy):
    nodes = []
    edges = []

    def process_level(data, parent=None):
        for id_str, entry in data.items():
            nodes.append((entry['id'], entry['label']))
            if parent:
                edges.append((entry['id'], parent['id']))
            if entry['children']:
                process_level(entry['children'], entry)

    process_level(hierarchy)

    with open('out/motifs/motif_nodes_gpt.tsv', 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['motif_id', 'label'])
        writer.writerows(nodes)

    with open('out/motifs/edges_synopsis.tsv', 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['motif_child', 'motif_parent'])
        writer.writerows(edges)

def get_ordered_parental_chain(G, node):
    # Get the ancestors of the node (including the node itself)
    ancestors = list(nx.ancestors(G, node))
    ancestors.append(node)

    # Sort based on the specificity of the motif (more specific motifs come later)
    # Single-letter nodes should always appear last
    ordered_ancestors = sorted(ancestors, key=lambda x: (len(x) == 1, len(x), x))

    return ordered_ancestors


# %% Read the full file & generate nodes, edges
file_path = 'data/motifs/detailed_synopsis_all.txt'
with open(file_path, 'r', encoding='utf-8') as file:
    text = file.read()

hierarchy = parse_motifs(text)
generate_tsv_files(hierarchy)
generate_skos(hierarchy)

print("TSV files 'motif_nodes_gpt.tsv' and 'edges_synopsis.tsv' have been generated.")

# %% Create a directed graph
G = nx.DiGraph()

# Add edges from your TSV file
with open('out/motifs/edges_synopsis.tsv', 'r') as f:
  next(f)  # Skip header
  for line in f:
    child, parent = line.strip().split('\t')
    G.add_edge(parent, child)

## USES

# %% Example usage of ordered parental chain
node = 'D810'
ordered_parental_chain = get_ordered_parental_chain(G, node)
print(f"Ordered parental chain for {node}: {ordered_parental_chain}")


# %% Example of finding lowest common ancestor
node1 = 'D800'
node2 = 'D810'
lca = lowest_common_ancestor(G, node1, node2)
print(f"Lowest common ancestor of {node1} and {node2}: {lca}")

# %% Search for motifs by keyword
def search_motifs_by_keyword(keyword):
    matches = []
    with open('out/motifs/motif_nodes_gpt.tsv', 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # Skip header
        for motif_id, label in reader:
            if keyword.lower() in label.lower():
                matches.append((motif_id, label))
    return matches

# Example usage
keyword = "magic"
results = search_motifs_by_keyword(keyword)
print(f"Motifs containing '{keyword}':")
for motif_id, label in results:  # Print first 5 results
    print(f"{motif_id}: {label}")


# %% vizualize the graph
import csv
import matplotlib.pyplot as plt
# first add labels to the nodes
with open('out/motifs/motif_nodes_gpt.tsv', 'r') as f:
  reader = csv.reader(f, delimiter='\t')
  next(reader)  # Skip header
  for motif_id, label in reader:
    G.nodes[motif_id]['label'] = label

def visualize_motif_branch(G, root_node, max_depth=2):
  def get_subgraph(node, current_depth):
    if current_depth > max_depth:
      return []
    children = list(G.successors(node))
    edges = [(node, child) for child in children]
    for child in children:
      edges.extend(get_subgraph(child, current_depth + 1))
    return edges

  subgraph_edges = get_subgraph(root_node, 1)
  subgraph = nx.DiGraph(subgraph_edges)

  # Ensure only nodes that are descendants of root_node are included
  descendants = nx.descendants(G, root_node)
  descendants.add(root_node)
  subgraph = subgraph.subgraph(descendants).copy()

  pos = nx.spring_layout(subgraph, k=0.9, iterations=50)
  plt.figure(figsize=(15, 10))
  nx.draw(subgraph, pos, with_labels=True, node_size=3000, node_color='lightblue',
          font_size=8, font_weight='bold', arrows=True)

  # Filter labels to include only nodes in the subgraph
  labels = {node: G.nodes[node]['label'] for node in subgraph.nodes}
  nx.draw_networkx_labels(subgraph, pos, labels, font_size=6)

  plt.title(f"Motif Branch: {root_node}")
  plt.axis('off')
  plt.tight_layout()
  plt.show()

# Example usage
visualize_motif_branch(G, 'D')
