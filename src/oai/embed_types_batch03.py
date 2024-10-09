import os
import asyncio
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from openai import AsyncOpenAI
import tiktoken
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

BATCH_SIZE = 300
MAX_TOKENS = 8191  # Token limit for openai_model

# Function to estimate token count using tiktoken
def count_tokens(text, model=openai_model):
  encoding = tiktoken.encoding_for_model(model)
  return len(encoding.encode(text))


# Clean the text (remove problematic characters or excessive whitespace)
def clean_text(text):
  if text is None:
    return ""
  return text.replace("\n", " ").replace("\r", " ").strip()


# Batch function: Attempts to process a full batch
async def get_embeddings_batch(type_ids, texts):
  valid_texts = []
  valid_type_ids = []

  for type_id, text in zip(type_ids, texts):
    cleaned_text = clean_text(text)
    token_count = count_tokens(cleaned_text)

    if token_count > MAX_TOKENS:
      print(f"Text too long, skipping type_id {type_id}: {cleaned_text[:50]}... ({token_count} tokens)")
      continue  # Skip texts that are too long

    valid_texts.append(cleaned_text)
    valid_type_ids.append(type_id)

  if not valid_texts:
    return []

  try:
    response = await client.embeddings.create(input=valid_texts, model=openai_model)

    # Log the response for debugging
    print(f"Full batch response: {response}")

    if response.data and isinstance(response.data, list):
      embeddings = [item.embedding for item in response.data]  # Extract embeddings for all items
      return list(zip(valid_type_ids, embeddings))  # Return type_id and embeddings as tuples
    else:
      print(f"Unexpected response structure: {response}")
      return []

  except Exception as e:
    print(f"Error in get_embeddings_batch: {e}")
    return []


# Individual processing fallback: For rows that fail in batch mode
async def get_embeddings_individual(type_id, text):
  try:
    cleaned_text = clean_text(text)
    token_count = count_tokens(cleaned_text)

    if token_count > MAX_TOKENS:
      print(f"Text too long, skipping type_id {type_id}: {cleaned_text[:50]}... ({token_count} tokens)")
      return None

    # Send individual request
    response = await client.embeddings.create(input=[cleaned_text], model=openai_model)

    if response.data and isinstance(response.data, list):
      return response.data[0].embedding  # Extract the single embedding
    else:
      print(f"Unexpected response structure for type_id {type_id}: {response}")
      return None

  except Exception as e:
    print(f"Error in get_embeddings_individual for type_id {type_id}:\nText: {cleaned_text}\nError: {e}")
    return None


# Process a batch, with fallback to individual rows if needed
async def process_batch(batch):
  type_ids, labels, texts = zip(*batch)

  # Try batch processing first
  embeddings_batch = await get_embeddings_batch(type_ids, texts)

  if not embeddings_batch:
    # If the batch fails, retry each row individually
    print(f"Retrying batch individually due to failure.")
    results = []
    for type_id, label, text in batch:
      embedding = await get_embeddings_individual(type_id, text)
      if embedding:
        results.append((type_id, label, text, embedding))
    return results
  else:
    # Return the embeddings from the successful batch
    return [(type_id, label, text, embedding) for (type_id, embedding), label, text in
            zip(embeddings_batch, labels, texts)]


# Main loop for processing all rows
async def process_embeddings(batch_size=BATCH_SIZE, limit=None):
  conn = psycopg2.connect(**DB_PARAMS)
  cursor = conn.cursor()

  try:
    # Fetch unprocessed rows
    query = """
                SELECT type_id, label, text 
                FROM folklore.embed_text_types
                WHERE type_id NOT IN (SELECT type_id FROM folklore.type_embeddings_3sm)
            """
    if limit:
      query += f" LIMIT {limit}"

    cursor.execute(query)
    rows = cursor.fetchall()

    print(f"Total rows to process: {len(rows)}")

    for i in range(0, len(rows), batch_size):
      batch = rows[i:i + batch_size]
      results = await process_batch(batch)

      if results:
        # Insert results into the database
        insert_query = """
                    INSERT INTO folklore.type_embeddings_3sm (type_id, label, text, embedding)
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
