@app.route('/get_tmi_hierarchy')
def get_tmi_hierarchy():
    """Build TMI hierarchy from synopsis and motif_synopsis_edges tables"""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        # Get all synopsis entries and edges
        cur.execute("""
            SELECT motif_id, label 
            FROM folklore.synopsis 
            ORDER BY motif_id;
        """)
        all_synopsis = {row[0]: row[1] for row in cur.fetchall()}
        
        cur.execute("""
            SELECT motif_child, motif_parent
            FROM folklore.motif_synopsis_edges;
        """)
        all_edges = cur.fetchall()
        
        # Build parent-to-children mapping
        children_map = {}
        for child, parent in all_edges:
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(child)
        
        # Build hierarchy starting from main categories (children of MIFL, excluding MIFL itself)
        def build_node(motif_id, level=0):
            # Skip MIFL root - start with actual categories
            if motif_id == 'MIFL':
                return None
                
            node = {
                'motif_id': motif_id,
                'label': all_synopsis.get(motif_id, motif_id),
                'children': []
            }
            
            # Get children for this node
            if motif_id in children_map:
                for child_id in sorted(children_map[motif_id]):
                    if child_id != 'MIFL':  # Avoid circular references
                        child_node = build_node(child_id, level + 1)
                        if child_node:
                            node['children'].append(child_node)
            
            return node
        
        # Start with main categories (A, B, C, D, etc.) - children of MIFL
        hierarchy = []
        if 'MIFL' in children_map:
            main_categories = sorted(children_map['MIFL'])
            for category in main_categories:
                # Only include single-letter categories for top level
                if len(category) == 1 and category.isalpha():
                    node = build_node(category)
                    if node:
                        hierarchy.append(node)
        
        cur.close()
        conn.close()
        return jsonify(hierarchy)
        
    except Exception as e:
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/get_motifs_in_category/<category>')
def get_motifs_in_category(category):
    """Get motifs within a specific category with pagination - UPDATED for TMI hierarchy"""
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
        # Get motifs in category with pagination (only those with associated tale types)
        # Updated to work with actual motif IDs from motif_text table
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