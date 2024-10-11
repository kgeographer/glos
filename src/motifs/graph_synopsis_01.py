import networkx as nx
import pandas as pd

# Load nodes
nodes_df = pd.read_csv('results/nodes_synopsis.tsv', sep='\t')
edges_df = pd.read_csv('results/edges_synopsis.tsv', sep='\t')

# Initialize a directed graph
G = nx.DiGraph()

# Add nodes with their labels
for index, row in nodes_df.iterrows():
    G.add_node(row['id'], label=row['label'])

# Add edges (parent-child relationships)
for index, row in edges_df.iterrows():
    if pd.notna(row['parent']):  # Avoid the null parent
        G.add_edge(row['parent'], row['child'])

# Function to retrieve all descendants of a node and print them with labels
def print_descendants_with_labels(graph, node):
  if node in graph:
    # Print the label of the node itself
    node_label = graph.nodes[node]['label'] if 'label' in graph.nodes[node] else 'No Label'
    print(f"Descendants of {node}: {node_label}")

    # Get the list of descendants and sort it
    descendants = sorted(list(nx.descendants(graph, node)))  # Sort the descendants

    for descendant in descendants:
      label = graph.nodes[descendant]['label'] if 'label' in graph.nodes[descendant] else 'No Label'
      print(f"{descendant}: {label}")
  else:
    print(f"Node '{node}' not found in the graph.")


# Prompt the user for a node to search
node_input = input("Enter a node ID: ")

# Example usage: Get all nodes below the entered node and print them with labels, sorted
print_descendants_with_labels(G, node_input)