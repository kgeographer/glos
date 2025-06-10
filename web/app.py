from flask import Flask, request, jsonify, render_template, render_template_string
import openai
import psycopg2
import os
from dotenv import load_dotenv
import markdown

app = Flask(__name__)

# Load environment variables and set OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
openai_model = 'text-embedding-3-small'

# Create an OpenAI client instance
client = openai.Client()
openai_model = 'text-embedding-3-small'


@app.route("/about")
def about():
    with open("templates/about.md", "r") as f:
        content = f.read()
    html = markdown.markdown(content)

    full_page = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>About GLOS</title>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" crossorigin="anonymous"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" crossorigin="anonymous">
        <link href="/static/css/styles.css" rel="stylesheet">
    </head>
    <body>
        <div class="container">
            <nav class="navbar navbar-expand-lg navbar-light bg-light">
                <div class="container-fluid">
                    <a class="navbar-brand" href="/">
                        <img src="/static/images/glos_wordmark.jpg" alt="GLOS Logo" height="32">
                    </a>
                    <div class="collapse navbar-collapse justify-content-end">
                        <ul class="navbar-nav">
                            <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
                            <li class="nav-item"><a class="nav-link" href="/explore">Concept Matcher</a></li>
                            <li class="nav-item"><a class="nav-link" href="/atu_tmi_v2">ATU/TMI</a></li>
                            <li class="nav-item active"><a class="nav-link" href="/about">About</a></li>
                            <li class="nav-item"><a class="nav-link disabled-link" href="/mapping">Mapping</a></li>
                        </ul>
                    </div>
                </div>
            </nav>

            <div class="mt-4">
                {html}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(full_page)


# Function to get the embedding for a prompt
def get_embedding(text):
  response = client.embeddings.create(
    input=text,
    model=openai_model
  )
  return response.data[0].embedding

def find_closest_neighbors(conn, embedding, table, id_col, text_col, top_n=10, offset=0):
    with conn.cursor() as cur:
        query = f"""
            SELECT {id_col}, {text_col}, embedding <-> %s::vector AS distance
            FROM folklore.{table}
            ORDER BY distance
            LIMIT %s OFFSET %s;
        """
        cur.execute(query, (embedding, top_n, offset))
        return cur.fetchall()

