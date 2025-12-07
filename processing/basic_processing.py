import pandas as pd
import numpy as np

# ==========================
# CONFIG
# ==========================
INPUT_PATH = "data/sim_racing/telemetry-rio-5-laps.csv"
OUTPUT_PATH = "data/sim_racing/processed_rio.csv"

# ==========================
# LOAD TELEMETRY
# ==========================
df = pd.read_csv(INPUT_PATH)

print("Loaded telemetry with columns:")
print(df.columns.tolist())
print("\nTotal samples:", len(df))

# ==========================
# BASIC NORMALIZATION
# ==========================
# Try to auto-detect common racing signal names
column_map = {
    "speed": ["Speed", "speed", "Velocity", "velocity"],
    "throttle": ["Throttle", "throttle", "ThrottlePos"],
    "brake": ["Brake", "brake", "BrakePressure"],
    "rpm": ["RPM", "rpm", "EngineRPM"],
    "gear": ["Gear", "gear", "nGear"]
}

normalized = {}

for key, aliases in column_map.items():
    found = False
    for col in aliases:
        if col in df.columns:
            normalized[key] = df[col]
            found = True
            break
    if not found:
        print(f"WARNING: Could not find column for {key}")

# Build normalized dataframe
proc = pd.DataFrame(normalized)

# ==========================
# TIME BASE (IF MISSING)
# ==========================
if "Time" in df.columns:
    proc["time"] = df["Time"]
else:
    # Assume 100 Hz sample rate if time is missing
    proc["time"] = np.arange(len(proc)) * 0.01

# ==========================
# DERIVED SIGNALS
# ==========================

# Acceleration (m/s^2)
if "speed" in proc.columns:
    speed_ms = proc["speed"] / 3.6
    proc["accel"] = np.gradient(speed_ms, proc["time"])
else:
    proc["accel"] = 0

# Brake events (binary)
if "brake" in proc.columns:
    proc["brake_event"] = (proc["brake"] > 5).astype(int)
else:
    proc["brake_event"] = 0

# Throttle zones
if "throttle" in proc.columns:
    proc["full_throttle"] = (proc["throttle"] > 95).astype(int)
else:
    proc["full_throttle"] = 0

# Gear shift detection
if "gear" in proc.columns:
    proc["gear_shift"] = proc["gear"].diff().fillna(0)
else:
    proc["gear_shift"] = 0

# ==========================
# SAVE PROCESSED TELEMETRY
# ==========================
proc.to_csv(OUTPUT_PATH, index=False)
print(f"\nProcessed telemetry saved to: {OUTPUT_PATH}")

"""
WHAT THIS FILE IS DOING (IN RACE TERMS)

| Code Section     | What It Means in Racing                             |
| ---------------- | --------------------------------------------------- |
| Column detection | Adapts automatically to different telemetry formats |
| Time base        | Builds a proper sampling timeline                   |
| Acceleration     | Detects corner entry & exit force                   |
| Brake events     | Detects braking zones                               |
| Full throttle    | Detects straights                                   |
| Gear shifts      | Detects upshifts/downshifts                         |
| Output CSV       | Clean engineer-ready telemetry                      |

"""