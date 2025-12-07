import pandas as pd
import matplotlib.pyplot as plt

# ======================================
# LOAD PROCESSED RACE TELEMETRY
# ======================================

DATA_PATH = "data/sim_racing/processed_rio_race_engineering.csv"
df = pd.read_csv(DATA_PATH)

print("Loaded processed telemetry:", len(df), "samples")

# ======================================
# FILTER TO A SINGLE LAP (START WITH LAP 0)
# ======================================

lap_to_plot = 0
lap_df = df[df["lap"] == lap_to_plot]

print("Samples in lap:", len(lap_df))

distance = lap_df["distance_m"]
speed = lap_df["speed"]
brake = lap_df["brake"]
brake_event = lap_df["brake_event"]
long_accel = lap_df["long_accel"]

# ======================================
# PLOT 1 — SPEED VS DISTANCE WITH BRAKING
# ======================================

plt.figure()
plt.plot(distance, speed)

# Overlay braking zones
braking_points = lap_df[brake_event == 1]
plt.scatter(braking_points["distance_m"], braking_points["speed"])

plt.xlabel("Distance (m)")
plt.ylabel("Speed")
plt.title("Speed vs Distance with Braking Zones (Lap 0)")
plt.grid(True)
plt.show()

# ======================================
# PLOT 2 — LONGITUDINAL ACCELERATION VS DISTANCE
# ======================================

plt.figure()
plt.plot(distance, long_accel)

plt.xlabel("Distance (m)")
plt.ylabel("Longitudinal Acceleration")
plt.title("Acceleration vs Distance (Lap 0)")
plt.grid(True)
plt.show()