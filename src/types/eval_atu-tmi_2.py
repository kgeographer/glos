import psycopg2
import numpy as np
import os

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "database": "staging",
    "user": "postgres",
    "port": 5435
}

# Weighting score for ranks (Rank 1 = 10 points, Rank 10 = 1 point)
rank_weights = {i+1: 10-i for i in range(10)}

# Fetch the nearest motifs using pgvector directly from Postgres
def fetch_nearest_motifs_pgvector(conn, type_embedding_id, top_n=10):
    with conn.cursor() as cur:
        query = """
            SELECT motif_id, embedding <-> (SELECT embedding FROM folklore.type_embeddings WHERE type_id = %s) AS similarity
            FROM folklore.motif_embeddings
            ORDER BY embedding <-> (SELECT embedding FROM folklore.type_embeddings WHERE type_id = %s)
            LIMIT %s
        """
        cur.execute(query, (type_embedding_id, type_embedding_id, top_n))
        rows = cur.fetchall()

    return [(row[0].strip('.'), row[1]) for row in rows]  # Remove trailing period from motif IDs
# Fetch embeddings from the database
def fetch_type_embeddings(conn, limit=10):
    with conn.cursor() as cur:
        query = """
            SELECT type_id, embedding 
            FROM folklore.type_embeddings
            LIMIT %s
        """
        cur.execute(query, (limit,))
        rows = cur.fetchall()

    return {row[0]: np.array(row[1]) for row in rows}  # Dictionary with type_id as key and embedding as value

# Evaluate match percentage, rank, and weighted score for each ATU type
def evaluate_matches(conn, type_embeddings, edges_table, output_file='out/eval_atu_tmi.tsv'):
    with open(output_file, 'w') as outfile:
        # Write header to output file
        outfile.write("type_id\tassociated_motifs\tfetched_motifs\tmatch_percentage\tfirst_associated_rank\tweighted_score\n")

        cursor = conn.cursor()

        # Process each type embedding
        for type_id, type_embedding in type_embeddings.items():
            # Get Uther's associated motifs
            cursor.execute(f"SELECT motif_id FROM {edges_table} WHERE type_id = %s", (type_id,))
            associated_motifs = [row[0].strip('.') for row in cursor.fetchall()]  # Remove trailing period from motif IDs

            if not associated_motifs:
                continue  # Skip if no associated motifs found

            # Fetch nearest motifs using the embedding
            fetched_motifs = fetch_nearest_motifs_pgvector(conn, type_embedding)

            # Calculate match percentage
            fetched_ids = [motif_id for motif_id, _ in fetched_motifs]
            matches = [motif for motif in associated_motifs if motif in fetched_ids]
            match_percentage = (len(matches) / len(associated_motifs)) * 100 if associated_motifs else 0

            # Rank of first associated motif in fetched motifs
            first_associated_rank = min([fetched_ids.index(motif) + 1 for motif in matches], default=None)

            # Calculate weighted score
            weighted_score = sum([rank_weights.get(fetched_ids.index(motif) + 1, 0) for motif in matches])

            # Prepare output line
            associated_motifs_str = ','.join(associated_motifs)
            fetched_motifs_str = ','.join([motif_id for motif_id, _ in fetched_motifs])
            output_line = f"{type_id}\t{associated_motifs_str}\t{fetched_motifs_str}\t{match_percentage:.2f}\t{first_associated_rank}\t{weighted_score}\n"
            outfile.write(output_line)

    print(f"Evaluation results saved to {output_file}")

# Connect to the database
conn = psycopg2.connect(**DB_PARAMS)

# Fetch the first 10 type embeddings from the database
type_embeddings = fetch_type_embeddings(conn, limit=10)

# Run the evaluation
evaluate_matches(conn, type_embeddings, 'folklore.edges_atu_tmi')

# Close the database connection
conn.close()