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

## for EXPLORE
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

    # table = 'motif_embeddings_3sm' if query_type == 'motif' else 'type_embeddings_3sm'
    # add option to access the extended motif table holding only 'A' motifs
    if query_type == 'motif':
        table = 'motif_embeddings_3sm'
    elif query_type == 'type':
        table = 'type_embeddings_3sm'
    elif query_type == 'myth_motif':
        table = 'motif_extended_3sm'

    id_col = 'motif_id' if query_type in ['motif', 'myth_motif'] else 'type_id'
    text_col = 'motif_text' if query_type in ['motif', 'myth_motif'] else 'text'

    embedding = get_embedding(input_text)

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

    closest_neighbors = find_closest_neighbors(conn, embedding, table, id_col, text_col)
    conn.close()

    return jsonify(closest_neighbors)
## end of EXPLORE

## for ATU-TMI
@app.route('/atu_tmi')
def atu_tmi():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    cur.execute("SELECT type_id, label FROM folklore.type_embeddings_3sm ORDER BY type_id;")
    tale_types = cur.fetchall()
    conn.close()
    return render_template('atu_tmi.html', tale_types=tale_types)


@app.route('/get_motifs_for_type/<type_id>')
def get_motifs_for_type(type_id):
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT tm.motif_id, mt.text,
               COALESCE(
                   STRING_AGG(DISTINCT mr.ref_term, ', ' ORDER BY mr.ref_term), 
                   ''
               ) as ref_terms
        FROM folklore.type_motif tm
        JOIN folklore.motif_text mt ON tm.motif_id = mt.motif_id
        LEFT JOIN folklore.motif_ref mr ON tm.motif_id = mr.motif_id
        WHERE tm.type_id = %s
        GROUP BY tm.motif_id, mt.text
        ORDER BY tm.motif_id;
    """, (type_id,))

    motifs = []
    for row in cur.fetchall():
        motifs.append({
            'motif_id': row[0],
            'text': row[1],
            'ref_terms': row[2] if row[2] else ''
        })

    cur.close()
    conn.close()
    return jsonify(motifs)


@app.route('/get_types_for_motif/<motif_id>')
def get_types_for_motif(motif_id):
    """Get tale types that contain a specific motif (TMI→ATU lookup)"""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # Get tale types containing this motif with their details
    cur.execute("""
        SELECT tm.type_id, te.label,
               COALESCE(
                   STRING_AGG(DISTINCT tr.ref_term, ', ' ORDER BY tr.ref_term), 
                   ''
               ) as ref_terms
        FROM folklore.type_motif tm
        JOIN folklore.type_embeddings_3sm te ON tm.type_id = te.type_id
        LEFT JOIN folklore.type_ref tr ON tm.type_id = tr.type_id
        WHERE tm.motif_id = %s
        GROUP BY tm.type_id, te.label
        ORDER BY tm.type_id;
    """, (motif_id,))

    types = []
    for row in cur.fetchall():
        types.append({
            'type_id': row[0],
            'label': row[1],
            'ref_terms': row[2] if row[2] else ''
        })

    cur.close()
    conn.close()
    return jsonify(types)


@app.route('/get_atu_hierarchy')
def get_atu_hierarchy():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # Get the full hierarchy
    cur.execute("""
        SELECT id, type_range, parent, label
        FROM folklore.atu_type_groups
        ORDER BY id;
    """)

    hierarchy = cur.fetchall()
    cur.close()
    conn.close()

    # Convert to nested structure
    def build_tree(parent_range=None):
        children = []
        for row in hierarchy:
            if row[2] == parent_range:  # parent field matches
                node = {
                    'id': row[0],
                    'type_range': row[1],
                    'parent': row[2],
                    'label': row[3],
                    'children': build_tree(row[1])  # recursive call with current type_range as parent
                }
                children.append(node)
        return children

    tree = build_tree('ATU')  # Start with top-level ATU categories
    return jsonify(tree)


@app.route('/get_motif_hierarchy')
def get_motif_hierarchy():
    """Get TMI motif categories for hierarchical display"""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # Get the major motif categories (A, B, C, etc.)
    cur.execute("""
        SELECT t.category, 
               t.total_count,
               COALESCE(c.connected_count, 0) as connected_count
        FROM (
            SELECT DISTINCT LEFT(motif_id, 1) as category,
                   COUNT(*) as total_count
            FROM folklore.motif_text
            WHERE motif_id ~ '^[A-Z]'
            GROUP BY category
        ) t
        LEFT JOIN (
            SELECT DISTINCT LEFT(mt.motif_id, 1) as category,
                   COUNT(DISTINCT mt.motif_id) as connected_count
            FROM folklore.motif_text mt
            JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
            WHERE mt.motif_id ~ '^[A-Z]'
            GROUP BY category
        ) c ON t.category = c.category
        ORDER BY t.category;
    """)

    categories = []
    for row in cur.fetchall():
        # Get category description from synopsis table if available
        cur.execute("""
            SELECT label FROM folklore.synopsis 
            WHERE motif_id = %s
            LIMIT 1;
        """, (row[0] + '.',))

        desc_row = cur.fetchone()
        description = desc_row[0] if desc_row else f"Category {row[0]}"

        categories.append({
            'category': row[0],
            'description': description,
            'total_count': row[1],
            'connected_count': row[2]
        })
    cur.close()
    conn.close()
    return jsonify(categories)


@app.route('/get_types_in_range/<type_range>')
def get_types_in_range(type_range):
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # Parse the range (e.g., "1155–1169")
    if '–' in type_range:
        start, end = type_range.split('–')
        start = int(start.strip())
        end = int(end.strip())

        # Match type_ids where the numeric prefix falls within the range
        # This handles cases like: 1166, 1166*, 1168A, etc.
        cur.execute("""
            SELECT type_id, label
            FROM folklore.type_embeddings_3sm
            WHERE type_id ~ '^[0-9]+'  -- Must start with digits
            AND CAST(REGEXP_REPLACE(type_id, '^([0-9]+).*', '\\1') AS INTEGER) BETWEEN %s AND %s
            ORDER BY 
                CAST(REGEXP_REPLACE(type_id, '^([0-9]+).*', '\\1') AS INTEGER),
                type_id;
        """, (start, end))
    else:
        # Handle exact matches or single numbers
        cur.execute("""
            SELECT type_id, label
            FROM folklore.type_embeddings_3sm
            WHERE type_id = %s OR type_id ~ ('^' || %s || '[^0-9]')
            ORDER BY type_id;
        """, (type_range, type_range))

    types = [{'type_id': row[0], 'label': row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(types)


@app.route('/get_motifs_in_category/<category>')
def get_motifs_in_category(category):
    """Get motifs within a specific category (e.g., 'A' for mythological motifs)"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # Get motifs in category with pagination (only those with associated tale types)
    # Note: category is expected to be a single letter like 'A', 'B', etc.
    cur.execute("""
        SELECT mt.motif_id, mt.text,
               COUNT(tm.type_id) as type_count
        FROM folklore.motif_text mt
        LEFT JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
        WHERE mt.motif_id LIKE %s
        GROUP BY mt.motif_id, mt.text
        HAVING COUNT(tm.type_id) > 0
        ORDER BY mt.motif_id
        LIMIT %s OFFSET %s;
    """, (f"{category}%", limit, offset))

    motifs = []
    for row in cur.fetchall():
        motifs.append({
            'motif_id': row[0],
            'text': row[1],
            'type_count': row[2]
        })

    # Also get total count for pagination
    cur.execute("""
        SELECT COUNT(*) FROM folklore.motif_text 
        WHERE motif_id LIKE %s;
    """, (f"{category}%",))

    total_count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return jsonify({
        'motifs': motifs,
        'total': total_count,
        'limit': limit,
        'offset': offset
    })