@app.route('/neighbors', methods=['POST'])
def neighbors():
    data = request.json
    input_text = data['text']
    query_type = data['queryType']

    offset = int(data.get('offset', 0))
    limit = int(data.get('limit', 10))

    if query_type == 'motif':
        table = 'motif_embeddings_3sm'
        id_col = 'motif_id'
        text_col = 'motif_text'
        ref_table = 'motif_ref'
    elif query_type == 'type':
        table = 'type_embeddings_3sm'
        id_col = 'type_id'
        text_col = 'label'
        ref_table = 'type_ref'
    elif query_type == 'myth_motif':
        table = 'motif_extended_3sm'
        id_col = 'motif_id'
        text_col = 'motif_text'
        ref_table = 'motif_ref'
    else:
        return jsonify({'error': 'Invalid query type'}), 400

    embedding = get_embedding(input_text)

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

    # Step 1: Get neighbors from the embeddings table
    # Step 1: Get neighbors from the embeddings table
    with conn.cursor() as cur:
        if query_type == 'type':
            query = f"""
                SELECT type_id, label, text, embedding <-> %s::vector AS distance
                FROM folklore.type_embeddings_3sm
                ORDER BY distance
                LIMIT %s OFFSET %s;
            """
            cur.execute(query, (embedding, limit, offset))
            raw_results = cur.fetchall()
        else:
            query = f"""
                SELECT {id_col}, {text_col}, embedding <-> %s::vector AS distance
                FROM folklore.{table}
                ORDER BY distance
                LIMIT %s OFFSET %s;
            """
            cur.execute(query, (embedding, limit, offset))
            raw_results = cur.fetchall()

    ids = [r[0] for r in raw_results]

    # Step 2: Get ref_terms from motif_ref or type_ref
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT {id_col}, array_agg(ref_term ORDER BY ref_term) AS ref_terms
            FROM folklore.{ref_table}
            WHERE {id_col} = ANY(%s)
            GROUP BY {id_col}
        """, (ids,))
        ref_term_rows = cur.fetchall()

    ref_term_lookup = {row[0]: row[1] for row in ref_term_rows}

    # Step 3: Assemble final output
    enriched_results = []
    for row in raw_results:
        if query_type == 'type':
            item_id, label, text, distance = row
            enriched_results.append({
                'type_id': item_id,
                'label': label,
                'text': text,
                'ref_terms': ref_term_lookup.get(item_id, []),
                'distance': distance
            })
        else:
            item_id, text, distance = row
            enriched_results.append({
                id_col: item_id,
                'text': text,
                'ref_terms': ref_term_lookup.get(item_id, []),
                'distance': distance
            })

    conn.close()
    return jsonify(enriched_results)

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

## New route for ATU-TMI v2
@app.route('/atu_tmi_v2')
def atu_tmi_v2():
    # New implementation here
    return render_template('atu_tmi_v2.html')

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
    motif_rows = cur.fetchall()
    for row in motif_rows:
        motifs.append({
            'motif_id': row[0],
            'text': row[1],
            'ref_terms': row[2] if row[2] else ''
        })

    # For each motif, compute how many tale types it is associated with
    for motif in motifs:
        cur.execute("""
            SELECT COUNT(DISTINCT type_id)
            FROM folklore.type_motif
            WHERE motif_id = %s
        """, (motif['motif_id'],))
        motif['tale_type_count'] = cur.fetchone()[0]
        print(f"DEBUG: Motif {motif['motif_id']} has {motif['tale_type_count']} tale types")

        # Add related tale types (excluding the current one)
        cur.execute("""
            SELECT DISTINCT type_id
            FROM folklore.type_motif
            WHERE motif_id = %s AND type_id != %s
        """, (motif['motif_id'], type_id))
        related_types_raw = cur.fetchall()
        motif['related_types'] = [str(row[0]) for row in related_types_raw]

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


@app.route('/get_tmi_hierarchy')
def get_tmi_hierarchy():
    """Build hierarchical TMI structure"""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT s.motif_id, s.label,
                   COUNT(DISTINCT tm.motif_id) as connected_count
            FROM folklore.synopsis s
            LEFT JOIN folklore.motif_text mt ON mt.motif_id LIKE REPLACE(s.motif_id, '-', '%') || '%'
            LEFT JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
            WHERE s.motif_id LIKE '%-%'  -- All categories, not just A
            GROUP BY s.motif_id, s.label
            HAVING COUNT(DISTINCT tm.motif_id) > 0
            ORDER BY 
                LEFT(s.motif_id, 1),  -- Sort by category letter first
                CAST(REGEXP_REPLACE(SPLIT_PART(s.motif_id, '-', 1), '[A-Z]', '', 'g') AS INTEGER),
                CAST(REGEXP_REPLACE(SPLIT_PART(s.motif_id, '-', 2), '[A-Z]', '', 'g') AS INTEGER);
        """)

        ranges = cur.fetchall()

        # Build hierarchy by checking which ranges contain others
        def range_contains(parent_range, child_range):
            # Extract numbers from ranges like "A100-A499" -> (100, 499)
            def extract_numbers(range_str):
                parts = range_str.split('-')
                start = int(''.join(filter(str.isdigit, parts[0])))
                end = int(''.join(filter(str.isdigit, parts[1])))
                return start, end

            parent_start, parent_end = extract_numbers(parent_range)
            child_start, child_end = extract_numbers(child_range)

            return (parent_start <= child_start and
                    parent_end >= child_end and
                    parent_range != child_range)

        # Build hierarchy
        hierarchy = []
        used_ranges = set()

        for parent_id, parent_label in ranges:
            if parent_id in used_ranges:
                continue

            # Find children for this parent
            children = []
            for child_id, child_label in ranges:
                if child_id != parent_id and range_contains(parent_id, child_id):
                    children.append({
                        'motif_id': child_id,
                        'label': child_label,
                        'children': []
                    })
                    used_ranges.add(child_id)

            # Only add as top-level if it has children or no parent
            has_parent = any(range_contains(other_id, parent_id) for other_id, _ in ranges if other_id != parent_id)

            if not has_parent:
                hierarchy.append({
                    'motif_id': parent_id,
                    'label': parent_label,
                    'children': children
                })

        # Wrap in main A category
        result = [{
            'motif_id': 'A',
            'label': 'A: MYTHOLOGICAL MOTIFS',
            'children': hierarchy
        }]

        cur.close()
        conn.close()
        return jsonify(result)

    except Exception as e:
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/get_tmi_categories')
def get_tmi_categories():
    """Get top-level TMI categories (A, B, C, etc.) with connected motif counts"""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        print("DEBUG: Getting all TMI categories with connected motifs")

        # Get all categories that have any connected motifs
        cur.execute("""
            SELECT LEFT(mt.motif_id, 1) as category,
                   COUNT(DISTINCT tm.motif_id) as connected_count,
                   COUNT(DISTINCT mt.motif_id) as total_count
            FROM folklore.motif_text mt
            LEFT JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
            WHERE LENGTH(LEFT(mt.motif_id, 1)) = 1 
            AND LEFT(mt.motif_id, 1) ~ '^[A-Z]$'
            GROUP BY LEFT(mt.motif_id, 1)
            HAVING COUNT(DISTINCT tm.motif_id) > 0
            ORDER BY LEFT(mt.motif_id, 1);
        """)

        categories = []
        category_descriptions = {
            'A': 'MYTHOLOGICAL MOTIFS',
            'B': 'ANIMALS',
            'C': 'TABU',
            'D': 'MAGIC',
            'E': 'THE DEAD',
            'F': 'MARVELS',
            'G': 'OGRES',
            'H': 'TESTS',
            'J': 'THE WISE AND THE FOOLISH',
            'K': 'DECEPTIONS',
            'L': 'REVERSAL OF FORTUNE',
            'M': 'ORDAINING THE FUTURE',
            'N': 'CHANCE AND FATE',
            'P': 'SOCIETY',
            'Q': 'REWARDS AND PUNISHMENTS',
            'R': 'CAPTIVES AND FUGITIVES',
            'S': 'UNNATURAL CRUELTY',
            'T': 'SEX',
            'U': 'THE NATURE OF LIFE',
            'V': 'RELIGION',
            'W': 'TRAITS OF CHARACTER',
            'X': 'HUMOR',
            'Z': 'MISCELLANEOUS GROUPS'
        }

        for row in cur.fetchall():
            category = row[0]
            categories.append({
                'category': category,
                'description': category_descriptions.get(category, f"Category {category}"),
                'connected_count': row[1],
                'total_count': row[2]
            })

        cur.close()
        conn.close()

        print(f"DEBUG: Found {len(categories)} categories with connected motifs")
        return jsonify(categories)

    except Exception as e:
        print(f"ERROR in get_tmi_categories: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            cur.close()
            conn.close()
        except:
            pass
        return jsonify({"error": str(e)}), 500


## START: USING synopsis_edges and motif_text tables
@app.route('/get_tmi_ranges/<category>')
def get_tmi_ranges(category):
    """Get direct children of a TMI category using the hierarchy table"""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        print(f"DEBUG: Getting direct children for category '{category}'")

        # Get direct children of this category from the hierarchy table
        cur.execute("""
            SELECT mse.motif_child as range_id,
                   s.label,
                   COUNT(DISTINCT tm.motif_id) as connected_count,
                   COUNT(DISTINCT mt.motif_id) as total_count
            FROM folklore.motif_synopsis_edges mse
            JOIN folklore.synopsis s ON mse.motif_child = s.motif_id
            LEFT JOIN folklore.motif_text mt ON mt.motif_id LIKE REPLACE(mse.motif_child, '-', '%') || '%'
            LEFT JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
            WHERE mse.motif_parent = %s
            GROUP BY mse.motif_child, s.label
            ORDER BY mse.motif_child;
        """, (category,))

        ranges = []
        for row in cur.fetchall():
            ranges.append({
                'range_id': row[0],
                'label': row[1],
                'connected_count': row[2],
                'total_count': row[3]
            })

        cur.close()
        conn.close()

        print(f"DEBUG: Found {len(ranges)} direct children for category {category}")
        return jsonify(ranges)

    except Exception as e:
        print(f"ERROR in get_tmi_ranges: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            cur.close()
            conn.close()
        except:
            pass
        return jsonify({"error": str(e)}), 500


## BEGIN NEW HYBRID APPROACH
@app.route('/get_tmi_children/<parent_id>')
def get_tmi_children(parent_id):
    """Get direct children of any TMI node - hybrid approach to fill gaps"""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        print(f"DEBUG TMI_CHILDREN: === Starting for parent_id '{parent_id}' ===")

        # First check if this is a "10s bin" (A0, A10, A20, etc.) that needs algorithmic filling
        is_tens = is_tens_bin(parent_id)
        print(f"DEBUG TMI_CHILDREN: is_tens_bin({parent_id}) = {is_tens}")

        if is_tens:
            print(f"DEBUG TMI_CHILDREN: Using algorithmic approach for 10s bin '{parent_id}'")
            children = get_algorithmic_children(cur, parent_id)
        else:
            print(f"DEBUG TMI_CHILDREN: Using synopsis_edges approach for '{parent_id}'")
            children = get_synopsis_children(cur, parent_id)

        print(f"DEBUG TMI_CHILDREN: Generated {len(children)} children")

        # Debug first few children
        for i, child in enumerate(children[:5]):
            print(
                f"DEBUG TMI_CHILDREN:   [{i}] {child['child_id']}: {child['label'][:50]}... connected={child['connected_count']} leaf={child['is_leaf']}")

        if len(children) > 5:
            print(f"DEBUG TMI_CHILDREN:   ... and {len(children) - 5} more children")

        cur.close()
        conn.close()

        print(f"DEBUG TMI_CHILDREN: === Returning {len(children)} children for {parent_id} ===")
        return jsonify(children)

    except Exception as e:
        print(f"ERROR TMI_CHILDREN: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            cur.close()
            conn.close()
        except:
            pass
        return jsonify({"error": str(e)}), 500


def is_tens_bin(motif_id):
    """Check if this is a '10s bin' like A0, A10, A20, B0, B10, etc."""
    import re
    # Pattern: Single letter followed by number divisible by 10 (A0, A10, A20, A30...)
    pattern = r'^[A-Z]([0-9]+)$'
    match = re.match(pattern, motif_id)
    if match:
        number = int(match.group(1))
        return number % 10 == 0  # True for 0, 10, 20, 30, etc.
    return False


def get_algorithmic_children(cur, parent_id):
    """Get all motifs that belong under this 10s bin from motif_text"""
    # Extract category and range
    category = parent_id[0]  # e.g., 'A'
    start_num = int(parent_id[1:])  # e.g., 0, 10, 20
    end_num = start_num + 9  # e.g., 9, 19, 29

    print(f"DEBUG ALGORITHMIC: Searching for {category}{start_num}-{category}{end_num} motifs")

    # Get ALL motifs in this range from motif_text
    cur.execute("""
        SELECT mt.motif_id, mt.text,
               COUNT(tm.type_id) as connected_count
        FROM folklore.motif_text mt
        JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
        WHERE mt.motif_id ~ %s
        AND CAST(REGEXP_REPLACE(
            SPLIT_PART(mt.motif_id, '.', 1),
            '[A-Z]', '', 'g'
        ) AS INTEGER) BETWEEN %s AND %s
        GROUP BY mt.motif_id, mt.text
        ORDER BY
            CAST(REGEXP_REPLACE(
                SPLIT_PART(mt.motif_id, '.', 1),
                '[A-Z]', '', 'g'
            ) AS INTEGER),
            LENGTH(mt.motif_id),
            mt.motif_id;
    """, (f"^{category}[0-9]", start_num, end_num))

    results = cur.fetchall()
    print(f"DEBUG ALGORITHMIC: SQL query returned {len(results)} raw results")

    children = []
    for i, row in enumerate(results):
        child_data = {
            'child_id': row[0],
            'label': row[1],
            'connected_count': row[2],
            'total_count': row[2],  # Same for individual motifs
            'has_children': False,  # Individual motifs are leaf nodes
            'is_leaf': True
        }
        children.append(child_data)

        # Debug first few and last few
        if i < 3 or i >= len(results) - 3:
            print(f"DEBUG ALGORITHMIC:   [{i}] {row[0]}: '{row[1][:40]}...' connected={row[2]}")

    print(f"DEBUG ALGORITHMIC: Created {len(children)} child objects")
    return children


def get_synopsis_children(cur, parent_id):
    """Get children using the existing synopsis_edges approach"""
    print(f"DEBUG SYNOPSIS: Getting children from synopsis_edges for '{parent_id}'")

    # Get direct children from synopsis_edges
    cur.execute("""
        SELECT mse.motif_child, s.label
        FROM folklore.motif_synopsis_edges mse
        JOIN folklore.synopsis s ON mse.motif_child = s.motif_id
        WHERE mse.motif_parent = %s;
    """, (parent_id,))

    results = cur.fetchall()
    print(f"DEBUG SYNOPSIS: Found {len(results)} direct children in synopsis_edges")

    if len(results) == 0:
        print(f"DEBUG SYNOPSIS: No children found for '{parent_id}' - returning empty list")
        return []

    # Your existing sort logic
    def sort_tmi_children(item):
        child_id = item[0]
        category = child_id[0] if child_id else 'Z'
        is_range = '-' in child_id

        if is_range:
            try:
                parts = child_id.split('-')
                start_num = int(''.join(filter(str.isdigit, parts[0])))
                end_num = int(''.join(filter(str.isdigit, parts[1])))
                return (category, 1, start_num, end_num, 0, 0)
            except (ValueError, IndexError):
                return (category, 1, 999999, 999999, 0, 0)
        else:
            try:
                num_part = child_id[1:] if len(child_id) > 1 else '0'
                parts = num_part.split('.')
                main_num = int(parts[0]) if parts[0].isdigit() else 0
                decimal_1 = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                decimal_2 = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                return (category, 0, main_num, 0, decimal_1, decimal_2)
            except (ValueError, IndexError):
                return (category, 0, 999999, 0, 0, 0)

    sorted_results = sorted(results, key=sort_tmi_children)
    print(f"DEBUG SYNOPSIS: Sorted {len(sorted_results)} children")

    children = []
    for i, row in enumerate(sorted_results):
        child_id = row[0]
        child_label = row[1]

        # Check if this child has its own children
        cur.execute("""
            SELECT COUNT(*) FROM folklore.motif_synopsis_edges 
            WHERE motif_parent = %s;
        """, (child_id,))

        has_children_count = cur.fetchone()[0]
        has_children = has_children_count > 0

        # Count connected motifs using existing logic
        connected_count = count_connected_motifs_in_range(cur, child_id)

        child_data = {
            'child_id': child_id,
            'label': child_label,
            'connected_count': connected_count,
            'total_count': connected_count,
            'has_children': has_children,
            'is_leaf': not has_children
        }
        children.append(child_data)

        # Debug output for first few children
        if i < 5:
            print(f"DEBUG SYNOPSIS:   [{i}] {child_id}: has_children={has_children}, connected={connected_count}")

    print(f"DEBUG SYNOPSIS: Created {len(children)} child objects")
    return children


def count_connected_motifs_in_range(cur, range_id):
    """Helper function to count connected motifs in a given TMI range or leaf"""

    if '-' in range_id:
        # Handle ranges like "A0-A99", "T100-T199", etc.
        try:
            parts = range_id.split('-')
            start_part = parts[0]  # e.g., "T100"
            end_part = parts[1]  # e.g., "T199"

            category = start_part[0]  # e.g., "T"
            start_num = int(''.join(filter(str.isdigit, start_part)))  # e.g., 100
            end_num = int(''.join(filter(str.isdigit, end_part)))  # e.g., 199

            print(f"DEBUG: Counting range {range_id} -> category={category}, range={start_num}-{end_num}")

            # Count motifs where the numeric part falls within the range
            cur.execute("""
                SELECT COUNT(DISTINCT tm.motif_id)
                FROM folklore.motif_text mt
                JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
                WHERE mt.motif_id ~ %s
                AND CAST(REGEXP_REPLACE(
                    SPLIT_PART(mt.motif_id, '.', 1), 
                    '[A-Z]', '', 'g'
                ) AS INTEGER) BETWEEN %s AND %s;
            """, (f"^{category}[0-9]", start_num, end_num))

            result = cur.fetchone()[0]
            print(f"DEBUG: Range {range_id} has {result} connected motifs")
            return result

        except (ValueError, IndexError) as e:
            print(f"DEBUG: Error parsing range {range_id}: {e}")
            return 0

    else:
        # Handle leaf nodes like "T100", "T110", etc.
        # These are decade bins: T100 should include T100-T109
        try:
            if len(range_id) < 2:
                return 0

            category = range_id[0]
            numeric_part = ''.join(filter(str.isdigit, range_id))

            if not numeric_part:
                return 0

            bin_number = int(numeric_part)

            # Determine the decade range for this bin
            # T100 -> 100-109, T110 -> 110-119, T130 -> 130-139, etc.
            range_start = bin_number
            range_end = bin_number + 9

            print(f"DEBUG: Counting leaf bin {range_id} -> category={category}, decade range={range_start}-{range_end}")

            # Count motifs in this decade range
            cur.execute("""
                SELECT COUNT(DISTINCT tm.motif_id)
                FROM folklore.motif_text mt
                JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
                WHERE mt.motif_id ~ %s
                AND CAST(REGEXP_REPLACE(
                    SPLIT_PART(mt.motif_id, '.', 1), 
                    '[A-Z]', '', 'g'
                ) AS INTEGER) BETWEEN %s AND %s;
            """, (f"^{category}[0-9]", range_start, range_end))

            result = cur.fetchone()[0]
            print(f"DEBUG: Leaf bin {range_id} has {result} connected motifs in range {range_start}-{range_end}")
            return result

        except Exception as e:
            print(f"DEBUG: Error counting leaf {range_id}: {e}")
            return 0


@app.route('/get_motifs_for_node/<node_id>')
def get_motifs_for_node(node_id):
    """Get actual motifs for a TMI node (leaf bin) - ONLY those connected to ATU"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    # DEBUG: Log the limit being used
    print(f"DEBUG get_motifs_for_node: node_id={node_id}, limit={limit}, offset={offset}")
    if limit == 5:
        print("*** FOUND LIMIT 5 in get_motifs_for_node! ***")
        import traceback
        traceback.print_stack()

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        print(f"DEBUG: Getting motifs for node '{node_id}'")

        # Determine if this is a range or a specific bin
        if '-' in node_id:
            # Handle ranges like A100-A499
            start_part, end_part = node_id.split('-')
            category = start_part[0]
            start_num = int(''.join(filter(str.isdigit, start_part)))
            end_num = int(''.join(filter(str.isdigit, end_part)))

            print(f"DEBUG: Range detected - {category} from {start_num} to {end_num}")

            cur.execute("""
                SELECT mt.motif_id, mt.text, COUNT(tm.type_id) as type_count
                FROM folklore.motif_text mt
                JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
                WHERE mt.motif_id ~ %s
                AND CAST(REGEXP_REPLACE(
                    SPLIT_PART(mt.motif_id, '.', 1),
                    '[A-Z]', '', 'g'
                ) AS INTEGER) BETWEEN %s AND %s
                GROUP BY mt.motif_id, mt.text
                ORDER BY
                    CAST(REGEXP_REPLACE(
                        SPLIT_PART(mt.motif_id, '.', 1),
                        '[A-Z]', '', 'g'
                    ) AS INTEGER),
                    mt.motif_id
                LIMIT %s OFFSET %s;
            """, (f"^{category}[0-9]", start_num, end_num, limit, offset))

        else:
            # Handle specific bins like T210, T100, etc.
            # These should be DECADE bins: T210 = T210-T219
            if len(node_id) < 2:
                print(f"DEBUG: Node ID too short: {node_id}")
                cur.close()
                conn.close()
                return jsonify({'motifs': [], 'total': 0, 'limit': limit, 'offset': offset})

            category = node_id[0]
            numeric_part = ''.join(filter(str.isdigit, node_id))

            if not numeric_part:
                print(f"DEBUG: No numeric part found in {node_id}")
                cur.close()
                conn.close()
                return jsonify({'motifs': [], 'total': 0, 'limit': limit, 'offset': offset})

            bin_number = int(numeric_part)

            # Determine the DECADE range for this bin
            # T210 -> 210-219, T100 -> 100-109, etc.
            range_start = bin_number
            range_end = bin_number + 9

            print(f"DEBUG: Bin {node_id} -> category {category}, decade range {range_start}-{range_end}")

            cur.execute("""
                SELECT mt.motif_id, mt.text, COUNT(tm.type_id) as type_count
                FROM folklore.motif_text mt
                JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
                WHERE mt.motif_id ~ %s
                AND CAST(REGEXP_REPLACE(
                    SPLIT_PART(mt.motif_id, '.', 1),
                    '[A-Z]', '', 'g'
                ) AS INTEGER) BETWEEN %s AND %s
                GROUP BY mt.motif_id, mt.text
                ORDER BY
                    CAST(REGEXP_REPLACE(
                        SPLIT_PART(mt.motif_id, '.', 1),
                        '[A-Z]', '', 'g'
                    ) AS INTEGER),
                    LENGTH(mt.motif_id),
                    mt.motif_id
                LIMIT %s OFFSET %s;
            """, (f"^{category}[0-9]", range_start, range_end, limit, offset))

        results = cur.fetchall()

        # Get total count using the same logic
        if '-' in node_id:
            cur.execute("""
                SELECT COUNT(*)
                FROM folklore.motif_text mt
                JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
                WHERE mt.motif_id ~ %s
                AND CAST(REGEXP_REPLACE(
                    SPLIT_PART(mt.motif_id, '.', 1),
                    '[A-Z]', '', 'g'
                ) AS INTEGER) BETWEEN %s AND %s;
            """, (f"^{category}[0-9]", start_num, end_num))
        else:
            cur.execute("""
                SELECT COUNT(*)
                FROM folklore.motif_text mt
                JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
                WHERE mt.motif_id ~ %s
                AND CAST(REGEXP_REPLACE(
                    SPLIT_PART(mt.motif_id, '.', 1),
                    '[A-Z]', '', 'g'
                ) AS INTEGER) BETWEEN %s AND %s;
            """, (f"^{category}[0-9]", range_start, range_end))

        total_connected = cur.fetchone()[0]

        print(f"DEBUG: Query returned {len(results)} connected motifs, total: {total_connected}")

        motifs = []
        for i, row in enumerate(results):
            if len(row) >= 3:
                motifs.append({
                    'motif_id': row[0],
                    'text': row[1],
                    'type_count': row[2]
                })

        cur.close()
        conn.close()

        return jsonify({
            'motifs': motifs,
            'total': total_connected,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        print(f"ERROR in get_motifs_for_node: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            cur.close()
            conn.close()
        except:
            pass
        return jsonify({"error": str(e)}), 500

@app.route('/get_tmi_breadcrumb/<node_id>')
def get_tmi_breadcrumb(node_id):
    """Get the breadcrumb trail for a TMI node"""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        breadcrumb = []
        current_node = node_id

        # Walk up the hierarchy to build breadcrumb
        while current_node:
            # Get current node details
            cur.execute("""
                SELECT s.motif_id, s.label
                FROM folklore.synopsis s
                WHERE s.motif_id = %s;
            """, (current_node,))

            node_data = cur.fetchone()
            if node_data:
                breadcrumb.insert(0, {
                    'node_id': node_data[0],
                    'label': node_data[1]
                })

            # Get parent
            cur.execute("""
                SELECT motif_parent
                FROM folklore.motif_synopsis_edges
                WHERE motif_child = %s;
            """, (current_node,))

            parent_data = cur.fetchone()
            current_node = parent_data[0] if parent_data else None

        cur.close()
        conn.close()

        return jsonify(breadcrumb)

    except Exception as e:
        print(f"ERROR in get_tmi_breadcrumb: {str(e)}")
        try:
            cur.close()
            conn.close()
        except:
            pass
        return jsonify({"error": str(e)}), 500


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
    """Get motifs within a specific category - ONLY those connected to tale types"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        # Get motifs in category that are connected to tale types
        cur.execute("""
            SELECT mt.motif_id, mt.text,
                   COUNT(tm.type_id) as type_count
            FROM folklore.motif_text mt
            JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
            WHERE mt.motif_id LIKE %s
            GROUP BY mt.motif_id, mt.text
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

        # Get total count of connected motifs in this category
        cur.execute("""
            SELECT COUNT(*) 
            FROM folklore.motif_text mt
            JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
            WHERE mt.motif_id LIKE %s;
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

    except Exception as e:
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500


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

    # 🆕 Fetch related tale types
    cur.execute("""
        SELECT DISTINCT type_id
        FROM folklore.type_motif
        WHERE motif_id = %s;
    """, (motif_id,))
    related_types_raw = cur.fetchall()
    related_types = [str(row[0]) for row in related_types_raw]

    cur.close()
    conn.close()

    if result:
        ref_terms_list = result[1].split(', ') if result[1] else []
        return jsonify({
            'text': result[0] or '',
            'ref_terms': ref_terms_list,
            'related_types': related_types  # ✅ Add this field
        })
    return jsonify({'text': '', 'ref_terms': [], 'related_types': []})

# @app.route('/get_motif_details/<motif_id>')
# def get_motif_details(motif_id):
#     """Get detailed information about a specific motif"""
#     conn = psycopg2.connect(
#         dbname=os.getenv('DB_NAME'),
#         user=os.getenv('DB_USER'),
#         host=os.getenv('DB_HOST'),
#         port=os.getenv('DB_PORT')
#     )
#     cur = conn.cursor()
#
#     # Get motif text and cultural references
#     cur.execute("""
#         SELECT mt.text,
#                STRING_AGG(DISTINCT mr.ref_term, ', ' ORDER BY mr.ref_term) as ref_terms
#         FROM folklore.motif_text mt
#         LEFT JOIN folklore.motif_ref mr ON mt.motif_id = mr.motif_id
#         WHERE mt.motif_id = %s
#         GROUP BY mt.text;
#     """, (motif_id,))
#
#     result = cur.fetchone()
#     cur.close()
#     conn.close()
#
#     if result:
#         ref_terms_list = result[1].split(', ') if result[1] else []
#         return jsonify({
#             'text': result[0] or '',
#             'ref_terms': ref_terms_list
#         })
#     return jsonify({'text': '', 'ref_terms': []})


@app.route('/search_motifs')
def search_motifs():
    """Search for motifs by ID or text with AND/OR logic and fuzzy toggle (placeholder)"""
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 20))
    logic = request.args.get('logic', 'OR').upper()
    fuzzy = request.args.get('fuzzy', '0') == '1'

    if not query:
        return jsonify([])

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    cur.execute("SET search_path TO folklore, public;")

    if fuzzy:
        if len(query) < 3:
            # Avoid noise from short strings
            cur.close()
            conn.close()
            return jsonify([])

        sql = """
            SELECT motif_id, text
            FROM folklore.motif_text
            WHERE similarity(text::text, %s::text) > 0.3
            ORDER BY similarity(text::text, %s::text) DESC
            LIMIT %s;
        """
        cur.execute(sql, (query, query, limit))
        results = [{'motif_id': r[0], 'text': r[1]} for r in cur.fetchall()]

        cur.close()
        conn.close()
        return jsonify(results)

    terms = [t.strip() for t in query.replace(',', ' ').split() if t.strip()]
    if not terms:
        return jsonify([])

    clauses = [f"(motif_id ILIKE %s OR text ILIKE %s)" for _ in terms]
    connector = " AND " if logic == "AND" else " OR "
    where_clause = connector.join(clauses)

    sql = f"""
        SELECT motif_id, text
        FROM folklore.motif_text
        WHERE {where_clause}
        ORDER BY motif_id
        LIMIT %s;
    """

    params = []
    for term in terms:
        params.extend([f"%{term}%", f"%{term}%"])
    params.append(limit)

    cur.execute(sql, params)
    results = [{'motif_id': r[0], 'text': r[1]} for r in cur.fetchall()]

    cur.close()
    conn.close()
    return jsonify(results)

@app.route('/search_types')
def search_types():
    """Search for tale types by ID or label with support for AND/OR logic and fuzzy toggle (trigram similarity)"""
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 20))
    logic = request.args.get('logic', 'OR').upper()
    fuzzy = request.args.get('fuzzy', '0') == '1'

    if not query:
        return jsonify([])

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    cur.execute("SET search_path TO folklore, public;")

    if fuzzy:
        if len(query) < 3:
            # Too short for trigram similarity to be meaningful
            cur.close()
            conn.close()
            return jsonify([])

        sql = """
            SELECT type_id, label
            FROM folklore.type_embeddings_3sm
            WHERE similarity(label::text, %s::text) > 0.3
            ORDER BY similarity(label::text, %s::text) DESC
            LIMIT %s;
        """
        cur.execute(sql, (query, query, limit))
        results = [{'type_id': r[0], 'label': r[1]} for r in cur.fetchall()]

        cur.close()
        conn.close()
        return jsonify(results)

    # Normalize input: comma or space delimited
    terms = [t.strip() for t in query.replace(',', ' ').split() if t.strip()]
    if not terms:
        return jsonify([])

    # Build dynamic WHERE clause
    clauses = [f"(label ILIKE %s OR type_id ILIKE %s)" for _ in terms]
    connector = " AND " if logic == "AND" else " OR "
    where_clause = connector.join(clauses)

    sql = f"""
        SELECT type_id, label
        FROM folklore.type_embeddings_3sm
        WHERE {where_clause}
        ORDER BY 
            CASE WHEN type_id ~ '^[0-9]+'
                 THEN CAST(REGEXP_REPLACE(type_id, '^([0-9]+).*', '\\1') AS INTEGER)
                 ELSE 9999
            END,
            type_id
        LIMIT %s;
    """

    params = []
    for term in terms:
        params.extend([f"%{term}%", f"%{term}%"])
    params.append(limit)

    cur.execute(sql, params)
    results = [{'type_id': r[0], 'label': r[1]} for r in cur.fetchall()]

    cur.close()
    conn.close()
    return jsonify(results)

