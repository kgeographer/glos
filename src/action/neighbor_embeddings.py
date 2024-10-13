import openai
import psycopg2
import os
from dotenv import load_dotenv

# Load OpenAI API key from .env file
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Create an OpenAI client instance
client = openai.Client()
openai_model = 'text-embedding-3-small'

# Function to get the embedding for a prompt
def get_embedding(text):
  response = client.embeddings.create(
    input=text,
    model=openai_model
  )
  return response.data[0].embedding


# Function to find nearest neighbors in the specified table
def find_closest_neighbors(conn, embedding, table, id_col, text_col, top_n=10):
  with conn.cursor() as cur:
    query = f"""
            SELECT {id_col}, {text_col}, embedding <-> %s::vector AS distance
            FROM folklore.{table}
            ORDER BY distance
            LIMIT %s;
        """
    cur.execute(query, (embedding, top_n))
    return cur.fetchall()


# Main function to handle input and process based on parameters
def main():
  # Get input text and table type from the user
  input_text = input("Enter the text for embedding: ")
  table_type = input("Choose table ('motif' or 'type'): ").strip().lower()

  # Determine table and column names based on input
  if table_type == 'motif':
    table = 'motif_embeddings_3sm'
    id_col = 'motif_id'
    text_col = 'motif_text'
  elif table_type == 'type':
    table = 'type_embeddings_3sm'
    id_col = 'type_id'
    text_col = 'text'
  else:
    print("Invalid table type. Choose 'motif' or 'type'.")
    return

  # Generate embedding for the input text
  embedding = get_embedding(input_text)

  # Connect to the Postgres database
  conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT')
  )

  # conn = psycopg2.connect(
  #   dbname="staging",
  #   user="postgres",
  #   host="localhost",
  #   port="5435"
  # )

  # Find closest neighbors based on the specified table
  closest_neighbors = find_closest_neighbors(conn, embedding, table, id_col, text_col)

  # Output results
  print("\nClosest matches:")
  for row in closest_neighbors:
    row_id, row_text, distance = row
    print(
      f"{id_col.capitalize()}: {row_id}\n{text_col.replace('_', ' ').capitalize()}: {row_text}\nDistance: {distance}\n")

  # Close the connection
  conn.close()


if __name__ == "__main__":
  main()
