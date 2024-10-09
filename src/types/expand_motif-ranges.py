import psycopg2

# Database connection parameters
DB_PARAMS = {
  "host": "localhost",
  "database": "staging",
  "user": "postgres",
  "port": 5435
}


# Function to get row number for a given motif_id
def get_rownum_for_motif(conn, motif_id):
  with conn.cursor() as cur:
    cur.execute("""
            SELECT rownum 
            FROM folklore.motif_text 
            WHERE motif_id = %s
        """, (motif_id,))
    row = cur.fetchone()
  return row[0] if row else None


# Function to get all motif IDs between two row numbers
def get_motif_ids_between(conn, start_rownum, end_rownum):
  with conn.cursor() as cur:
    cur.execute("""
            SELECT motif_id 
            FROM folklore.motif_text 
            WHERE rownum BETWEEN %s AND %s
        """, (start_rownum, end_rownum))
    rows = cur.fetchall()
  return [row[0] for row in rows]


# Function to insert motif IDs into edge table (insert mode)
def insert_motif_ids_to_edge_table(conn, type_id, motif_ids):
  with conn.cursor() as cur:
    for motif_id in motif_ids:
      cur.execute("""
                INSERT INTO folklore.edges_atu_tmi (type_id, motif_id)
                VALUES (%s, %s)
            """, (type_id, motif_id))
  conn.commit()  # Commit after all inserts to ensure they're saved


# Function to handle the ranges and perform actual insert
def process_ranges_insert(conn, type_id, start_motif, end_motif):
  # Step 1: Get the start and end row numbers
  start_rownum = get_rownum_for_motif(conn, start_motif)
  end_rownum = get_rownum_for_motif(conn, end_motif)

  if start_rownum is None or end_rownum is None:
    print(f"Could not find row numbers for {start_motif} or {end_motif}")
    return

  # Step 2: Fetch all motif IDs in between
  motif_ids = get_motif_ids_between(conn, start_rownum, end_rownum)

  # Step 3: Perform the actual insertion
  insert_motif_ids_to_edge_table(conn, type_id, motif_ids)


def main():
  # List of ranges to process
  ranges = [
    ('1960M', 'X1280', 'X1296.1'),
    # ('1319*', 'J1759', 'J1763'),
    # ('1319*', 'J1770', 'J1772'),
    # ('1419D', 'K1517', 'K1517.12'),
    # ('1960D', 'X1401', 'X1455'),
    # ('1960E', 'X1030', 'X1036'),
    # ('756B', 'S223', 'S226'),
    # ('875', 'H630', 'H659'),
    # ('875', 'H1050', 'H1065'),
    # ('921', 'H1050', 'H1064'),
    # ('875D', 'H586.1', 'H586.7')
  ]

  conn = psycopg2.connect(**DB_PARAMS)

  try:
    for type_id, start_motif, end_motif in ranges:
      process_ranges_insert(conn, type_id, start_motif, end_motif)

    print("All inserts have been completed.")

  finally:
    conn.close()


if __name__ == "__main__":
  main()
