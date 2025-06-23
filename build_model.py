import markovify

# Read the growing corpus
with open("intros.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Build a Markov model
model = markovify.NewlineText(text, state_size=2)

# Serialize it
with open("model.json", "w", encoding="utf-8") as f:
    f.write(model.to_json())

print("✅ model.json written.")
