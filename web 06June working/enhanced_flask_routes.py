# Add these routes to your existing app.py file

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
        SELECT motif_id, text,
               CASE 
                   WHEN motif_id = %s THEN 1
                   WHEN motif_id ILIKE %s THEN 2
                   ELSE 3
               END as relevance
        FROM folklore.motif_text
        WHERE motif_id ILIKE %s OR text ILIKE %s
        ORDER BY relevance, motif_id
        LIMIT %s;
    """, (query, f"{query}%", f"%{query}%", f"%{query}%", limit))
    
    results = []
    for row in cur.fetchall():
        results.append({
            'motif_id': row[0],
            'text': row[1],
            'relevance': row[2]
        })
    
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
        SELECT DISTINCT LEFT(motif_id, 1) as category,
               COUNT(*) as motif_count
        FROM folklore.motif_text
        WHERE motif_id ~ '^[A-Z]'
        GROUP BY category
        ORDER BY category;
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
            'count': row[1]
        })
    
    cur.close()
    conn.close()
    return jsonify(categories)


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
    
    # Get motifs in category with pagination
    cur.execute("""
        SELECT motif_id, text,
               (SELECT COUNT(*) FROM folklore.type_motif tm WHERE tm.motif_id = mt.motif_id) as type_count
        FROM folklore.motif_text mt
        WHERE motif_id LIKE %s
        ORDER BY motif_id
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