@app.route('/get_type_details/<type_id>')
def get_type_details(type_id):
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # Get type label, text, and cultural references
    cur.execute("""
        SELECT te.label, te.text,
               STRING_AGG(DISTINCT tr.ref_term, ', ' ORDER BY tr.ref_term) as ref_terms
        FROM folklore.type_embeddings_3sm te
        LEFT JOIN folklore.type_ref tr ON te.type_id = tr.type_id
        WHERE te.type_id = %s
        GROUP BY te.label, te.text;
    """, (type_id,))

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        ref_terms_list = result[2].split(', ') if result[2] else []
        return jsonify({
            'label': result[0] or '',
            'text': result[1] or '',
            'ref_terms': ref_terms_list
        })
    return jsonify({'label': '', 'text': '', 'ref_terms': []})


@app.route('/get_motif_details/<motif_id>')
def get_motif_details(motif_id):
    """Get detailed information about a specific motif"""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # Get motif text and cultural references
    cur.execute("""
        SELECT mt.text,
               STRING_AGG(DISTINCT mr.ref_term, ', ' ORDER BY mr.ref_term) as ref_terms
        FROM folklore.motif_text mt
        LEFT JOIN folklore.motif_ref mr ON mt.motif_id = mr.motif_id
        WHERE mt.motif_id = %s
        GROUP BY mt.text;
    """, (motif_id,))

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        ref_terms_list = result[1].split(', ') if result[1] else []
        return jsonify({
            'text': result[0] or '',
            'ref_terms': ref_terms_list
        })
    return jsonify({'text': '', 'ref_terms': []})


