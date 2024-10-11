import psycopg2
import csv

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "database": "staging",
    "user": "postgres",
    "port": 5435
}

# Function to fetch the associated motif IDs for a given ATU type
def fetch_associated_motif_ids(conn, type_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT motif_id
            FROM folklore.edges_atu_tmi
            WHERE type_id = %s
        """, (type_id,))
        rows = cur.fetchall()
    return [row[0] for row in rows]

# Function to fetch the embedding for a given type_id (ATU tale type)
def fetch_type_embedding(conn, type_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT embedding
            FROM folklore.type_embeddings
            WHERE type_id = %s
        """, (type_id,))
        row = cur.fetchone()
    if row:
        return row[0]  # Return the Postgres 'vector' type directly
    return None

# Function to fetch the 10 nearest motif embeddings using pgvector
def fetch_nearest_motifs_pgvector(conn, type_embedding, top_n=10, similarity_metric='cosine'):
    with conn.cursor() as cur:
        if similarity_metric == 'cosine':
            # Use cosine similarity explicitly in the query
            query = """
                SELECT motif_id, cosine_distance(embedding, %s) AS similarity
                FROM folklore.motif_embeddings
                ORDER BY cosine_distance(embedding, %s)
                LIMIT %s
            """
        else:
            # Use Euclidean distance (the default <-> operator)
            query = """
                SELECT motif_id, embedding <-> %s AS distance
                FROM folklore.motif_embeddings
                ORDER BY embedding <-> %s
                LIMIT %s
            """

        # Execute the query
        cur.execute(query, (type_embedding, type_embedding, top_n))
        rows = cur.fetchall()

    # Return a list of motif_id and their similarity/distance values
    return [(row[0], row[1]) for row in rows]

# Function to calculate match percentage: how many associated motifs are in fetched motifs
def calculate_match_percentage(associated_motif_ids, fetched_motif_ids):
    matches = set(associated_motif_ids).intersection(fetched_motif_ids)
    return len(matches) / len(associated_motif_ids) * 100 if associated_motif_ids else 0

# Function to calculate rank and weighted score
def calculate_rank_and_weighted_score(associated_motif_ids, fetched_motifs, top_n=10):
    fetched_motif_ids = [motif_id for motif_id, _ in fetched_motifs]

    # Rank: find the first match's index
    rank = next((i + 1 for i, motif_id in enumerate(fetched_motif_ids) if motif_id in associated_motif_ids), None)

    # Weighted score: higher rank yields a higher score
    if rank:
        weighted_score = (top_n - rank + 1) / top_n * 100  # Rank closer to 1 gives a higher score
    else:
        weighted_score = 0

    return rank, weighted_score

# Main function to process all ATU types in edges_atu_tmi and write to TSV
def process_all_types(output_file, top_n=10, similarity_metric='cosine'):
    conn = psycopg2.connect(**DB_PARAMS)

    try:
        with conn.cursor() as cur:
            # Fetch all distinct type_ids from edges_atu_tmi
            cur.execute("SELECT DISTINCT type_id FROM folklore.edges_atu_tmi")
            type_ids = [row[0] for row in cur.fetchall()]

        # Open the TSV file for writing
        with open(output_file, mode='w', newline='', encoding='utf-8') as tsvfile:
            writer = csv.writer(tsvfile, delimiter='\t')
            writer.writerow(['type_id', 'associated_motifs', 'fetched_motifs', 'match_percentage', 'rank', 'weighted_score'])

            for type_id in type_ids[:10]:  # Limit to first 10 for testing
                # Step 1: Fetch associated motif IDs (Uther's assertions)
                associated_motif_ids = fetch_associated_motif_ids(conn, type_id)

                # Step 2: Fetch the ATU tale type's embedding
                type_embedding = fetch_type_embedding(conn, type_id)
                if type_embedding is None:
                    print(f"Embedding for type_id {type_id} not found, skipping.")
                    continue

                # Step 3: Fetch 10 nearest motifs using pgvector
                fetched_motifs = fetch_nearest_motifs_pgvector(conn, type_embedding, top_n, similarity_metric)
                fetched_motif_ids = [motif_id for motif_id, _ in fetched_motifs]

                # Step 4: Calculate match percentage based on Uther's ground truth
                match_percentage = calculate_match_percentage(associated_motif_ids, fetched_motif_ids)

                # Step 5: Calculate rank and weighted score
                rank, weighted_score = calculate_rank_and_weighted_score(associated_motif_ids, fetched_motifs, top_n)

                # Write to TSV file
                writer.writerow([type_id, ','.join(associated_motif_ids), ','.join(fetched_motif_ids),
                                 f'{match_percentage:.2f}', rank or 'None', f'{weighted_score:.2f}'])

                # Print progress
                print(f"Processed type_id {type_id} with {match_percentage:.2f}% match, rank: {rank}, weighted score: {weighted_score:.2f}")

        print(f"Evaluation written to {output_file}")

    finally:
        conn.close()

# Run the script
if __name__ == "__main__":
    output_file = 'out/eval_atu-tmi_euc.tsv'
    process_all_types(output_file, top_n=10, similarity_metric='euclidean')  # Change similarity_metric to 'euclidean' if needed
    # process_all_types(output_file, top_n=10, similarity_metric='cosine')  # Change similarity_metric to 'cosine' if needed
