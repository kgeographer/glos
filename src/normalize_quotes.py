import os
import unicodedata

# Define your normalization function
def normalize_text(text):
    # Replace curly quotes/apostrophes with straight ones
    text = (text.replace("‘", "'").replace("’", "'")
                .replace("“", '"').replace("”", '"'))
    # Normalize en/em dashes and minus sign to simple hyphen
    text = (text.replace("–", "-").replace("—", "-").replace("−", "-"))
    # Normalize non-breaking spaces to regular space
    text = text.replace("\u00A0", " ")
    # Unicode normalization (optional but safe)
    return unicodedata.normalize('NFKC', text)

# Walk through all .txt files in the given folder
def normalize_folder_texts(folder_path):
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith(".txt"):
                file_path = os.path.join(root, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    original = f.read()
                normalized = normalize_text(original)
                if normalized != original:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(normalized)
                    print(f"Normalized: {file_path}")
                else:
                    print(f"No changes: {file_path}")

# Example usage
if __name__ == "__main__":
    folder_to_normalize = "data/myths"  # change as needed
    normalize_folder_texts(folder_to_normalize)
