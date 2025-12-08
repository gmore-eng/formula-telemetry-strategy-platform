import pandas as pd
import matplotlib.pyplot as plt

# ======================================
# LOAD BOTH DATASETS
# ======================================

SIM_PATH = "data/sim_racing/processed_rio_race_engineering.csv"
F1_PATH = "data/fastf1/processed_fastf1_race_engineering.csv"

sim_df = pd.read_csv(SIM_PATH)
f1_df = pd.read_csv(F1_PATH)

print("Loaded SIM data:", len(sim_df), "samples")
print("Loaded F1 data:", len(f1_df), "samples")

# ======================================
# FILTER SIM TO A SINGLE LAP (LAP 0)
# ======================================

sim_lap = sim_df[sim_df["lap"] == 0]

# ======================================
# NORMALIZE DISTANCE AXIS (0 → 1)
# This removes track-length differences
# ======================================

sim_dist_norm = sim_lap["distance_m"] / sim_lap["distance_m"].max()
f1_dist_norm = f1_df["distance_m"] / f1_df["distance_m"].max()

# ======================================
# EXTRACT ENGINEERING SIGNALS
# ======================================

sim_speed = sim_lap["speed"]
f1_speed = f1_df["speed"]

sim_accel = sim_lap["long_accel"]
f1_accel = f1_df["long_accel"]

# ======================================
# PLOT 1 — SPEED COMPARISON
# ======================================

plt.figure()
plt.plot(sim_dist_norm, sim_speed, label="SIM Speed")
plt.plot(f1_dist_norm, f1_speed, label="F1 Speed")

plt.xlabel("Normalized Distance (Lap %)")
plt.ylabel("Speed (km/h)")
plt.title("SIM vs F1 — Speed Comparison")
plt.legend()
plt.grid(True)
plt.show()

# ======================================
# PLOT 2 — ACCELERATION COMPARISON
# ======================================

plt.figure()
plt.plot(sim_dist_norm, sim_accel, label="SIM Acceleration")
plt.plot(f1_dist_norm, f1_accel, label="F1 Acceleration")

plt.xlabel("Normalized Distance (Lap %)")
plt.ylabel("Longitudinal Acceleration (m/s²)")
plt.title("SIM vs F1 — Acceleration Comparison")
plt.legend()
plt.grid(True)
plt.show()