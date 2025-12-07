import fastf1
import pandas as pd

# Enable caching so downloads are fast after the first time
fastf1.Cache.enable_cache("data/fastf1")

# Load a real F1 session: 2023 Bahrain Grand Prix - Race
session = fastf1.get_session(2023, "Bahrain", "R")
session.load()

# Pick a driver (example: Verstappen)
driver = "VER"
laps = session.laps.pick_driver(driver)

# Grab telemetry from the fastest lap
fastest_lap = laps.pick_fastest()
telemetry = fastest_lap.get_telemetry()

# Keep only signals we care about
df = telemetry[[
    "Time", "Speed", "Throttle", "Brake", "RPM", "nGear", "DRS", "X", "Y"
]]

# Save to CSV for your project pipeline
output_path = "data/fastf1/bahrain_2023_verstappen.csv"
df.to_csv(output_path, index=False)

print(f"Saved telemetry to {output_path}")