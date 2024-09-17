import re

# Initialize data structures
parent_map = {}  # This will store parent-child relationships
current_range = None  # This will store the most recent range (top-level or sub-range)
current_parent = None  # This will store the current parent

# Function to extract the numeric start and end of a range (e.g., "A100-A499" -> 100, 499)
def extract_range_from_line(line):
    range_match = re.findall(r'\b[A-Z]\d+-[A-Z]?\d+\b', line)
    if range_match:
        start, end = map(int, re.findall(r'\d+', range_match[0]))
        return start, end  # Return start and end of the range
    return None, None

# Function to extract the numeric value from a single identifier (e.g., "A100" -> 100)
def extract_single_id_from_line(line):
    match = re.search(r'^[A-Z]\d+\.', line)  # Ensures it starts with "A<number>."
    if match:
        return int(re.search(r'\d+', match.group()).group())
    return None

# Function to process each line
def process_line(line):
    global current_range, current_parent

    # Check if the line is a range (e.g., "A100-A499")
    start, end = extract_range_from_line(line)
    if start is not None and end is not None:
        # If it's the first range, set it as the top-level category
        if current_range is None:
            current_range = (start, end)
            current_parent = None  # No parent for the top-level category
            parent_map[line] = None  # Top-level category has no parent
        else:
            # Check if this new range falls within the previous range
            if current_range[0] <= start <= current_range[1]:
                # This is a sub-range of the current range
                parent_map[line] = current_parent  # Assign the current parent
                current_parent = line  # Now this range becomes the parent
                current_range = (start, end)  # Update the current range
            else:
                # This is a new top-level category, reset parent
                current_range = (start, end)
                current_parent = None
                parent_map[line] = None  # Top-level category has no parent
    else:  # Single identifier or non-range line
        single_id = extract_single_id_from_line(line)
        if single_id is not None and current_range is not None:
            # Check if this single ID falls within the current range
            if current_range[0] <= single_id <= current_range[1]:
                # This single ID is a child of the current parent
                parent_map[line] = current_parent

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
A900-A999. Topographical features of the earth
A900. Topography - general considerations
A910-A949. Water features
A910. Origin of water features
A920. Origin of the seas
A930. Origin of streams - general
""".strip().split('\n')

# Process each line in the detailed synopsis
for line in lines:
    process_line(line)

# Output the parent-child relationships
print("Parent-Child Relationships:")
for child, parent in parent_map.items():
    print(f"{child} --> Parent: {parent}")

