import networkx as nx
import pandas as pd

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

# Function to print descendants of a given node with labels
def print_descendants_with_labels(graph, node, labels):
    if node in graph:
        descendants = sorted(list(nx.descendants(graph, node)))  # Get all descendants
        print(f"Descendants of {node}: {labels.get(node, 'No Label')}")
        for descendant in descendants:
            label = labels.get(descendant, 'No Label')
            print(f"{descendant}: {label}")
    else:
        print(f"Node '{node}' not found in the graph.")

# Load the node labels from the motif nodes file
nodes_file_path = 'results//nodes_synopsis.tsv'
nodes_df = pd.read_csv(nodes_file_path, sep='\t')
labels = dict(zip(nodes_df['id'], nodes_df['label']))

# Print the total count of nodes loaded into the labels dictionary
print(f"Total nodes loaded with labels: {len(labels)}")

# Prompt user for a node to search
node_id = input("Enter a node ID: ")

# Print the descendants with their labels
print_descendants_with_labels(G, node_id, labels)