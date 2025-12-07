import pandas as pd
import numpy as np

# ======================================
# CONFIG
# ======================================

INPUT_PATH = "data/sim_racing/telemetry-rio-5-laps.csv"
OUTPUT_PATH = "data/sim_racing/processed_rio_race_engineering.csv"

# ======================================
# LOAD TELEMETRY
# ======================================

df = pd.read_csv(INPUT_PATH)

print("Loaded telemetry with", len(df), "samples")

# ======================================
# TIME BASE (seconds)
# ======================================

if "timestamp_ms" in df.columns:
    time = df["timestamp_ms"] / 1000.0
elif "current_race_time" in df.columns:
    time = df["current_race_time"]
else:
    time = np.arange(len(df)) * 0.01

# ======================================
# CORE SIGNALS (LOCKED TO YOUR DATASET)
# ======================================

speed = df["speed"]
brake = df["brake"]
rpm = df["current_engine_rpm"]
gear = df["gear"]
power = df["power"]
torque = df["torque"]
boost = df["boost"]

# ======================================
# TRUE LONGITUDINAL ACCELERATION
# ======================================

long_accel = df["acceleration_x"]

# ======================================
# WHEEL SPEED AVERAGE (VEHICLE SPEED ESTIMATE)
# ======================================

wheel_speed_avg = (
    df["wheel_rotation_speed_front_left"]
    + df["wheel_rotation_speed_front_right"]
    + df["wheel_rotation_speed_rear_left"]
    + df["wheel_rotation_speed_rear_right"]
) / 4.0

# ======================================
# TIRE SLIP & TRACTION LOSS
# ======================================

slip_avg = (
    df["tire_slip_rotation_front_left"]
    + df["tire_slip_rotation_front_right"]
    + df["tire_slip_rotation_rear_left"]
    + df["tire_slip_rotation_rear_right"]
) / 4.0

traction_loss = (slip_avg > 0.15).astype(int)

# ======================================
# TIRE TEMPERATURE DEGRADATION PROXY
# ======================================

tire_temp_avg = (
    df["tire_temp_front_left"]
    + df["tire_temp_front_right"]
    + df["tire_temp_rear_left"]
    + df["tire_temp_rear_right"]
) / 4.0

tire_temp_rate = np.gradient(tire_temp_avg, time)

# ======================================
# BRAKING ZONE DETECTION
# ======================================

brake_event = (brake > 5).astype(int)

# ======================================
# THROTTLE INTENT PROXY (USING POWER)
# ======================================

full_throttle_proxy = (power > power.quantile(0.85)).astype(int)

# ======================================
# GEAR SHIFT DETECTION
# ======================================

gear_shift = df["gear"].diff().fillna(0)

# ======================================
# POSITION & DISTANCE
# ======================================

distance = df["distance_traveled"]
lap = df["lap_number"]
race_pos = df["race_position"]

# ======================================
# BUILD ENGINEER-READY OUTPUT
# ======================================

proc = pd.DataFrame({
    "time_s": time,
    "lap": lap,
    "distance_m": distance,
    "speed": speed,
    "wheel_speed_avg": wheel_speed_avg,
    "long_accel": long_accel,
    "brake": brake,
    "brake_event": brake_event,
    "full_throttle_proxy": full_throttle_proxy,
    "gear": gear,
    "gear_shift": gear_shift,
    "rpm": rpm,
    "power": power,
    "torque": torque,
    "boost": boost,
    "tire_temp_avg": tire_temp_avg,
    "tire_temp_rate": tire_temp_rate,
    "tire_slip_avg": slip_avg,
    "traction_loss": traction_loss,
    "race_pos": race_pos
})

# ======================================
# SAVE OUTPUT
# ======================================

proc.to_csv(OUTPUT_PATH, index=False)

print("✅ Full race-engineering telemetry saved to:")
print(OUTPUT_PATH)

"""
WHAT THIS SCRIPT NOW DOES

| Feature             | What It Means in Racing            |
| ------------------- | ---------------------------------- |
| `long_accel`        | True longitudinal G-force          |
| `wheel_speed_avg`   | Vehicle speed estimate from wheels |
| `brake_event`       | Braking zone detection             |
| `full_throttle`     | Straight-line zones                |
| `gear_shift`        | Shift point detection              |
| `tire_temp_rate`    | Tire degradation proxy             |
| `tire_slip_avg`     | Grip loss                          |
| `traction_loss`     | Traction control indicators        |
| `lap`, `distance_m` | Lap delta & track positioning      |
| `race_pos`          | Strategy context                   |

"""