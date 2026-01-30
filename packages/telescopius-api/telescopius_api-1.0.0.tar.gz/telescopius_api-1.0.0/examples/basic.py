"""Basic usage example - get quote of the day."""

import os

from telescopius import TelescopiusClient

# Get API key from environment variable
api_key = os.environ.get("TELESCOPIUS_API_KEY")
if not api_key:
    print("Please set TELESCOPIUS_API_KEY environment variable")
    exit(1)

# Using context manager (recommended)
with TelescopiusClient(api_key=api_key) as client:
    quote = client.get_quote_of_the_day()
    print(f'"{quote["text"]}"')
    print(f"  - {quote['author']}")
