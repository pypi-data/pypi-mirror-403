"""Find objects by name example."""

import os

from telescopius import TelescopiusClient

api_key = os.environ.get("TELESCOPIUS_API_KEY")
if not api_key:
    print("Please set TELESCOPIUS_API_KEY environment variable")
    exit(1)

with TelescopiusClient(api_key=api_key) as client:
    # Search for the Orion Nebula
    results = client.search_targets(
        name="Orion Nebula",
        lat=38.7223,
        lon=-9.1393,
        timezone="Europe/Lisbon",
    )

    print(f"Found {results['matched']} objects matching 'Orion Nebula'\n")

    for item in results["page_results"]:
        obj = item["object"]
        print(f"Name: {obj.get('main_name') or obj['main_id']}")
        print(f"  IDs: {', '.join(obj.get('ids', [])[:5])}")
        print(f"  Type: {', '.join(obj.get('types', []))}")
        print(f"  Constellation: {obj.get('con_name')}")
        print(f"  RA: {obj.get('ra')}h, Dec: {obj.get('dec')}°")
        print(f"  Magnitude: {obj.get('visual_mag')}")
        print()
