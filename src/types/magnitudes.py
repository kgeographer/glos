import numpy as np
import psycopg2
import json

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "database": "staging",
    "user": "postgres",
    "port": 5435
}

# Connect to the database
conn = psycopg2.connect(**DB_PARAMS)
cursor = conn.cursor()

# Fetch embeddings from the folklore schema's motif_embeddings table
cursor.execute("SELECT motif_id, embedding FROM folklore.motif_embeddings LIMIT 10")
rows = cursor.fetchall()

# Calculate norms using NumPy
for row in rows:
    motif_id, embedding_str = row
    # Parse the string embedding back into a list of floats
    embedding_array = np.array(json.loads(embedding_str))  # Convert JSON-like string to list of floats
    # Calculate Euclidean norm (magnitude)
    norm = np.linalg.norm(embedding_array)
    print(f"Motif ID: {motif_id}, Norm: {norm}")

# Close the connection
cursor.close()
conn.close()
