"""Get solar system times example."""

import os

from telescopius import TelescopiusClient

api_key = os.environ.get("TELESCOPIUS_API_KEY")
if not api_key:
    print("Please set TELESCOPIUS_API_KEY environment variable")
    exit(1)

with TelescopiusClient(api_key=api_key) as client:
    # Get Sun, Moon, and planet times for Tokyo
    times = client.get_solar_system_times(
        lat=35.6762,
        lon=139.6503,
        timezone="Asia/Tokyo",
    )

    print("Solar System Times for Tokyo\n")
    print("=" * 40)

    # Sun times
    sun = times.get("sun", {})
    print("\nSun:")
    print(f"  Rise: {sun.get('rise')}")
    print(f"  Transit: {sun.get('transit')}")
    print(f"  Set: {sun.get('set')}")

    # Moon times
    moon = times.get("moon", {})
    print("\nMoon:")
    print(f"  Rise: {moon.get('rise')}")
    print(f"  Transit: {moon.get('transit')}")
    print(f"  Set: {moon.get('set')}")
    print(f"  Phase: {moon.get('phase')}")
    print(f"  Illumination: {moon.get('illumination', 0) * 100:.1f}%")

    # Planets
    planets = ["mercury", "venus", "mars", "jupiter", "saturn"]
    print("\nPlanets:")
    for planet in planets:
        data = times.get(planet, {})
        if data:
            print(f"  {planet.capitalize()}: Rise {data.get('rise')} | Set {data.get('set')}")
