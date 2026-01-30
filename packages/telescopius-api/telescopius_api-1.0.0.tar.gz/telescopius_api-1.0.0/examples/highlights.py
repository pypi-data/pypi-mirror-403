"""Get tonight's highlights example."""

import os

from telescopius import TelescopiusClient

api_key = os.environ.get("TELESCOPIUS_API_KEY")
if not api_key:
    print("Please set TELESCOPIUS_API_KEY environment variable")
    exit(1)

with TelescopiusClient(api_key=api_key) as client:
    # Get popular targets best seen from New York tonight
    highlights = client.get_target_highlights(
        lat=40.7128,
        lon=-74.0060,
        timezone="America/New_York",
        min_alt=20,
    )

    print(f"Tonight's Highlights ({highlights['matched']} targets)\n")
    print("-" * 50)

    for item in highlights["page_results"]:
        obj = item["object"]
        name = obj.get("main_name") or obj["main_id"]
        obj_type = ", ".join(obj.get("types", [])[:2])

        print(f"  {name} ({obj_type})")

        if "tonight_times" in item:
            times = item["tonight_times"]
            print(f"    Best at: {times.get('transit')}")
        print()
