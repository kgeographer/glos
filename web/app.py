from flask import Flask, request, jsonify, render_template
import openai
import psycopg2
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables and set OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
openai_model = 'text-embedding-3-small'

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

@app.route('/neighbors', methods=['POST'])
def neighbors():
    data = request.json
    input_text = data['text']
    query_type = data['queryType']

    table = 'motif_embeddings_3sm' if query_type == 'motif' else 'type_embeddings_3sm'
    id_col = 'motif_id' if query_type == 'motif' else 'type_id'
    text_col = 'motif_text' if query_type == 'motif' else 'text'

    embedding = get_embedding(input_text)

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

    # conn = psycopg2.connect(
    #     dbname="staging",
    #     user="postgres",
    #     host="localhost",
    #     port="5435"
    # )

    closest_neighbors = find_closest_neighbors(conn, embedding, table, id_col, text_col)
    conn.close()

    return jsonify(closest_neighbors)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explore')
def explore():
    return render_template('explore.html')

@app.route('/mapping')
def mapping():
    return render_template('mapping.html')

if __name__ == '__main__':
    app.run(debug=True)
