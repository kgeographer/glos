
import os
import asyncio
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from openai import AsyncOpenAI
import time

# set True to run against all motifs
TEST_MODE = False

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "database": "staging",
    "user": "postgres",
    "port": 5435
}

embedding_model = 'text-embedding-3-small'
llm_model = 'gpt-4-turbo'
BATCH_SIZE = 20  # Limit for LLM due to cost/time

async def expand_motifs(texts):
    prompts = [
        f"Expand the following folkloric motif into 2–3 sentences for semantic interpretation:\nMotif: \"{text}\"" 
        for text in texts
    ]
    try:
        responses = await asyncio.gather(*[
            client.chat.completions.create(
                model=llm_model,
                messages=[{"role": "user", "content": prompt}]
            ) for prompt in prompts
        ])
        return [r.choices[0].message.content.strip() for r in responses]
    except Exception as e:
        print(f"Error in expand_motifs: {e}")
        return ["" for _ in texts]

async def get_embeddings(texts):
    try:
        response = await client.embeddings.create(input=texts, model=embedding_model)
        return [embedding.embedding for embedding in response.data]
    except Exception as e:
        print(f"Error in get_embeddings: {e}")
        return [[] for _ in texts]

async def process_batch(batch):
    motif_ids, motif_texts = zip(*batch)
    expanded_texts = await expand_motifs(motif_texts)
    embeddings = await get_embeddings(expanded_texts)
    return list(zip(motif_ids, motif_texts, expanded_texts, embeddings))

async def main():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS folklore.motif_extended_3sm (
            motif_id TEXT PRIMARY KEY,
            motif_text TEXT,
            expanded_text TEXT,
            embedding VECTOR(1536)
        )
    """)
    conn.commit()

    query = "SELECT motif_id, text FROM folklore.motif_text WHERE motif_id LIKE 'A%' AND motif_id NOT IN (SELECT motif_id FROM motif_extended_3sm) ORDER BY motif_id"
    if TEST_MODE:
        query += " LIMIT 20"
    cur.execute(query)
    # cur.execute("SELECT motif_id, text FROM motif_text WHERE motif_id NOT IN (SELECT motif_id FROM motif_extended_3sm)")
    all_rows = cur.fetchall()
    total = len(all_rows)
    print(f"Total motifs to process: {total}")

    for i in range(0, total, BATCH_SIZE):
        batch = all_rows[i:i + BATCH_SIZE]
        results = await process_batch(batch)

        insert_query = '''
            INSERT INTO folklore.motif_extended_3sm (motif_id, motif_text, expanded_text, embedding)
            VALUES %s
            ON CONFLICT (motif_id) DO NOTHING
        '''
        execute_values(cur, insert_query, results)
        conn.commit()
        print(f"Inserted batch {i//BATCH_SIZE + 1} of {((total - 1)//BATCH_SIZE) + 1}")

    cur.close()
    conn.close()

if __name__ == '__main__':
    asyncio.run(main())
