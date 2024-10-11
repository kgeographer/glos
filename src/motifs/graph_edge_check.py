import networkx as nx

# Initialize a directed graph
G = nx.DiGraph()

# Manually add the nodes
nodes = [
    'A100-A199', 'A100', 'A110', 'A120', 'A140', 'A150', 'A160', 'A170', 'A180', 'A190',
    'A200-A299', 'A200', 'A210', 'A220', 'A240', 'A250', 'A260', 'A270', 'A280',
    'A300-A399', 'A300', 'A310', 'A400-A499', 'A400', 'A410', 'A420', 'A430', 'A440',
    'A450', 'A460', 'A490'
]

# Add the nodes with dummy labels
for node in nodes:
    G.add_node(node, label=f"Label for {node}")

# Correct the edges to be parent -> child
edges = [
    ('A100-A499', 'A100-A199'), ('A100-A199', 'A100'), ('A100-A199', 'A110'), ('A100-A199', 'A120'),
    ('A100-A199', 'A140'), ('A100-A199', 'A150'), ('A100-A199', 'A160'), ('A100-A199', 'A170'),
    ('A100-A199', 'A180'), ('A100-A199', 'A190'), ('A100-A499', 'A200-A299'), ('A200-A299', 'A200'),
    ('A200-A299', 'A210'), ('A200-A299', 'A220'), ('A200-A299', 'A240'), ('A200-A299', 'A250'),
    ('A200-A299', 'A260'), ('A200-A299', 'A270'), ('A200-A299', 'A280'), ('A100-A499', 'A300-A399'),
    ('A300-A399', 'A300'), ('A300-A399', 'A310'), ('A100-A499', 'A400-A499'), ('A400-A499', 'A400'),
    ('A400-A499', 'A410'), ('A400-A499', 'A420'), ('A400-A499', 'A430'), ('A400-A499', 'A440'),
    ('A400-A499', 'A450'), ('A400-A499', 'A460'), ('A400-A499', 'A490')
]

G.add_edges_from(edges)

# Print edges to ensure they are added
print(f"Edges added: {list(G.edges)}")

# Function to retrieve and print all descendants
def print_descendants_with_labels(graph, node):
    if node in graph:
        descendants = list(nx.descendants(graph, node))
        if descendants:
            print(f"Descendants of {node}:")
            for descendant in sorted(descendants):
                label = graph.nodes[descendant]['label'] if 'label' in graph.nodes[descendant] else 'No Label'
                print(f"{descendant}: {label}")
        else:
            print(f"No descendants found for {node}.")
    else:
        print(f"Node '{node}' not found in the graph.")

# Example usage: Get all descendants of 'A100-A499' and print them
print_descendants_with_labels(G, 'A100-A499')

# Check direct children as well for debugging
print(f"Direct children of A100-A499: {list(G.successors('A100-A499'))}")
