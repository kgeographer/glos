import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

# Load DB credentials from .env
load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),  # include this if your .env has it
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT')
)

# Queries to run
queries = {
    "total_tale_types": "SELECT COUNT(DISTINCT type_id) FROM folklore.type_ref;",
    "ref_term_counts": """
        SELECT ref_term, COUNT(DISTINCT type_id) AS num_tales
        FROM folklore.type_ref
        GROUP BY ref_term
        ORDER BY num_tales DESC;
    """,
    "type_culture_counts": """
        SELECT type_id, COUNT(ref_term) AS num_cultures
        FROM folklore.type_ref
        GROUP BY type_id
        ORDER BY num_cultures DESC;
    """
}

# Execute queries and store results
def run_query(query, conn):
    with conn.cursor() as cur:
        cur.execute(query)
        colnames = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=colnames)

df_total = run_query(queries["total_tale_types"], conn)
df_ref_term = run_query(queries["ref_term_counts"], conn)
df_type_culture = run_query(queries["type_culture_counts"], conn)

# Output results
print("\n📌 Total distinct tale types:", df_total.iloc[0, 0])
print("\n📊 Top 10 ref_terms by tale type count:")
print(df_ref_term.head(10))

print("\n🌐 Top 10 tale types by number of cultures:")
print(df_type_culture.head(10))

# Optional: Save results to CSV
df_ref_term.to_csv("src/ref_terms/output/ref_term_counts.csv", index=False)
df_type_culture.to_csv("src/ref_terms/output/type_culture_counts.csv", index=False)
