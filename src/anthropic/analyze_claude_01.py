import psycopg2
import numpy as np
from openai import OpenAI
import anthropic
import os
from dotenv import load_dotenv
import json
from typing import Dict, List, Tuple, Any

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
  "host": "localhost",
  "database": "staging",
  "user": "postgres",
  "port": 5435
}

# Set up Anthropic client
anthropic_client = anthropic.Anthropic(
  api_key=os.getenv("ANTHROPIC_API_KEY")
)

# create hierarchical structure 'category_by_id{}' from atu_type_groups table
def build_atu_category_hierarchy() -> Dict[str, Dict]:
  """
  Build a hierarchical representation of the ATU category structure from the database.

  Returns:
      Dict[str, Dict]: Dictionary of categories keyed by their ID
  """
  conn = psycopg2.connect(**DB_PARAMS)
  cursor = conn.cursor()

  # Fetch all category records
  cursor.execute("""
        SELECT id, type_range, parent, label
        FROM folklore.atu_type_groups
        ORDER BY id
    """)

  records = cursor.fetchall()
  cursor.close()
  conn.close()

  # Build dictionary of categories
  category_by_id = {}
  for record in records:
    id_val, type_range, parent, label = record
    category_by_id[type_range] = {
      "id": id_val,
      "type_range": type_range,
      "parent": parent,
      "label": label,
      "children": []
    }

  # Add children to their parents
  for cat_id, category in category_by_id.items():
    parent_id = category["parent"]
    if parent_id and parent_id in category_by_id:
      category_by_id[parent_id]["children"].append(cat_id)

  return category_by_id

# generate embeddings for the ATU categories using Anthropic's API
def normalize_range(range_str: str) -> Tuple[int, int]:
  """
  Normalize an ATU range string to a start and end integer.

  Args:
      range_str: ATU range string (like "1-299" or "1–99")

  Returns:
      Tuple[int, int]: Start and end of the range
  """
  if not range_str or range_str == "ATU":
    return (0, 9999)  # Special case for the root

  # Handle both hyphen types
  if "–" in range_str:  # en dash
    parts = range_str.split("–")
  else:
    parts = range_str.split("-")

  # Extract numeric values
  start = int(''.join(filter(str.isdigit, parts[0])))
  end = int(''.join(filter(str.isdigit, parts[1]))) if len(parts) > 1 else start

  return (start, end)

# Generate rich descriptions for each ATU category.
def generate_category_descriptions(category_hierarchy: Dict[str, Dict]) -> List[Dict]:
  """
  Generate rich descriptions for each ATU category.

  Args:
      category_hierarchy: The hierarchy of ATU categories

  Returns:
      List[Dict]: List of categories with descriptions
  """
  categories_with_desc = []

  for cat_id, category in category_hierarchy.items():
    # Skip non-range categories
    if cat_id == "ATU":
      continue

    # Get normalized range
    start, end = normalize_range(cat_id)

    # Build a rich description
    description = f"ATU Category {cat_id}: {category['label']} - "

    # Add information about parent category if it exists
    parent_id = category["parent"]
    if parent_id and parent_id in category_hierarchy:
      description += f"Part of {parent_id} ({category_hierarchy[parent_id]['label']}). "

    # Add information about child categories if they exist
    if category["children"]:
      child_labels = [f"{child_id} ({category_hierarchy[child_id]['label']})"
                      for child_id in category["children"][:3]]
      description += f"Includes subcategories: {', '.join(child_labels)}"
      if len(category["children"]) > 3:
        description += f" and {len(category['children']) - 3} more."

    # Add examples of tale types in this category if possible
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    cursor.execute("""
            SELECT type_id, label
            FROM folklore.type_embeddings_3sm
            WHERE REGEXP_REPLACE(type_id, '[A-Za-z]', '', 'g')::integer BETWEEN %s AND %s
            LIMIT 3
        """, (start, end))

    examples = cursor.fetchall()
    cursor.close()
    conn.close()

    if examples:
      example_str = ", ".join([f"{ex[0]} ({ex[1].split('.')[0]})" for ex in examples])
      description += f" Example tale types: {example_str}."

    categories_with_desc.append({
      "id": cat_id,
      "numeric_range": (start, end),
      "label": category["label"],
      "description": description
    })

  return categories_with_desc

# Get embedding for text using Anthropic's API.
def get_anthropic_embedding(text: str) -> List[float]:
  """
  Get embedding for text using Anthropic's API.

  Args:
      text: The text to embed

  Returns:
      List[float]: The embedding vector
  """
  response = anthropic_client.embeddings.create(
    model="claude-3-haiku-20240307",
    input=text,
    dimensions=1536  # Match OpenAI's dimensions for compatibility
  )

  return response.embeddings[0]

