import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(
  dbname=os.getenv('DB_NAME'),
  user=os.getenv('DB_USER'),
  host=os.getenv('DB_HOST'),
  port=os.getenv('DB_PORT')
)
cur = conn.cursor()
cur.execute("""
    SELECT type_id, label, text 
    FROM folklore.type_embeddings_3sm 
    WHERE type_id = '1408';
""")
row = cur.fetchone()
print(f"type_id: {row[0]}\nlabel: {row[1]}\ntext: {row[2][:80]}...")  # truncate for sanity

cur.close()
conn.close()

print("Connecting with:")
print("DB_NAME:", os.getenv("DB_NAME"))
print("DB_HOST:", os.getenv("DB_HOST"))
print("DB_PORT:", os.getenv("DB_PORT"))