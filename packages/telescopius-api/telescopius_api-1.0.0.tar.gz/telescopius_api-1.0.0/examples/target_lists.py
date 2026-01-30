"""Working with target lists example."""

import os

from telescopius import TelescopiusClient

api_key = os.environ.get("TELESCOPIUS_API_KEY")
if not api_key:
    print("Please set TELESCOPIUS_API_KEY environment variable")
    exit(1)

with TelescopiusClient(api_key=api_key) as client:
    # Get all user's target lists
    lists = client.get_target_lists()

    if not lists:
        print("No target lists found for this user.")
        print("Create some lists at https://telescopius.com to see them here!")
        exit(0)

    print(f"Found {len(lists)} target list(s)\n")
    print("-" * 40)

    for lst in lists:
        print(f"\nList: {lst['name']}")
        print(f"  ID: {lst['id']}")

        # Get details for this list with observation data
        details = client.get_target_list_by_id(
            lst["id"],
            lat=38.7223,
            lon=-9.1393,
            timezone="Europe/Lisbon",
        )

        targets = details.get("targets", [])
        print(f"  Targets: {len(targets)}")

        # Show first few targets
        for target in targets[:3]:
            name = target.get("main_name") or target.get("main_id", "Unknown")
            print(f"    - {name}")

        if len(targets) > 3:
            print(f"    ... and {len(targets) - 3} more")
