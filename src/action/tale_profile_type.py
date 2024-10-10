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

# Define the tale as a fixed string for now
prompt = """
Long ago, the Sun and the Moon were married to each other. The Sun would sail across the sky, 
blazing in all his glory, till he would reach the end of the world where Sky and Earth meet. 
At night, when his light would be hidden, his wife the Moon would sail gently across the sky, 
till the Sun rose again in the morning. The Sun and the Moon had many children. The boys were 
like their father the Sun, already blazing with light even though they were little. The girls were 
like their mother the Moon, glowing softly. Now the young suns greatly admired their father the Sun, 
and wanted to be like him. They too wanted to sail across the sky down to the end of the world where 
Sky and Earth met. But their father would not take them with him. So one day the young suns gathered 
together in a body, and began following their father the Sun as he started off on his journey across the sky. 
'Go back!' ordered the Sun. 'You may not follow me! There is place for only one Sun in the sky!' 
But the young suns replied, 'We want to be like you! We too want to sail across the sky all day!' 
The Sun again ordered his sons to return home to their mother the Moon, but the boys would not listen. 
They insisted on following him. At this, the Sun grew angry, and also afraid – he felt that the brilliance 
of his sons might outshine him very soon. So, in anger and fear, he turned upon his sons and tried to kill them. 
The young suns ran in fright and took refuge with their grandmother Yemaja, the goddess of brooks and streams. 
Yemaja, to save her grandchildren from the wrath of the Sun, turned them into fish and hid them in 
the sea and the rivers and streams of the earth. But the daughters of the Sun and the Moon had remained 
quietly at home with their mother. They are still with her, and we can see them, following the Moon at night, 
when the Sun's fierce light is hidden. And so there came to be fish in the sea and the rivers and streams; 
and also stars in the sky.
"""


# Function to get the embedding for a prompt
def get_embedding(text):
  response = client.embeddings.create(
    input=text,
    model=openai_model
  )
  return response.data[0].embedding


# Generate the embedding for the tale
prompt_embedding = get_embedding(prompt)

# Connect to the Postgres database
conn = psycopg2.connect(
  dbname="staging",
  user="postgres",
  host="localhost",
  port="5435"
)


# Query the vector database to find the closest tale types
def find_closest_types(embedding, top_n=10):
  with conn.cursor() as cur:
    cur.execute("""
          SELECT type_id, text, embedding <-> %s::vector AS distance
          FROM folklore.type_embeddings_3sm
          ORDER BY distance
          LIMIT %s;
      """, (embedding, top_n))

    return cur.fetchall()


# Retrieve the closest tale types
closest_types = find_closest_types(prompt_embedding)

# Output the results
for row in closest_types:
  type_id, text, distance = row
  print(f"Type ID: {type_id}\nType Text: {text}\nDistance: {distance}\n")

# Close the connection
conn.close()
