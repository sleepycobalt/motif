import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic()

resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=200,
    messages=[{"role": "user", "content": "Reply with one sentence confirming the API works."}],
)
print(resp.content[0].text)
print("tokens in/out:", resp.usage.input_tokens, resp.usage.output_tokens)
