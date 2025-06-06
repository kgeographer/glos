import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

# fuzzy = True enables pg_trgm-based search; assumes extension is installed and indexed
fuzzy = True  # Set to True to use PostgreSQL trigram similarity

# Load env vars or manually define connection
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cur = conn.cursor()
cur.execute("SET search_path TO folklore, public;")

# Toggle these
search_fields = ["text"]  # Options: ['label'], ['text'], ['label', 'text']
search_terms = ["fire-breathing dragon"] # Add terms here, 1, >1 with comma]
logic = "AND"  # OR or AND
mode = "motifs"  # "types" or "motifs"

# Build WHERE clause
where_clauses = []
params = []

for term in search_terms:
    term_clauses = [f"{field} ILIKE %s" for field in search_fields]
    clause = "(" + " OR ".join(term_clauses) + ")"
    where_clauses.append(clause)
    params.extend([f"%{term}%"] * len(search_fields))

# Determine table and fields based on mode
if mode == "types":
    table = "folklore.type_embeddings_3sm"
    id_field = "type_id"
    select_fields = "type_id, label, LEFT(text, 300) AS snippet"
elif mode == "motifs":
    table = "folklore.motif_text"
    id_field = "motif_id"
    select_fields = "motif_id, text, NULL AS snippet"  # no text field in motifs
else:
    raise ValueError("Invalid mode: must be 'types' or 'motifs'")

# Query
if fuzzy:
    # Only one term is supported for fuzzy search
    if len(search_terms) != 1:
        raise ValueError("Fuzzy search only supports one search term at a time.")
    fuzzy_term = search_terms[0]
    query = f"""
        SELECT {select_fields}
        FROM {table}
        WHERE similarity({search_fields[0]}::text, %s::text) > 0.3
        ORDER BY similarity({search_fields[0]}::text, %s::text) DESC
        LIMIT 10;
    """
    params = [fuzzy_term, fuzzy_term]
else:
    final_where = " OR ".join(where_clauses) if logic == "OR" else " AND ".join(where_clauses)
    query = f"""
        SELECT {select_fields}
        FROM {table}
        WHERE {final_where}
        ORDER BY {id_field}
        LIMIT 10;
    """

print("Running query:\n", query)
cur.execute(query, params)

# Show results
results = cur.fetchall()
for r in results:
    print(f"{id_field.upper()} {r[0]}: {r[1]}")
    if r[2]:
        print(f"  → {r[2]}\n")

cur.close()
conn.close()