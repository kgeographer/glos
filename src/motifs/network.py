# %%
import networkx as nx
from networkx.algorithms.lowest_common_ancestors import lowest_common_ancestor

# Create a directed graph
G = nx.DiGraph()

# %% Add edges from your TSV file
with open('out/motifs/motif_edges.tsv', 'r') as f:
    next(f)  # Skip header
    for line in f:
        child, parent = line.strip().split('\t')
        G.add_edge(parent, child)

# %% Get the parental chain for a specific node
node = 'A100'
parental_chain = list(nx.ancestors(G, node))
parental_chain.append(node)
parental_chain.sort(key=lambda x: int(x[1:]))  # Sort based on the numerical part of the ID
print(f"Parental chain for {node}: {parental_chain}")


# %% Find the lowest common ancestor of two nodes
node1 = 'A10'
node2 = 'A100'
lca = lowest_common_ancestor(G, node1, node2)
print(f"Lowest common ancestor of {node1} and {node2}: {lca}")
