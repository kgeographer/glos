import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

def analyze_tmi_hierarchy():
    """Analyze gaps in TMI hierarchy to understand the missing motifs problem."""
    
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    
    print("=== TMI HIERARCHY DIAGNOSTIC ANALYSIS ===\n")
    
    # 1. Check what's in synopsis_edges vs motif_text for category A
    print("1. SYNOPSIS EDGES vs MOTIF TEXT COMPARISON (Category A)")
    print("-" * 60)
    
    # Get all A motifs from motif_text
    query_all_a = """
    SELECT motif_id 
    FROM folklore.motif_text 
    WHERE motif_id LIKE 'A%' 
    ORDER BY motif_id
    """
    all_a_motifs = pd.read_sql(query_all_a, conn)
    print(f"Total A motifs in motif_text: {len(all_a_motifs)}")
    
    # Get all A entries from synopsis_edges
    query_edges_a = """
    SELECT DISTINCT motif_child 
    FROM folklore.motif_synopsis_edges 
    WHERE motif_child LIKE 'A%'
    ORDER BY motif_child
    """
    edges_a_motifs = pd.read_sql(query_edges_a, conn)
    print(f"Total A entries in synopsis_edges: {len(edges_a_motifs)}")
    
    # 2. Identify the gap patterns
    print("\n2. SPECIFIC GAP ANALYSIS")
    print("-" * 30)
    
    # Look at the A0-A99 range specifically
    query_a0_99 = """
    SELECT motif_id 
    FROM folklore.motif_text 
    WHERE motif_id ~ '^A[0-9]+' 
    AND CAST(REGEXP_REPLACE(motif_id, '^A([0-9]+).*', '\\1') AS INTEGER) BETWEEN 0 AND 99
    ORDER BY 
        CAST(REGEXP_REPLACE(motif_id, '^A([0-9]+).*', '\\1') AS INTEGER),
        LENGTH(motif_id),
        motif_id
    LIMIT 50
    """
    a0_99_motifs = pd.read_sql(query_a0_99, conn)
    print("First 50 A0-A99 motifs from motif_text:")
    for idx, row in a0_99_motifs.iterrows():
        print(f"  {row['motif_id']}")
    
    # Check what synopsis_edges has for this range
    query_edges_a0_99 = """
    SELECT motif_child 
    FROM folklore.motif_synopsis_edges 
    WHERE motif_child LIKE 'A%'
    AND (motif_child ~ '^A[0-9]+' OR motif_child LIKE 'A%-%')
    ORDER BY motif_child
    """
    edges_a0_99 = pd.read_sql(query_edges_a0_99, conn)
    print(f"\nA entries in synopsis_edges ({len(edges_a0_99)} total):")
    for idx, row in edges_a0_99.iterrows():
        print(f"  {row['motif_child']}")
    
    # 3. Check connected motifs (those with ATU tale type connections)
    print("\n3. CONNECTED MOTIFS ANALYSIS")
    print("-" * 35)
    
    query_connected_a = """
    SELECT mt.motif_id, COUNT(tm.type_id) as type_count
    FROM folklore.motif_text mt
    JOIN folklore.type_motif tm ON mt.motif_id = tm.motif_id
    WHERE mt.motif_id LIKE 'A%'
    AND mt.motif_id ~ '^A[0-9]+'
    AND CAST(REGEXP_REPLACE(mt.motif_id, '^A([0-9]+).*', '\\1') AS INTEGER) BETWEEN 0 AND 99
    GROUP BY mt.motif_id
    ORDER BY 
        CAST(REGEXP_REPLACE(mt.motif_id, '^A([0-9]+).*', '\\1') AS INTEGER),
        LENGTH(mt.motif_id),
        mt.motif_id
    LIMIT 30
    """
    connected_a = pd.read_sql(query_connected_a, conn)
    print(f"Connected A0-A99 motifs (first 30 of {len(connected_a)}):")
    for idx, row in connected_a.iterrows():
        print(f"  {row['motif_id']} -> {row['type_count']} tale types")
    
    # 4. Identify the missing hierarchy levels
    print("\n4. MISSING HIERARCHY PATTERNS")
    print("-" * 35)
    
    # Look for motifs that should be intermediate nodes
    missing_intermediates = []
    
    # Check for A1, A2, A3... A9 (single digits)
    for i in range(1, 10):
        motif_id = f"A{i}"
        check_query = f"""
        SELECT COUNT(*) 
        FROM folklore.motif_text 
        WHERE motif_id = '{motif_id}'
        """
        result = pd.read_sql(check_query, conn)
        if result.iloc[0, 0] > 0:
            missing_intermediates.append(motif_id)
    
    # Check for A1.1, A1.2, etc. patterns  
    for i in range(1, 20):
        for j in range(1, 10):
            motif_id = f"A{i}.{j}"
            check_query = f"""
            SELECT COUNT(*) 
            FROM folklore.motif_text 
            WHERE motif_id = '{motif_id}'
            """
            result = pd.read_sql(check_query, conn)
            if result.iloc[0, 0] > 0:
                missing_intermediates.append(motif_id)
                if len(missing_intermediates) > 20:  # Limit for display
                    break
        if len(missing_intermediates) > 20:
            break
    
    print(f"Sample missing intermediate motifs (not in synopsis_edges):")
    for motif in missing_intermediates[:15]:
        print(f"  {motif}")
    
    # 5. Suggest hierarchy structure
    print("\n5. PROPOSED HIERARCHY STRUCTURE")
    print("-" * 40)
    print("Current synopsis_edges structure:")
    print("  A (root)")
    print("  └── A0-A99")
    print("      ├── A0")
    print("      ├── A10") 
    print("      └── A20")
    print()
    print("Needed complete structure:")
    print("  A (root)")
    print("  └── A0-A99")
    print("      ├── A0")
    print("      ├── A1 (missing)")
    print("      │   ├── A1.1 (missing)")
    print("      │   ├── A1.2 (missing)")
    print("      │   └── A1.3 (missing)")
    print("      ├── A2 (missing)")
    print("      ├── A3 (missing)")
    print("      ...")
    print("      ├── A10")
    print("      └── A20")
    
    conn.close()
    
    print("\n=== ANALYSIS COMPLETE ===")
    print("\nRECOMMENDATION:")
    print("1. Build complete hierarchy from motif_text using numeric patterns")
    print("2. Supplement synopsis_edges with algorithmic parent-child detection") 
    print("3. Create a hybrid approach that uses both data sources")

if __name__ == "__main__":
    analyze_tmi_hierarchy()