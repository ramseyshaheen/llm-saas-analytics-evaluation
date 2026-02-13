import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

# Create Claude client using API key
client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Send test message
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=50,
    messages=[
        {
            "role": "user",
            "content": "Reply with exactly the word: connected"
        }
    ]
)

print(response.content[0].text)
