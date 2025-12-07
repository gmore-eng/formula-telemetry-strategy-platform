import pandas as pd
import numpy as np

# ======================================
# CONFIG
# ======================================

INPUT_PATH = "data/fastf1/bahrain_2023_verstappen.csv"
OUTPUT_PATH = "data/fastf1/processed_fastf1_race_engineering.csv"

# ======================================
# LOAD FASTF1 TELEMETRY
# ======================================

df = pd.read_csv(INPUT_PATH)

print("Loaded FastF1 telemetry with", len(df), "samples")
print("Columns:", df.columns.tolist())

# ======================================
# TIME BASE (seconds)
# ======================================

# FastF1 Time column is usually a timedelta string or numeric
if df["Time"].dtype == object:
    time = pd.to_timedelta(df["Time"]).dt.total_seconds()
else:
    time = df["Time"]

# Normalize time to start at 0
time = time - time.iloc[0]

# ======================================
# CORE SIGNALS
# ======================================

speed = df["Speed"]                 # km/h
throttle = df["Throttle"]           # %
brake = df["Brake"]                 # True/False or 0/1
rpm = df["RPM"]                     # engine RPM
gear = df["nGear"]                  # gear number
drs = df["DRS"]                     # DRS state (0/1)

# ======================================
# DERIVED LONGITUDINAL ACCELERATION
# ======================================

speed_ms = speed / 3.6
long_accel = np.gradient(speed_ms, time)

# ======================================
# BRAKING ZONE DETECTION
# ======================================

# If Brake is boolean, convert to int
if brake.dtype == bool:
    brake_event = brake.astype(int)
else:
    brake_event = (brake > 0).astype(int)

# ======================================
# FULL THROTTLE DETECTION
# ======================================

full_throttle = (throttle > 95).astype(int)

# ======================================
# GEAR SHIFT DETECTION
# ======================================

gear_shift = gear.diff().fillna(0)

# ======================================
# TRACK DISTANCE (RECONSTRUCTED)
# ======================================

# Approximate distance by integrating speed over time
distance_m = np.cumsum(speed_ms * np.gradient(time))

# Normalize to start at 0
distance_m = distance_m - distance_m.iloc[0]

# ======================================
# BUILD ENGINEER-READY OUTPUT
# ======================================

proc = pd.DataFrame({
    "time_s": time,
    "distance_m": distance_m,
    "speed": speed,
    "long_accel": long_accel,
    "throttle": throttle,
    "full_throttle": full_throttle,
    "brake": brake_event,
    "gear": gear,
    "gear_shift": gear_shift,
    "rpm": rpm,
    "drs": drs
})

# ======================================
# PREVIEW IN TERMINAL (CLEAN)
# ======================================

print("\n===== SAMPLE FASTF1 PROCESSED OUTPUT =====")
print(proc.head(10).to_string(index=False))

# ======================================
# SAVE OUTPUT
# ======================================

proc.to_csv(OUTPUT_PATH, index=False)

print("\n✅ Processed FastF1 telemetry saved to:")
print(OUTPUT_PATH)