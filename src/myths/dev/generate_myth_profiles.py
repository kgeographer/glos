import json
from pathlib import Path
from collections import defaultdict

# Define input and output paths
input_dir = Path("out/myths/jsonld_raw")
output_path = Path("out/myths/reports/myth_profiles_20.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

# Initialize container for myth profiles
myth_profiles = {}

# Process each file
for file_path in input_dir.glob("*.jsonld"):
    myth_id = file_path.stem  # e.g., 'pm001_cagn_orders_world'
    myth_key = myth_id.split("_")[0]  # normalize to 'pm001'

    # Temporary containers for this myth
    entities = set()
    events = set()
    relations = set()
    roles = set()

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assertions = data.get("assertions", [])
        for assertion in assertions:
            # Entity types
            entity = assertion.get("entity")
            if entity and "type" in entity:
                entities.add(entity["type"])

            # Event types and roles
            event = assertion.get("event")
            if event:
                if "type" in event:
                    events.add(event["type"])
                for role_key in ["agent", "patient", "instrument", "beneficiary"]:
                    if role_key in event:
                        roles.add(role_key)
                if "resultingState" in event:
                    relations.add("resultingState")

            # Relation types
            relation = assertion.get("relation")
            if relation and "type" in relation:
                relations.add(relation["type"])

    # Assemble profile
    myth_profiles[myth_key] = {
        "entity_types": sorted(entities),
        "event_types": sorted(events),
        "relation_types": sorted(relations),
        "role_types": sorted(roles)
    }

# Save profiles to JSON
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(myth_profiles, f, indent=2)

print(f"Myth profiles written to {output_path}")