import psycopg2
import numpy as np
import json
from typing import Dict, List, Any
import anthropic
import os
from dotenv import load_dotenv
from pprint import pprint

# Load environment variables
load_dotenv()

# Set up Anthropic client
anthropic_client = anthropic.Anthropic(
  api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Database connection parameters
DB_PARAMS = {
  "host": "localhost",
  "database": "staging",
  "user": "postgres",
  "port": 5435
}


def cosine_similarity(a, b):
  """Calculate cosine similarity between two vectors."""
  a_norm = np.linalg.norm(a)
  b_norm = np.linalg.norm(b)

  if a_norm == 0 or b_norm == 0:
    return 0

  return np.dot(a, b) / (a_norm * b_norm)


def get_anthropic_embedding(text):
  """Get embedding for text using Anthropic's API."""
  response = anthropic_client.embeddings.create(
    model="claude-3-haiku-20240307",
    input=text,
    dimensions=1536
  )

  return response.embeddings[0]


def normalize_range(range_str):
  """Normalize an ATU range string to a start and end integer."""
  if not range_str or range_str == "ATU":
    return (0, 9999)

  if "–" in range_str:  # en dash
    parts = range_str.split("–")
  else:
    parts = range_str.split("-")

  start = int(''.join(filter(str.isdigit, parts[0])))
  end = int(''.join(filter(str.isdigit, parts[1]))) if len(parts) > 1 else start

  return (start, end)


def test_narrative_analysis(narrative_text):
  """
  Test the narrative analysis without storing results.

  Args:
      narrative_text: The narrative to analyze

  Returns:
      Dict: Analysis results
  """
  print("Analyzing narrative...")
  print(f"Text length: {len(narrative_text)} characters")

  # Step 1: Get categories from the database
  conn = psycopg2.connect(**DB_PARAMS)
  cursor = conn.cursor()

  cursor.execute("""
        SELECT category_id, label, embedding
        FROM folklore.atu_category_embeddings
    """)

  categories = cursor.fetchall()
  if not categories:
    print("No category embeddings found. Please run create_atu_category_embeddings() first.")
    cursor.close()
    conn.close()
    return None

  print(f"Found {len(categories)} ATU categories with embeddings")

  # Step 2: Get narrative embedding
  print("Generating narrative embedding...")
  narrative_embedding = get_anthropic_embedding(narrative_text)

  # Step 3: Find similar categories
  print("Comparing to ATU categories...")
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
  top_categories = category_scores[:5]  # Top 5 for testing

  print("\nTop ATU Categories:")
  for i, category in enumerate(top_categories):
    print(
      f"{i + 1}. {category['category_id']} - {category['category_name']} (Similarity: {category['similarity']:.4f})")

  # Step 4: Get tale types for top categories
  tale_types_by_category = {}
  all_tale_types = []

  print("\nFinding tale types in each category...")
  for category in top_categories[:3]:  # Just use top 3 categories
    # Normalize the range
    start, end = normalize_range(category["category_id"])

    cursor.execute("""
            SELECT type_id, label, text, embedding
            FROM folklore.type_embeddings_3m
            WHERE REGEXP_REPLACE(type_id, '[A-Za-z]', '', 'g')::integer BETWEEN %s AND %s
        """, (start, end))

    category_tales = []
    tale_count = 0

    for row in cursor.fetchall():
      tale_count += 1
      type_id, label, text, embedding = row

      # Calculate similarity to the narrative
      similarity = cosine_similarity(narrative_embedding, embedding)

      # Only add if similarity is above threshold (0.5 for testing)
      if similarity > 0.5:
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

        tale_data = {
          "type_id": type_id,
          "label": label,
          "text": text[:200] + "..." if len(text) > 200 else text,  # Truncate for display
          "similarity": similarity,
          "motif_ids": motif_ids[:10],  # Limit for display
          "ref_terms": ref_terms[:10],  # Limit for display
          "combinations": combinations[:10],  # Limit for display
          "category_id": category["category_id"]
        }

        category_tales.append(tale_data)
        all_tale_types.append(tale_data)

    # Sort by similarity
    category_tales.sort(key=lambda x: x["similarity"], reverse=True)

    print(
      f"  Category {category['category_id']} - {category['category_name']}: Found {tale_count} tale types, {len(category_tales)} with similarity > 0.5")

    tale_types_by_category[category["category_id"]] = category_tales

  # Step 5: Get top motifs for the most similar tale types
  print("\nFinding relevant motifs...")
  all_tale_types.sort(key=lambda x: x["similarity"], reverse=True)
  top_tale_types = all_tale_types[:10]  # Top 10 overall

  # Collect all motif IDs from top tale types
  all_motif_ids = []
  for tt in top_tale_types:
    all_motif_ids.extend(tt["motif_ids"])

  # Remove duplicates
  unique_motif_ids = list(set(all_motif_ids))

  # Get motif details
  motif_details = []
  for motif_id in unique_motif_ids[:20]:  # Limit to 20 motifs for testing
    cursor.execute("""
            SELECT m.motif_id, m.motif_text, m.embedding
            FROM folklore.motif_embedding m
            WHERE m.motif_id = %s
        """, (motif_id,))

    row = cursor.fetchone()
    if row:
      motif_id, motif_text, motif_embedding = row

      # Calculate similarity to narrative
      similarity = cosine_similarity(narrative_embedding, motif_embedding)

      motif_details.append({
        "motif_id": motif_id,
        "motif_text": motif_text,
        "similarity": similarity
      })

  # Sort motifs by similarity
  motif_details.sort(key=lambda x: x["similarity"], reverse=True)

  # Close database connection
  cursor.close()
  conn.close()

  # Prepare final results
  results = {
    "top_categories": top_categories,
    "top_tale_types": top_tale_types,
    "top_motifs": motif_details[:10]  # Top 10 motifs
  }

  # Print summary
  print("\n===== ANALYSIS SUMMARY =====")
  print(
    f"Top ATU Category: {results['top_categories'][0]['category_id']} - {results['top_categories'][0]['category_name']}")
  print("\nTop 5 Tale Types:")
  for i, tt in enumerate(results['top_tale_types'][:5]):
    print(f"{i + 1}. {tt['type_id']} - {tt['label']} (Similarity: {tt['similarity']:.4f})")

  print("\nTop 5 Motifs:")
  for i, motif in enumerate(results['top_motifs'][:5]):
    print(f"{i + 1}. {motif['motif_id']} - {motif['motif_text'][:100]}... (Similarity: {motif['similarity']:.4f})")

  return results

# Tsui||goab tale text
tsui_goab_tale = """The Supreme Being
Tsui||goab was a great powerful chief of the Khoikhoi; in fact, he was the first Khoikhoib, from whom all the Khoikhoi tribes took their origin. But Tsui||goab was not his original name. This Tsui||goab went to war with another chief, ||Gaunab, because the latter always killed great numbers of Tsui||goab's people. In this fight, however, Tsui||goab was repeatedly overpowered by ||Gaunab, but in every battle the former grew stronger; and at last he was so strong and big that he easily destroyed ||Gaunab, by giving him one blow behind the ear. While ||Gaunab was expiring he gave his enemy a blow on the knee. Since that day the conqueror of ||Gaunab received the name Tsui|| goab, "sore knee," or "wounded knee." Henceforth he could not walk properly, because he was lame. He could do wonderful things, which no other man could do, because he was very wise. He could tell what would happen in future times. He died several times, and several times he rose again. And whenever he came back to us, there were great feastings and rejoicings. Milk was brought from every kraal, and fat cows and fat ewes were slaughtered. Tsui||goab gave every man plenty of cattle and sheep, because he was very rich. He gives rain, he makes the clouds, he lives in the clouds, and he makes our cows and sheep fruitful. Tsui||goab lives in a beautiful heaven, and ||Gaunab lives in a dark heaven, quite separated from the heaven of Tsui||goab."""

# Run the test
test_results = test_narrative_analysis(tsui_goab_tale)