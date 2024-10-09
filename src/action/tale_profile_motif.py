import openai
import psycopg2
import os
from dotenv import load_dotenv

from src.oai.embed_motifs_batch import openai_model

# Load OpenAI API key from .env file
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Create an OpenAI client instance
client = openai.Client()
openai_model = 'text-embedding-3-small'

# Define the tale as a fixed string for now
# 1003 (linked to motif K1411.)
short_tale = """
Old person as helper on quest.
"""

# Function to get the embedding for the tale
def get_embedding(text):
  response = client.embeddings.create(
    input=text,
    model=openai_model
  )
  return response.data[0].embedding  # Access the response in the new API format


# Generate the embedding for the tale
tale_embedding = get_embedding(short_tale)

# Connect to the Postgres database
conn = psycopg2.connect(
  dbname="staging",
  user="postgres",
  host="localhost",
  port="5435"
)


# Query the vector database to find the closest motifs
def find_closest_motifs(embedding, top_n=20):
  with conn.cursor() as cur:
    cur.execute("""
          SELECT motif_id, motif_text, embedding <-> %s::vector AS distance
          FROM folklore.motif_embeddings_3sm
          ORDER BY distance
          LIMIT %s;
      """, (embedding, top_n))

    return cur.fetchall()


# Retrieve the closest motifs
closest_motifs = find_closest_motifs(tale_embedding)

# Output the results
for row in closest_motifs:
  motif_id, motif_text, distance = row
  print(f"Motif ID: {motif_id}\nMotif Text: {motif_text}\nDistance: {distance}\n")

# Close the connection
conn.close()
