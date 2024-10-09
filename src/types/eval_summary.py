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


# Function to fetch the embedding and text for a given type_id (ATU tale type)
def fetch_type_embedding(conn, type_id):
  with conn.cursor() as cur:
    cur.execute("""
            SELECT embedding, text
            FROM folklore.type_embeddings
            WHERE type_id = %s
        """, (type_id,))
    row = cur.fetchone()
  if row:
    return row[0], row[1]  # Return the embedding and text
  return None, None


# Function to fetch motif text for a given motif ID
def fetch_motif_text(conn, motif_id):
  with conn.cursor() as cur:
    cur.execute("""
            SELECT motif_text
            FROM folklore.motif_embeddings
            WHERE motif_id = %s
        """, (motif_id,))
    row = cur.fetchone()
  return row[0] if row else None


# Function to fetch the 10 nearest motif embeddings using pgvector
def fetch_nearest_motifs_pgvector(conn, type_embedding, top_n=10, similarity_metric='cosine'):
  with conn.cursor() as cur:
    if similarity_metric == 'cosine':
      # Use cosine similarity explicitly in the query
      query = """
                SELECT motif_id, motif_text, cosine_distance(embedding, %s) AS similarity
                FROM folklore.motif_embeddings
                ORDER BY cosine_distance(embedding, %s)
                LIMIT %s
            """
    else:
      # Use Euclidean distance (the default <-> operator)
      query = """
                SELECT motif_id, motif_text, embedding <-> %s AS distance
                FROM folklore.motif_embeddings
                ORDER BY embedding <-> %s
                LIMIT %s
            """

    # Execute the query
    cur.execute(query, (type_embedding, type_embedding, top_n))
    rows = cur.fetchall()

  # Return a list of motif_id, motif_text, and similarity/distance
  return [(row[0], row[1], row[2]) for row in rows]


# Function to calculate match percentage: how many associated motifs are in fetched motifs
def calculate_match_percentage(associated_motif_ids, fetched_motif_ids):
  matches = set(associated_motif_ids).intersection(fetched_motif_ids)
  return len(matches) / len(associated_motif_ids) * 100 if associated_motif_ids else 0


# Function to calculate rank and weighted score
def calculate_rank_and_weighted_score(associated_motif_ids, fetched_motif_ids):
  rank_sum = 0
  rank_matches = 0
  max_rank = len(fetched_motif_ids)

  # Go through each associated motif and check its rank in fetched motifs
  for associated_motif in associated_motif_ids:
    if associated_motif in fetched_motif_ids:
      rank = fetched_motif_ids.index(associated_motif) + 1  # Rank starts from 1
      rank_sum += rank
      rank_matches += 1

  # Calculate the weighted score as the inverse rank sum (lower ranks are better)
  weighted_score = (rank_matches / rank_sum) * 100 if rank_sum > 0 else 0
  return rank_matches, weighted_score


# Function to generate an output for unmatched types
def output_unmatched_types(conn, type_id, type_text, associated_motifs, fetched_motifs):
  # Prepare a detailed output for non-matching type_ids
  output_data = [f"Type ID: {type_id}", f"Type Text: {type_text}", f"Associated Motifs: {', '.join(associated_motifs)}"]

  # Fetch the text of each associated motif (Uther's motifs)
  associated_motif_texts = []
  for motif_id in associated_motifs:
    motif_text = fetch_motif_text(conn, motif_id)
    associated_motif_texts.append(f"  {motif_id}: {motif_text}" if motif_text else f"  {motif_id}: [No text found]")

  # Add the associated motifs with their text
  output_data.append("Associated Motif Texts:")
  output_data.extend(associated_motif_texts)

  # Add the fetched motifs with their text and similarity
  output_data.append("Closest Fetched Motifs:")
  for motif_id, motif_text, similarity in fetched_motifs:
    output_data.append(f"  Motif ID: {motif_id}, Text: {motif_text}, Similarity: {similarity:.4f}")

  output_data.append("\n")
  return "\n".join(output_data)


