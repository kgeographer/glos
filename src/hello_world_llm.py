from transformers import pipeline

def main():
    # Initialize the text generation pipeline with GPU support
    generator = pipeline('text-generation', model='gpt2', device=0)

    # Generate text based on a simple prompt with truncation
    prompt = "Hello, world!"
    output = generator(prompt, max_length=50, num_return_sequences=1, truncation=True)

    # Print the generated text
    print(output[0]['generated_text'])

if __name__ == "__main__":
    main()