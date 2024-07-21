# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text-classification", model="mehdie/fine_tuned_mBERT")

# Load model directly
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("mehdie/fine_tuned_mBERT")
model = AutoModelForSequenceClassification.from_pretrained("mehdie/fine_tuned_mBERT")

# %% copilot example
import torch

# Example input

def matcher(input_data):
    # Convert input to the expected string format if required by the model
    # This step depends on how the model expects the input
    input_str = f"{input_data['name1']} : {input_data['name2']}"

    # Tokenize the input
    inputs = tokenizer(input_str, return_tensors="pt")

    # Move inputs to GPU if available
    if torch.cuda.is_available():
        inputs = {key: value.to('cuda') for key, value in inputs.items()}

    # Get predictions
    with torch.no_grad():
        outputs = model(**inputs)

    # Process the outputs to extract the decision and confidence score
    # The specific indices here depend on the model's output format
    match_decision = outputs.logits.argmax(-1)
    confidence_score = torch.softmax(outputs.logits, dim=-1)

    # Assuming the model outputs 0 for 'no match' and 1 for 'match'
    decision_str = "Match" if match_decision.item() == 1 else "No Match"

    # Print the result
    print(f"Decision: {decision_str}, Confidence: {confidence_score.max().item():.2f}")


input_data = {"name1": "Yirushalāyim", "name2": "Jerusalem"}
matcher(input_data)
