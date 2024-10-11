# %% main script
import networkx as nx
import pandas as pd

# 253, 81, 85

# Path to the motif edges file
edges_file_path = 'results/edges_synopsis.tsv'  # Replace with your file path

# Initialize an empty directed graph
G = nx.DiGraph()

# Load the edge file
edges_df = pd.read_csv(edges_file_path, sep='\t')

# Add edges to the graph (the edge table should have 'child' and 'parent' columns)
for index, row in edges_df.iterrows():
    child = row['child']
    parent = row['parent']
    if parent and pd.notna(parent):  # Ensure parent is not NaN or empty
        G.add_edge(parent, child)

# Function to print descendants of a given node with labels and count the descendants
def print_descendants_and_count(graph, node, labels):
    if node in graph:
        # descendants = sorted(list(nx.descendants(graph, node)))  # Get all descendants
        descendants = list(nx.descendants(graph, node))  # Get all descendants
        # print(f"\nDescendants of {node}: {labels.get(node, 'No Label')}")
        # for descendant in descendants:
        #     label = labels.get(descendant, 'No Label')
        #     print(f"{descendant}: {label}")
        # Print the count of descendants
        print(f"Total descendants of {node}: {len(descendants)}")
        return len(descendants)
    else:
        print(f"Node '{node}' not found in the graph.")
        return 0

# Load the node labels from the motif nodes file
nodes_file_path = 'results/nodes_synopsis.tsv'  # Replace with your nodes file path
nodes_df = pd.read_csv(nodes_file_path, sep='\t')
labels = dict(zip(nodes_df['id'], nodes_df['label']))

# List of top-level nodes (A, B, C, D, etc.)
# top_level_categories = ['D']
top_level_categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Z']

# Run for each top-level category
for category in top_level_categories:
    # print(f"\n--- Processing category {category} ---")
    row_count = print_descendants_and_count(G, category, labels)

# Final comparison could happen after inspecting counts per category

# %% count nodes starting with each letter
import pandas as pd
from collections import defaultdict

# Load the node labels from the motif nodes file
nodes_file_path = 'results/nodes_synopsis.tsv'  # Replace with your file path
nodes_df = pd.read_csv(nodes_file_path, sep='\t')

# Create a dictionary to store the counts of nodes starting with each letter (A-Z, skipping I, O, Y)
prefix_counts = defaultdict(int)

# List of valid prefixes (A-Z, skipping I, O, Y)
valid_prefixes = [chr(i) for i in range(ord('A'), ord('Z') + 1) if chr(i) not in ['I', 'O', 'Y']]

# Iterate through the nodes and count based on the first letter of the node ID
for node_id in nodes_df['id']:
    if isinstance(node_id, str) and len(node_id) > 0:
        first_letter = node_id[0].upper()  # Get the first letter and convert to uppercase
        if first_letter in valid_prefixes:
            prefix_counts[first_letter] += 1

# Print the results
for prefix in valid_prefixes:
    print(f"Total nodes starting with '{prefix}': {prefix_counts[prefix]}")