# @app.route('/search_types')
# def search_types():
#     """Search for tale types by ID or label"""
#     query = request.args.get('q', '').strip()
#     limit = int(request.args.get('limit', 20))
#
#     if not query:
#         return jsonify([])
#
#     conn = psycopg2.connect(
#         dbname=os.getenv('DB_NAME'),
#         user=os.getenv('DB_USER'),
#         host=os.getenv('DB_HOST'),
#         port=os.getenv('DB_PORT')
#     )
#     cur = conn.cursor()
#
#     # Search by type ID and label
#     cur.execute("""
#         SELECT type_id, label,
#                CASE
#                    WHEN type_id = %s THEN 1
#                    WHEN type_id ILIKE %s THEN 2
#                    ELSE 3
#                END as relevance
#         FROM folklore.type_embeddings_3sm
#         WHERE type_id ILIKE %s OR label ILIKE %s
#         ORDER BY relevance,
#                  CASE WHEN type_id ~ '^[0-9]+'
#                       THEN CAST(REGEXP_REPLACE(type_id, '^([0-9]+).*', '\\1') AS INTEGER)
#                       ELSE 9999
#                  END,
#                  type_id
#         LIMIT %s;
#     """, (query, f"{query}%", f"%{query}%", f"%{query}%", limit))
#
#     results = []
#     for row in cur.fetchall():
#         results.append({
#             'type_id': row[0],
#             'label': row[1],
#             'relevance': row[2]
#         })
#
#     cur.close()
#     conn.close()
#     return jsonify(results)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explore')
def explore():
    return render_template('explore.html')