@app.route('/search_motifs')
def search_motifs():
    """Search for motifs by ID or text content"""
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 20))

    if not query:
        return jsonify([])

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # Search by motif ID (exact and prefix match) and text content
    cur.execute("""
        SELECT mt.motif_id, mt.text,
               COUNT(tm.type_id) as type_count,
               CASE 
                   WHEN mt.motif_id = %s THEN 1
                   WHEN mt.motif_id ILIKE %s THEN 2
                   ELSE 3
               END as relevance
        FROM folklore.motif_text mt
        LEFT JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
        WHERE mt.motif_id ILIKE %s OR mt.text ILIKE %s
        GROUP BY mt.motif_id, mt.text
        HAVING COUNT(tm.type_id) > 0
        ORDER BY relevance, mt.motif_id
        LIMIT %s;
    """, (query, f"{query}%", f"%{query}%", f"%{query}%", limit))

    results = []
    for row in cur.fetchall():
        results.append({
            'motif_id': row[0],
            'text': row[1],
            'type_count': row[2],  # Make sure this line exists
            'relevance': row[3]
        })

    # results = []
    # for row in cur.fetchall():
    #     results.append({
    #         'motif_id': row[0],
    #         'text': row[1],
    #         'relevance': row[2]
    #     })

    cur.close()
    conn.close()
    return jsonify(results)


@app.route('/search_types')
def search_types():
    """Search for tale types by ID or label"""
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 20))

    if not query:
        return jsonify([])

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # Search by type ID and label
    cur.execute("""
        SELECT type_id, label,
               CASE 
                   WHEN type_id = %s THEN 1
                   WHEN type_id ILIKE %s THEN 2
                   ELSE 3
               END as relevance
        FROM folklore.type_embeddings_3sm
        WHERE type_id ILIKE %s OR label ILIKE %s
        ORDER BY relevance, 
                 CASE WHEN type_id ~ '^[0-9]+' 
                      THEN CAST(REGEXP_REPLACE(type_id, '^([0-9]+).*', '\\1') AS INTEGER)
                      ELSE 9999
                 END,
                 type_id
        LIMIT %s;
    """, (query, f"{query}%", f"%{query}%", f"%{query}%", limit))

    results = []
    for row in cur.fetchall():
        results.append({
            'type_id': row[0],
            'label': row[1],
            'relevance': row[2]
        })

    cur.close()
    conn.close()
    return jsonify(results)


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
