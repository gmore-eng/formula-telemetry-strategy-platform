import pandas as pd
import matplotlib.pyplot as plt

# ======================================
# LOAD PROCESSED FASTF1 TELEMETRY
# ======================================

DATA_PATH = "data/fastf1/processed_fastf1_race_engineering.csv"
df = pd.read_csv(DATA_PATH)

print("Loaded processed FastF1 telemetry:", len(df), "samples")

# ======================================
# BASIC SANITY CHECK
# ======================================

print("\nColumns:")
print(df.columns.tolist())

# ======================================
# EXTRACT ENGINEERING SIGNALS
# ======================================

distance = df["distance_m"]
speed = df["speed"]
long_accel = df["long_accel"]
brake_event = df["brake"]
full_throttle = df["full_throttle"]

# ======================================
# PLOT 1 — SPEED VS DISTANCE WITH BRAKING ZONES
# ======================================

plt.figure()
plt.plot(distance, speed, label="Speed")

# Overlay braking points
braking_points = df[brake_event == 1]
plt.scatter(
    braking_points["distance_m"],
    braking_points["speed"],
    label="Braking Zones",
    s=10
)

plt.xlabel("Distance (m)")
plt.ylabel("Speed (km/h)")
plt.title("FastF1 — Speed vs Distance with Braking Zones")
plt.legend()
plt.grid(True)
plt.show()

# ======================================
# PLOT 2 — LONGITUDINAL ACCELERATION VS DISTANCE
# ======================================

plt.figure()
plt.plot(distance, long_accel, label="Longitudinal Acceleration")

plt.xlabel("Distance (m)")
plt.ylabel("Acceleration (m/s²)")
plt.title("FastF1 — Acceleration vs Distance")
plt.legend()
plt.grid(True)
plt.show()

# ======================================
# OPTIONAL — FULL THROTTLE PHASE OVERLAY
# ======================================

plt.figure()
plt.scatter(
    df[full_throttle == 1]["distance_m"],
    df[full_throttle == 1]["speed"],
    s=5,
    label="Full Throttle"
)

plt.xlabel("Distance (m)")
plt.ylabel("Speed (km/h)")
plt.title("FastF1 — Full Throttle Zones")
plt.legend()
plt.grid(True)
plt.show()