@app.route('/mapping')
def mapping():
    return render_template('mapping.html')

@app.route('/get_all_motifs_for_node/<node_id>')
def get_all_motifs_for_node(node_id):
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    category = node_id[0]
    start_num = int(''.join(filter(str.isdigit, node_id)))
    end_num = start_num + 9

    try:
        cur.execute("""
            SELECT mt.motif_id, mt.text,
                   (SELECT COUNT(*) FROM folklore.type_motif tm WHERE tm.motif_id = mt.motif_id) as type_count
            FROM folklore.motif_text mt
            WHERE mt.motif_id ~ %s
            AND CAST(REGEXP_REPLACE(
                SPLIT_PART(mt.motif_id, '.', 1),
                '[A-Z]', '', 'g'
            ) AS INTEGER) BETWEEN %s AND %s
            ORDER BY
                CAST(REGEXP_REPLACE(
                    SPLIT_PART(mt.motif_id, '.', 1),
                    '[A-Z]', '', 'g'
                ) AS INTEGER),
                LENGTH(mt.motif_id),
                mt.motif_id;
        """, (f"^{category}[0-9]", start_num, end_num))

        results = cur.fetchall()
        motifs = []
        for row in results:
            motifs.append({
                'motif_id': row[0],
                'text': row[1],
                'type_count': row[2]
            })

        cur.close()
        conn.close()

        return jsonify({
            "motifs": motifs,
            "total": len(motifs)
        })

    except Exception as e:
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

def increment_range(motif_prefix):
    letter = motif_prefix[0]
    number = int(motif_prefix[1:])
    next_num = number + 10
    return f"{letter}{next_num}"


if __name__ == '__main__':
    print("REGISTERED ROUTES:")
    for rule in app.url_map.iter_rules():
        print(rule)
    app.run(debug=True)