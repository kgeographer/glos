import re
from collections import defaultdict

# Initialize data structures
hierarchy = defaultdict(list)
current_top_category = None
current_sub_range = None

# Function to determine hierarchy level
def get_hierarchy_level(motif_id):
    # Count decimal places to determine depth
    return motif_id.count('.')

# Function to process each line and build the hierarchy
def process_line(line, hierarchy, current_top_category, current_sub_range):
    # Match lines with top-level ranges (e.g., "A100-A499. GODS")
    range_match = re.match(r'([A-Z]\d+-[A-Z]?\d+)\.\s(.+)', line)
    if range_match:
        # Set current category as the range (e.g., "GODS")
        current_top_category = range_match.group(2).strip()
        current_sub_range = None  # Reset sub-range when a new top-level category is found
        hierarchy[current_top_category] = []
        return current_top_category, current_sub_range

    # Match sub-ranges (e.g., "A200-A299. Gods of the upper world")
    subrange_match = re.match(r'([A-Z]\d+-[A-Z]?\d+)\.\s(.+)', line)
    if subrange_match:
        current_sub_range = subrange_match.group(2).strip()
        if current_top_category:
            hierarchy[current_top_category].append((current_sub_range, "Sub-Range"))
        hierarchy[current_sub_range] = []
        return current_top_category, current_sub_range

    # Match individual motif entries (e.g., "A100. Deity")
    motif_match = re.match(r'([A-Z]\d+(?:\.\d+)*?)\.\s(.+)', line)
    if motif_match:
        motif_id = motif_match.group(1).strip()
        description = motif_match.group(2).strip()

        # Determine the hierarchy level based on motif ID
        level = get_hierarchy_level(motif_id)

        # Add the motif to the current sub-range or top-level category
        if current_sub_range:
            hierarchy[current_sub_range].append((motif_id, description, level))
        elif current_top_category:
            hierarchy[current_top_category].append((motif_id, description, level))

    return current_top_category, current_sub_range

# Example input data
lines = """
A100-A499. GODS
A100-A199. The gods in general
A100. Deity
A110. Origin of the gods
A120. Nature and appearance of the gods
A200-A299. Gods of the upper world
A200. God of the upper world
A210. Sky-god
A220. Sun-god
A300-A399. Gods of the underworld
A300. God of the underworld
A310. God of the world of the dead
A400-A499. Gods of the earth
A400. God of the earth
A410. Local gods
A420. God of water
""".strip().split('\n')

# Process each line in the detailed synopsis
for line in lines:
    current_top_category, current_sub_range = process_line(line, hierarchy, current_top_category, current_sub_range)

# Output the parsed hierarchy
for category, motifs in hierarchy.items():
    print(f"Category/Sub-Range: {category}")
    for motif in motifs:
        if isinstance(motif, tuple):
            motif_id, description, level = motif
            indent = "  " * level  # Indent based on hierarchy level
            print(f"{indent}{motif_id}. {description}")
        else:
            print(f"  Sub-Range: {motif}")