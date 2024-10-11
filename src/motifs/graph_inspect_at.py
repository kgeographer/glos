import networkx as nx
import pandas as pd

# Load nodes and edges from the files
nodes_file_path = 'out/motifs/graph/nodes_motifs.tsv'  # Change to the actual path
edges_file_path = 'out/motifs/graph/edges_motifs.tsv'  # Change to the actual path

# Create a directed graph
G = nx.DiGraph()

# Load nodes and add them to the graph
nodes_df = pd.read_csv(nodes_file_path, sep='\t', header=None, names=['motif_id', 'description'])
for _, row in nodes_df.iterrows():
    G.add_node(row['motif_id'], description=row['description'])

# Load edges and add them to the graph
edges_df = pd.read_csv(edges_file_path, sep='\t', header=None, names=['source', 'target'])
for _, row in edges_df.iterrows():
    G.add_edge(row['source'], row['target'])

# Calculate degree centrality (how many connections each node has)
degree_centrality = nx.degree_centrality(G)

# Calculate betweenness centrality (how often a node is on the shortest path between other nodes)
betweenness_centrality = nx.betweenness_centrality(G)

# Calculate closeness centrality (how close a node is to all other nodes)
closeness_centrality = nx.closeness_centrality(G)

# Calculate PageRank (importance of nodes in the graph)
pagerank = nx.pagerank(G)

# Function to get the top N nodes by centrality measure
def get_top_n(centrality_dict, n=10):
    return sorted(centrality_dict.items(), key=lambda x: x[1], reverse=True)[:n]

# Display top 10 nodes by degree centrality
print("Top 10 nodes by Degree Centrality:")
for node, centrality in get_top_n(degree_centrality):
    print(f"{node}: {centrality:.4f} ({G.nodes[node]['description']})")

# Display top 10 nodes by betweenness centrality
print("\nTop 10 nodes by Betweenness Centrality:")
for node, centrality in get_top_n(betweenness_centrality):
    print(f"{node}: {centrality:.4f} ({G.nodes[node]['description']})")

# Display top 10 nodes by closeness centrality
# (nneds all nodes referenced in edges to be present in the graph)
# print("\nTop 10 nodes by Closeness Centrality:")
# for node, centrality in get_top_n(closeness_centrality):
#     print(f"{node}: {centrality:.4f} ({G.nodes[node]['description']})")

# Display top 10 nodes by PageRank
print("\nTop 10 nodes by PageRank:")
for node, rank in get_top_n(pagerank):
    print(f"{node}: {rank:.4f} ({G.nodes[node]['description']})")
