import os
import asyncio
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from openai import AsyncOpenAI
import time

# Load environment variables
load_dotenv()

# Set up AsyncOpenAI client
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Database connection parameters
DB_PARAMS = {
  "host": "localhost",
  "database": "staging",
  "user": "postgres",
  "port": 5435
}

openai_model = 'text-embedding-3-small'
BATCH_SIZE = 100  # Adjust based on your API rate limits and performance


async def get_embeddings(texts):
  try:
    response = await client.embeddings.create(input=texts, model=openai_model)
    return [embedding.embedding for embedding in response.data]
  except Exception as e:
    print(f"Error in get_embeddings: {e}")
    return []


async def process_batch(batch):
  motif_ids, texts = zip(*batch)
  embeddings = await get_embeddings(texts)
  return list(zip(motif_ids, texts, embeddings))


async def process_embeddings(batch_size=BATCH_SIZE, limit=None):
  conn = psycopg2.connect(**DB_PARAMS)
  cursor = conn.cursor()

  try:
    # Fetch unprocessed rows
    query = """
            SELECT motif_id, motif_text_with_references 
            FROM folklore.embed_text_motifs
            WHERE motif_id NOT IN (SELECT motif_id FROM folklore.motif_embeddings_3sm)
        """
    if limit:
      query += f" LIMIT {limit}"

    cursor.execute(query)
    rows = cursor.fetchall()

    print(f"Total rows to process: {len(rows)}")

    for i in range(0, len(rows), batch_size):
      batch = rows[i:i + batch_size]
      results = await process_batch(batch)

      # Insert results into the database
      insert_query = """
                INSERT INTO folklore.motif_embeddings_3sm (motif_id, motif_text, embedding)
                VALUES %s
            """
      execute_values(cursor, insert_query, results)
      conn.commit()

      print(f"Processed batch {i // batch_size + 1}, total rows: {i + len(batch)}")

    print("Processing complete.")

  except Exception as e:
    print(f"An error occurred: {e}")
  finally:
    cursor.close()
    conn.close()


# Interactive function to run the script
def run_interactive():
  print("Interactive OpenAI Embedding Script")
  print("-----------------------------------")

  while True:
    choice = input("Enter '1' to process all rows, '2' to process a limited number, or 'q' to quit: ")

    if choice == 'q':
      break
    elif choice in ['1', '2']:
      batch_size = int(input("Enter batch size (default 100): ") or 100)

      if choice == '2':
        limit = int(input("Enter the number of rows to process: "))
      else:
        limit = None

      start_time = time.time()
      asyncio.run(process_embeddings(batch_size, limit))
      end_time = time.time()

      print(f"Total processing time: {end_time - start_time:.2f} seconds")
    else:
      print("Invalid choice. Please try again.")


# This allows you to run the script interactively in your IDE
if __name__ == "__main__":
  run_interactive()
