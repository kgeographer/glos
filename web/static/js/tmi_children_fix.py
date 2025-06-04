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
            print(f"DEBUG TMI_CHILDREN:   [{i}] {child['child_id']}: {child['label'][:50]}... connected={child['connected_count']} leaf={child['is_leaf']}")
        
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
    
    # TEMPORARY: Get ALL motifs in this range (not just connected ones)
    cur.execute("""
        SELECT mt.motif_id, mt.text,
               COUNT(tm.type_id) as connected_count
        FROM folklore.motif_text mt
        LEFT JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
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