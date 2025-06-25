import os
from openai import OpenAI

# Initialize OpenAI client
client = None
try:
    with open(os.path.join(os.path.dirname(__file__), 'key.txt'), 'r') as file:
        api_key = file.read().strip()
        client = OpenAI(api_key=api_key)
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    exit(1)

# Test the client
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Using a widely available model for testing
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is non-destructive testing?"}
        ],
        max_tokens=100
    )
    
    print("Response received:")
    print(response.choices[0].message.content)
    print("\nTest successful!")
except Exception as e:
    print(f"Error testing OpenAI client: {e}")
