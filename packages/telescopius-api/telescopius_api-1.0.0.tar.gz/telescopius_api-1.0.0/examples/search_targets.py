"""Search for astronomical targets example."""

import os

from telescopius import TelescopiusClient

api_key = os.environ.get("TELESCOPIUS_API_KEY")
if not api_key:
    print("Please set TELESCOPIUS_API_KEY environment variable")
    exit(1)

with TelescopiusClient(api_key=api_key) as client:
    # Search for galaxies and emission nebulae visible from Lisbon
    results = client.search_targets(
        lat=38.7223,
        lon=-9.1393,
        timezone="Europe/Lisbon",
        types="GXY,ENEB",
        min_alt=30,  # At least 30 degrees above horizon
        mag_max=10,  # Brighter than magnitude 10
        results_per_page=10,
    )

    print(f"Found {results['matched']} objects matching criteria\n")

    for item in results["page_results"]:
        obj = item["object"]
        name = obj.get("main_name") or obj["main_id"]
        mag = obj.get("visual_mag", "N/A")
        constellation = obj.get("con_name", "Unknown")

        print(f"  {name}")
        print(f"    Magnitude: {mag}")
        print(f"    Constellation: {constellation}")

        if "tonight_times" in item:
            times = item["tonight_times"]
            print(f"    Rise: {times.get('rise')} | Transit: {times.get('transit')} | Set: {times.get('set')}")
        print()
