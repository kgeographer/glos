#!/usr/bin/env python3
"""
Verify database structure for enhanced GLOS functionality
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Get database connection"""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def verify_tables():
    """Verify all required tables exist and have data"""
    conn = get_connection()
    cur = conn.cursor()
    
    required_tables = [
        'folklore.type_embeddings_3sm',
        'folklore.motif_text', 
        'folklore.type_motif',
        'folklore.motif_ref',
        'folklore.type_ref',
        'folklore.synopsis'
    ]
    
    print("=" * 60)
    print("DATABASE STRUCTURE VERIFICATION")
    print("=" * 60)
    
    for table in required_tables:
        try:
            # Check if table exists and get row count
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]
            print(f"✓ {table:<35} {count:>8,} rows")
            
            # Show sample data for key tables
            if table in ['folklore.type_embeddings_3sm', 'folklore.motif_text']:
                cur.execute(f"SELECT * FROM {table} LIMIT 1;")
                sample = cur.fetchone()
                print(f"    Sample: {sample}")
                
        except Exception as e:
            print(f"✗ {table:<35} ERROR: {e}")
    
    # Test specific queries used by new routes
    print(f"\n" + "-" * 60)
    print("TESTING KEY QUERIES")
    print("-" * 60)
    
    queries = [
        ("Motif categories", """
            SELECT DISTINCT LEFT(motif_id, 1) as category, COUNT(*) 
            FROM folklore.motif_text 
            WHERE motif_id ~ '^[A-Z]' 
            GROUP BY category 
            ORDER BY category 
            LIMIT 5;
        """),
        
        ("Motif→Type lookup", """
            SELECT tm.type_id, te.label
            FROM folklore.type_motif tm
            JOIN folklore.type_embeddings_3sm te ON tm.type_id = te.type_id
            WHERE tm.motif_id = 'A1'
            LIMIT 3;
        """),
        
        ("Motif search", """
            SELECT motif_id, text
            FROM folklore.motif_text
            WHERE motif_id ILIKE '%A1%' OR text ILIKE '%creator%'
            LIMIT 3;
        """),
        
        ("Type search", """
            SELECT type_id, label
            FROM folklore.type_embeddings_3sm
            WHERE type_id ILIKE '%300%' OR label ILIKE '%dragon%'
            LIMIT 3;
        """)
    ]
    
    for description, query in queries:
        try:
            cur.execute(query)
            results = cur.fetchall()
            print(f"✓ {description:<25} {len(results)} results")
            if results:
                print(f"    Sample: {results[0]}")
        except Exception as e:
            print(f"✗ {description:<25} ERROR: {e}")
    
    cur.close()
    conn.close()

def verify_indexes():
    """Check for useful indexes"""
    conn = get_connection()
    cur = conn.cursor()
    
    print(f"\n" + "-" * 60)
    print("INDEX RECOMMENDATIONS")
    print("-" * 60)
    
    # Check existing indexes
    cur.execute("""
        SELECT schemaname, tablename, indexname, indexdef
        FROM pg_indexes 
        WHERE schemaname = 'folklore'
        ORDER BY tablename, indexname;
    """)
    
    indexes = cur.fetchall()
    print(f"Existing indexes: {len(indexes)}")
    
    for schema, table, index_name, index_def in indexes:
        print(f"  {table}.{index_name}")
    
    # Recommend additional indexes for performance
    recommendations = [
        "CREATE INDEX IF NOT EXISTS idx_motif_text_search ON folklore.motif_text USING gin(to_tsvector('english', text));",
        "CREATE INDEX IF NOT EXISTS idx_type_label_search ON folklore.type_embeddings_3sm USING gin(to_tsvector('english', label));",
        "CREATE INDEX IF NOT EXISTS idx_type_motif_motif_id ON folklore.type_motif(motif_id);",
        "CREATE INDEX IF NOT EXISTS idx_motif_id_prefix ON folklore.motif_text(LEFT(motif_id, 1));",
    ]
    
    print(f"\nRecommended indexes for better search performance:")
    for rec in recommendations:
        print(f"  {rec}")
    
    cur.close()
    conn.close()

def main():
    try:
        verify_tables()
        verify_indexes()
        
        print(f"\n" + "=" * 60)
        print("Database structure looks good for enhanced GLOS functionality!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Database verification failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
