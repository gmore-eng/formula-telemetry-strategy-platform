import pandas as pd
import matplotlib.pyplot as plt

# ======================================
# LOAD PROCESSED TELEMETRY
# ======================================

DATA_PATH = "data/sim_racing/processed_rio_race_engineering.csv"
df = pd.read_csv(DATA_PATH)

print("Loaded processed telemetry:", len(df), "samples")

# ======================================
# SELECT LAPS TO COMPARE
# ======================================

laps_to_compare = [0, 1, 2]
lap_data = df[df["lap"].isin(laps_to_compare)]

# ======================================
# PLOT 1 — SPEED VS DISTANCE (MULTI-LAP)
# ======================================

plt.figure()

for lap in laps_to_compare:
    lap_df = lap_data[lap_data["lap"] == lap]
    plt.plot(lap_df["distance_m"], lap_df["speed"], label=f"Lap {lap}")

plt.xlabel("Distance (m)")
plt.ylabel("Speed")
plt.title("Multi-Lap Speed Comparison")
plt.legend()
plt.grid(True)
plt.show()

# ======================================
# PLOT 2 — BRAKING ZONES (MULTI-LAP)
# ======================================

plt.figure()

for lap in laps_to_compare:
    lap_df = lap_data[lap_data["lap"] == lap]
    braking_points = lap_df[lap_df["brake_event"] == 1]

    plt.scatter(
        braking_points["distance_m"],
        braking_points["speed"],
        label=f"Lap {lap}",
        s=8
    )

plt.xlabel("Distance (m)")
plt.ylabel("Speed at Braking")
plt.title("Braking Zones Comparison (All Laps)")
plt.legend()
plt.grid(True)
plt.show()

# ======================================
# PLOT 3 — ACCELERATION VS DISTANCE (MULTI-LAP)
# ======================================

plt.figure()

for lap in laps_to_compare:
    lap_df = lap_data[lap_data["lap"] == lap]
    plt.plot(
        lap_df["distance_m"],
        lap_df["long_accel"],
        label=f"Lap {lap}"
    )

plt.xlabel("Distance (m)")
plt.ylabel("Longitudinal Acceleration")
plt.title("Multi-Lap Acceleration Comparison")
plt.legend()
plt.grid(True)
plt.show()

"""
Plot 1 — Speed vs Distance (Multi-Lap)
You’ll see:
- 3 overlaid speed traces
- You can instantly spot:
- Earlier braking
- Higher exit speeds
- Lift-off differences
This is how engineers evaluate lap improvement.

Plot 2 — Braking Zones Overlay
You’ll see:
- Clusters of braking points at corner entries
- If Lap 1 brakes earlier than Lap 0 → confidence change
- If Lap 2 brakes later → riskier driving
This is driver behavior analysis.

Plot 3 — Acceleration vs Distance
You’ll see:
- Exit acceleration quality
- Throttle pickup aggression (via power + accel proxy)
- Traction limitation zones
This shows car balance and grip phase usage.
"""