# Create and store embeddings for ATU categories.
def create_atu_category_embeddings() -> List[Dict]:
  """
  Create and store embeddings for ATU categories.

  Returns:
      List[Dict]: Category information with embeddings
  """
  # Build the category hierarchy
  category_hierarchy = build_atu_category_hierarchy()

  # Generate rich descriptions
  categories_with_desc = generate_category_descriptions(category_hierarchy)

  # Generate embeddings
  for category in categories_with_desc:
    category["embedding"] = get_anthropic_embedding(category["description"])

  # Store in database
  conn = psycopg2.connect(**DB_PARAMS)
  cursor = conn.cursor()

  # Create table if it doesn't exist
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS folklore.atu_category_embeddings (
            category_id VARCHAR(20) PRIMARY KEY,
            label TEXT NOT NULL,
            description TEXT NOT NULL,
            range_start INTEGER,
            range_end INTEGER,
            embedding VECTOR(1536)
        )
    """)

  # Insert data
  for category in categories_with_desc:
    cursor.execute("""
            INSERT INTO folklore.atu_category_embeddings
            (category_id, label, description, range_start, range_end, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (category_id) DO UPDATE
            SET description = EXCLUDED.description,
                embedding = EXCLUDED.embedding
        """, (
      category["id"],
      category["label"],
      category["description"],
      category["numeric_range"][0],
      category["numeric_range"][1],
      category["embedding"]
    ))

  conn.commit()
  cursor.close()
  conn.close()

  return categories_with_desc

# Calculate cosine similarity between two vectors.
def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        float: Cosine similarity
    """
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)

    if a_norm == 0 or b_norm == 0:
      return 0

    return np.dot(a, b) / (a_norm * b_norm)

# Categorize a narrative according to the ATU hierarchy.
def categorize_narrative(narrative_text: str) -> List[Dict]:
  """
  Categorize a narrative according to the ATU hierarchy.

  Args:
      narrative_text: The narrative text to categorize

  Returns:
      List[Dict]: Ranked ATU categories with similarity scores
  """
  # Get embedding for the narrative
  narrative_embedding = get_anthropic_embedding(narrative_text)

  # Fetch category embeddings from the database
  conn = psycopg2.connect(**DB_PARAMS)
  cursor = conn.cursor()

  cursor.execute("""
        SELECT category_id, label, embedding
        FROM folklore.atu_category_embeddings
    """)

  categories = cursor.fetchall()
  cursor.close()
  conn.close()

  # Calculate similarities
  category_scores = []
  for cat_id, label, embedding in categories:
    similarity = cosine_similarity(narrative_embedding, embedding)

    category_scores.append({
      "category_id": cat_id,
      "category_name": label,
      "similarity": similarity
    })

  # Sort by similarity
  category_scores.sort(key=lambda x: x["similarity"], reverse=True)

  return category_scores

# Get tale types that belong to a specific ATU category.
def get_tale_types_by_category(category_id: str) -> List[Dict]:
    """
    Get tale types that belong to a specific ATU category.

    Args:
        category_id: The ATU category ID (range string like "1-299")

    Returns:
        List[Dict]: Tale types in the category
    """
    # Normalize the range
    start, end = normalize_range(category_id)

    # Query the database
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT type_id, label, text, embedding
        FROM folklore.type_embeddings_3sm
        WHERE REGEXP_REPLACE(type_id, '[A-Za-z]', '', 'g')::integer BETWEEN %s AND %s
    """, (start, end))

    tale_types = []
    for row in cursor.fetchall():
      type_id, label, text, embedding = row

      # Get associated motifs
      cursor.execute("""
            SELECT motif_id
            FROM folklore.edges_atu_tmi
            WHERE type_id = %s
        """, (type_id,))

      motif_ids = [row[0] for row in cursor.fetchall()]

      # Get cultural references
      cursor.execute("""
            SELECT ref_term
            FROM folklore.type_ref
            WHERE type_id = %s
        """, (type_id,))

      ref_terms = [row[0] for row in cursor.fetchall()]

      # Get combinations
      cursor.execute("""
            SELECT combinations
            FROM folklore.type_combinations
            WHERE type_id = %s
        """, (type_id,))

      combinations_row = cursor.fetchone()
      combinations = combinations_row[0].split(',') if combinations_row and combinations_row[0] else []

      tale_types.append({
        "type_id": type_id,
        "label": label,
        "text": text,
        "embedding": embedding,
        "motif_ids": motif_ids,
        "ref_terms": ref_terms,
        "combinations": combinations,
        "category_id": category_id
      })

    cursor.close()
    conn.close()

    return tale_types

# Match a narrative to ATU categories and their associated tale types.
def match_narrative_to_categories(narrative_text: str, top_n: int = 3) -> Dict[str, Any]:
  """
  Match a narrative to ATU categories and their associated tale types.

  Args:
      narrative_text: The narrative text to analyze
      top_n: Number of top categories to consider

  Returns:
      Dict: Results including categories and matching tale types
  """
  # Step 1: Categorize the narrative
  category_scores = categorize_narrative(narrative_text)
  top_categories = category_scores[:top_n]

  # Step 2: Get tale types for the top categories
  narrative_embedding = get_anthropic_embedding(narrative_text)
  tale_types_by_category = {}
  all_tale_types = []

  for category in top_categories:
    tale_types = get_tale_types_by_category(category["category_id"])

    # Calculate similarity to the narrative
    for tt in tale_types:
      similarity = cosine_similarity(narrative_embedding, tt["embedding"])
      tt["similarity"] = similarity

    # Sort by similarity
    tale_types.sort(key=lambda x: x["similarity"], reverse=True)

    tale_types_by_category[category["category_id"]] = tale_types
    all_tale_types.extend(tale_types)

  # Step 3: Rank all tale types by similarity
  all_tale_types.sort(key=lambda x: x["similarity"], reverse=True)
  top_tale_types = all_tale_types[:20]  # Top 20 overall

  return {
    "top_categories": top_categories,
    "tale_types_by_category": tale_types_by_category,
    "top_tale_types": top_tale_types
  }

# Example narrative text