# Main function to process all ATU types in edges_atu_tmi and write to TSV
def process_all_types(output_file, unmatched_file, top_n=10, similarity_metric='cosine'):
  conn = psycopg2.connect(**DB_PARAMS)

  # Variables to track success rates
  total_types = 0
  total_100_match = 0
  total_partial_match = 0

  try:
    with conn.cursor() as cur:
      # Fetch all distinct type_ids from edges_atu_tmi
      cur.execute("SELECT DISTINCT type_id FROM folklore.edges_atu_tmi")
      type_ids = [row[0] for row in cur.fetchall()]

    # Open the TSV file for writing the evaluation
    with open(output_file, mode='w', newline='', encoding='utf-8') as tsvfile, open(unmatched_file, mode='w',
                                                                                    encoding='utf-8') as unmatchedfile:
      writer = csv.writer(tsvfile, delimiter='\t')
      writer.writerow(['type_id', 'associated_motifs', 'fetched_motifs', 'match_percentage', 'rank', 'weighted_score'])

      unmatched_output = []

      for type_id in type_ids:  # Process all types (1700+)
        total_types += 1

        # Step 1: Fetch associated motif IDs (Uther's assertions)
        associated_motif_ids = fetch_associated_motif_ids(conn, type_id)

        # Step 2: Fetch the ATU tale type's embedding and text
        type_embedding, type_text = fetch_type_embedding(conn, type_id)
        if type_embedding is None:
          print(f"Embedding for type_id {type_id} not found, skipping.")
          continue

        # Step 3: Fetch 10 nearest motifs using pgvector
        fetched_motifs = fetch_nearest_motifs_pgvector(conn, type_embedding, top_n, similarity_metric)
        fetched_motif_ids = [motif_id for motif_id, _, _ in fetched_motifs]

        # Step 4: Calculate match percentage based on Uther's ground truth
        match_percentage = calculate_match_percentage(associated_motif_ids, fetched_motif_ids)

        # Step 5: Calculate rank and weighted score
        rank, weighted_score = calculate_rank_and_weighted_score(associated_motif_ids, fetched_motif_ids)

        # Track the match statistics for summary
        if match_percentage == 100:
          total_100_match += 1
        elif match_percentage > 0:
          total_partial_match += 1

        # Step 6: If no match, generate detailed output for further analysis
        if match_percentage == 0:
          unmatched_output.append(
            output_unmatched_types(conn, type_id, type_text, associated_motif_ids, fetched_motifs))

        # Step 7: Write evaluation to TSV
        writer.writerow([type_id, ','.join(associated_motif_ids), ','.join(fetched_motif_ids),
                         f'{match_percentage:.2f}', rank, f'{weighted_score:.2f}'])  # Rank and weighted score added

        # Print progress
        print(
          f"Processed type_id {type_id} with {match_percentage:.2f}% match, Rank: {rank}, Weighted Score: {weighted_score:.2f}")

      # Write unmatched types to separate file
      unmatchedfile.write("\n".join(unmatched_output))
      print(f"Unmatched type details written to {unmatched_file}")

    # Print summary
    total_no_match = total_types - total_100_match - total_partial_match
    print("\nSummary:")
    print(f"Total types processed: {total_types}")
    print(f"100% match: {total_100_match} ({(total_100_match / total_types) * 100:.2f}%)")
    print(f"Partial match (1-99%): {total_partial_match} ({(total_partial_match / total_types) * 100:.2f}%)")
    print(f"No match (0%): {total_no_match} ({(total_no_match / total_types) * 100:.2f}%)")

    print(f"Evaluation written to {output_file}")

  finally:
    conn.close()


# Run the script
if __name__ == "__main__":
  output_file = 'out/eval_atu-tmi_euc.tsv'
  unmatched_file = 'out/unmatched_atu_tmi.txt'
  process_all_types(output_file, unmatched_file, top_n=10, similarity_metric='euclidean')
