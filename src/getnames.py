import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

def getnames(place_name):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"List all the name variants and language variants for the place, '{place_name}'"
            }
        ],
        model="gpt-3.5-turbo",
    )

    # Extracting the response content
    response_content = chat_completion.choices[0].message.content.strip()
    return response_content

def parse_variants(response_content):
    variants_dict = {}
    for line in response_content.split("\n"):
        if ". " in line:
            number, variant = line.split(". ", 1)
            language = variant.split(" (")[-1].rstrip(")")
            place_name = variant.split(" (")[0]
            if language not in variants_dict:
                variants_dict[language] = []
            variants_dict[language].append(place_name)
    return variants_dict

if __name__ == "__main__":
    place_name = "Tavakli, Turkey"
    variants_text = getnames(place_name)
    print(f"Raw Variants for {place_name}:\n{variants_text}")

    variants_dict = parse_variants(variants_text)
    print(f"Structured Variants for {place_name}:\n{variants_dict}")