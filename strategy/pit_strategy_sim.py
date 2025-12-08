import pandas as pd
import numpy as np

# ======================================
# CONFIG
# ======================================

INPUT_PATH = "data/sim_racing/processed_rio_race_engineering.csv"

# Assume a hypothetical race length
TARGET_RACE_LAPS = 20

# Assume a fixed pit loss in seconds
PIT_LOSS_SECONDS = 20.0

# ======================================
# LOAD DATA
# ======================================

df = pd.read_csv(INPUT_PATH)
print(f"Loaded processed sim telemetry: {len(df)} samples")

if "lap" not in df.columns:
    raise ValueError("Expected a 'lap' column in the processed sim data.")

laps = sorted(df["lap"].unique())
print(f"Found laps in data: {laps}")

# ======================================
# PER-LAP METRICS
# ======================================

lap_stats = []

for lap_id in laps:
    lap_df = df[df["lap"] == lap_id]

    if len(lap_df) < 5:
        continue

    t_start = lap_df["time_s"].iloc[0]
    t_end = lap_df["time_s"].iloc[-1]
    lap_time = t_end - t_start

    avg_speed = lap_df["speed"].mean()
    avg_tire_temp = lap_df["tire_temp_avg"].mean()

    brake_density = lap_df["brake_event"].mean()
    high_slip_density = (lap_df["tire_slip_avg"].abs() > 0.15).mean()
    traction_loss_density = lap_df["traction_loss"].mean()

    tire_stress = (
        0.4 * brake_density +
        0.4 * high_slip_density +
        0.2 * traction_loss_density
    )

    lap_stats.append({
        "lap": lap_id,
        "lap_time_s": lap_time,
        "avg_speed": avg_speed,
        "avg_tire_temp": avg_tire_temp,
        "brake_density": brake_density,
        "high_slip_density": high_slip_density,
        "traction_loss_density": traction_loss_density,
        "tire_stress": tire_stress
    })

lap_stats_df = pd.DataFrame(lap_stats).sort_values("lap").reset_index(drop=True)

print("\n===== PER-LAP METRICS (SIM) =====")
print(lap_stats_df.to_string(index=False))

# ======================================
# SIMPLE TIRE DEGRADATION MODEL
# ======================================

if len(lap_stats_df) >= 3:
    x = lap_stats_df["lap"].values
    y = lap_stats_df["lap_time_s"].values

    coeffs = np.polyfit(x, y, deg=1)
    slope = coeffs[0]
    intercept = coeffs[1]

    print("\n===== DEGRADATION MODEL =====")
    print(f"Lap time ≈ {slope:.3f} * lap + {intercept:.3f}")
    print(f"Estimated degradation per lap: {slope:.3f} s/lap")
else:
    slope = 0.0
    print("\nNot enough laps to fit a degradation model. Using zero degradation.")

# ======================================
# HYPOTHETICAL 1-STOP STRATEGY MODEL
# ======================================

valid_laps = lap_stats_df["lap"].values
first_lap = int(valid_laps[0])
last_lap = int(valid_laps[-1])

stint_length_observed = len(valid_laps)
print(f"\nObserved stint length in data: {stint_length_observed} laps")

candidate_pit_laps = range(first_lap + 1, min(last_lap, TARGET_RACE_LAPS - 1) + 1)

strategy_rows = []

for pit_lap in candidate_pit_laps:
    laps_before_pit = pit_lap - first_lap
    laps_after_pit = TARGET_RACE_LAPS - laps_before_pit

    base_lap_time = lap_stats_df["lap_time_s"].iloc[0]

    times_before = [
        base_lap_time + slope * max(0, (first_lap + i) - first_lap)
        for i in range(laps_before_pit)
    ]

    times_after = [
        base_lap_time + slope * max(0, i)
        for i in range(laps_after_pit)
    ]

    total_race_time = sum(times_before) + PIT_LOSS_SECONDS + sum(times_after)

    strategy_rows.append({
        "pit_lap": pit_lap,
        "laps_before_pit": laps_before_pit,
        "laps_after_pit": laps_after_pit,
        "total_race_time_s": total_race_time
    })

strategy_df = pd.DataFrame(strategy_rows)

if not strategy_df.empty:
    best_row = strategy_df.loc[strategy_df["total_race_time_s"].idxmin()]

    print("\n===== 1-STOP PIT STRATEGY ESTIMATE (SIM) =====")
    print(strategy_df.to_string(index=False))

    print("\n===== RECOMMENDED PIT WINDOW (SIMPLE MODEL) =====")
    print(f"Hypothetical race length: {TARGET_RACE_LAPS} laps")
    print(f"Assumed pit loss: {PIT_LOSS_SECONDS:.1f} s")

    print(f"\nBest pit lap (1-stop): Lap {int(best_row['pit_lap'])}")
    print(f"Estimated total race time: {best_row['total_race_time_s']:.2f} s")
else:
    print("\nNot enough laps or candidate pit laps to compute strategy.")
