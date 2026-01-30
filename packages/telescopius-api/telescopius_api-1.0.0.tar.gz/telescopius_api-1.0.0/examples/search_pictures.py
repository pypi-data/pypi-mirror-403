"""Search for astrophotography pictures example."""

import os

from telescopius import TelescopiusClient

api_key = os.environ.get("TELESCOPIUS_API_KEY")
if not api_key:
    print("Please set TELESCOPIUS_API_KEY environment variable")
    exit(1)

with TelescopiusClient(api_key=api_key) as client:
    # Get featured astrophotography pictures
    pictures = client.search_pictures(
        order="is_featured",
        results_per_page=10,
    )

    print("Featured Astrophotography Pictures\n")
    print("=" * 50)

    for pic in pictures.get("results", []):
        print(f"\n  {pic.get('title', 'Untitled')}")
        print(f"    By: {pic.get('username', 'Unknown')}")
        if pic.get("url"):
            print(f"    URL: https://telescopius.com{pic['url']}")
