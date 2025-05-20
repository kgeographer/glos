"""
extract_ontology_elements.py

This script scans all JSON-LD files in the 'out/myths/jsonld_raw' directory, each representing
a processed creation myth, and extracts a consolidated list of all unique ontological terms
used across the dataset. It collects the following vocabularies:

- Entity Types: classes of beings, objects, or places referenced in the myths.
- Event Types: types of actions or processes described in mythic events.
- Relation Types: named relationships between entities (e.g., childOf, spouseOf, resultingState).
- Role Types: semantic roles within events, such as agent, patient, or instrument.

The collected terms are organized into a CSV file, 'ontology_elements_20.csv',
saved in the 'out/myths/' directory. This output serves as a raw term inventory for
future normalization and formal ontology development.
"""

import json
import os
import pandas as pd
from pathlib import Path

# Define input and output paths
input_dir = Path("out/myths/jsonld_raw")
output_csv = Path("out/myths/ontology_elements_20.csv")

# Initialize sets to collect unique values
entity_types = set()
event_types = set()
relation_types = set()
role_types = set()

# Loop through all JSON-LD files in the input directory
for file_path in input_dir.glob("*.jsonld"):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assertions = data.get("assertions", [])
        for assertion in assertions:
            # Extract entity types
            entity = assertion.get("entity")
            if entity and "type" in entity:
                entity_types.add(entity["type"])

            # Extract event types and role types
            event = assertion.get("event")
            if event:
                if "type" in event:
                    event_types.add(event["type"])
                for role_key in ["agent", "patient", "instrument", "beneficiary"]:
                    if role_key in event:
                        role_types.add(role_key)
                # Treat resultingState as a relation type
                if "resultingState" in event:
                    relation_types.add("resultingState")

            # Extract explicit relation types
            relation = assertion.get("relation")
            if relation and "type" in relation:
                relation_types.add(relation["type"])

# Normalize lists to equal lengths
max_len = max(
    len(entity_types), len(event_types),
    len(relation_types), len(role_types)
)
def pad(lst): return sorted(lst) + [None] * (max_len - len(lst))

# Create DataFrame
df = pd.DataFrame({
    "Entity Types": pad(entity_types),
    "Event Types": pad(event_types),
    "Relation Types": pad(relation_types),
    "Role Types": pad(role_types)
})

# Ensure output directory exists and save CSV
output_csv.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_csv, index=False)

print(f"Ontology elements written to {output_csv}")
