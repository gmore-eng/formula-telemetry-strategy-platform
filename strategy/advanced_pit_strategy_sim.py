import pandas as pd
import numpy as np

# ======================================
# CONFIG
# ======================================

INPUT_PATH = "data/sim_racing/processed_rio_race_engineering.csv"

TARGET_RACE_LAPS = 20           # hypothetical race length
PIT_LOSS_SECONDS = 20.0         # fixed pit loss

WARMUP_LAPS = 1                 # laps dominated by warm-up / driver adaptation

COMPOUNDS = {
    "Soft": {
        "deg_mult": 1.3,        # degrades faster
        "base_offset": -1.0     # slightly faster when fresh
    },
    "Medium": {
        "deg_mult": 1.0,
        "base_offset": 0.0
    },
    "Hard": {
        "deg_mult": 0.7,        # more durable
        "base_offset": +1.0     # slightly slower when fresh
    }
}

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
# PER-LAP METRICS (STINT ANALYSIS)
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
# WARM-UP PHASE + TRUE DEGRADATION MODEL
# ======================================

if len(lap_stats_df) >= 3:
    # Treat first WARMUP_LAPS as dominated by warm-up / driver adaptation
    warmup_mask = lap_stats_df["lap"] < (lap_stats_df["lap"].min() + WARMUP_LAPS)
    deg_mask = ~warmup_mask

    if deg_mask.sum() >= 2:
        x = lap_stats_df.loc[deg_mask, "lap"].values
        y = lap_stats_df.loc[deg_mask, "lap_time_s"].values

        coeffs = np.polyfit(x, y, deg=1)
        raw_slope = coeffs[0]
        intercept = coeffs[1]
    else:
        raw_slope = 0.0
        intercept = lap_stats_df["lap_time_s"].iloc[0]
else:
    raw_slope = 0.0
    intercept = lap_stats_df["lap_time_s"].iloc[0]

# If raw_slope is negative, that means improvement, not degradation
if raw_slope < 0:
    print("\nNOTE: Negative raw slope detected (laps getting faster).")
    print("Interpreting this as warm-up / learning phase rather than degradation.")
    # Use a small positive base degradation to reflect long-run reality
    base_deg = 0.05
else:
    base_deg = raw_slope

# Stress-driven scaling: higher average tire stress → faster degradation
mean_stress = lap_stats_df["tire_stress"].mean()
max_stress = lap_stats_df["tire_stress"].max()
if max_stress > 0:
    stress_norm = mean_stress / max_stress
else:
    stress_norm = 0.5  # fallback

# Effective base degradation per lap (s/lap)
effective_base_deg = base_deg * (0.5 + stress_norm)  # scale between ~0.5x and ~1.5x

print("\n===== DEGREDATION MODEL (ADVANCED) =====")
print(f"Raw slope from degradation laps: {raw_slope:.4f} s/lap")
print(f"Mean tire stress: {mean_stress:.4f} (normalized factor: {stress_norm:.3f})")
print(f"Effective base degradation per lap: {effective_base_deg:.4f} s/lap")
print(f"Warm-up laps treated separately: first {WARMUP_LAPS} lap(s)")

# Base lap time from first non-warmup lap
base_ref_row = lap_stats_df.iloc[min(WARMUP_LAPS, len(lap_stats_df)-1)]
base_lap_time = base_ref_row["lap_time_s"]

print(f"\nReference base lap time (post-warmup): {base_lap_time:.3f} s")

# ======================================
# STRATEGY SIMULATION HELPERS
# ======================================

def simulate_stint(stint_laps: int, compound_name: str) -> float:
    """
    Simulate one stint: tire starts 'fresh' and degrades each lap.
    """
    compound = COMPOUNDS[compound_name]
    deg = effective_base_deg * compound["deg_mult"]
    offset = compound["base_offset"]

    total = 0.0
    for i in range(stint_laps):
        lap_time = base_lap_time + offset + deg * i
        total += lap_time
    return total

def simulate_strategy(stints, pit_loss=PIT_LOSS_SECONDS):
    """
    stints: list of dicts like:
      {"laps": 7, "compound": "Soft"}
    """
    total_time = 0.0
    total_laps = 0
    desc_parts = []

    for idx, stint in enumerate(stints):
        laps = stint["laps"]
        comp = stint["compound"]
        total_laps += laps

        stint_time = simulate_stint(laps, comp)
        total_time += stint_time

        desc_parts.append(f"{laps}L on {comp}")

        # Add pit stop time between stints (but not after final stint)
        if idx < len(stints) - 1:
            total_time += pit_loss

    return total_laps, total_time, " | ".join(desc_parts)

# ======================================
# DEFINE CANDIDATE STRATEGIES
# ======================================

strategies = []

# 0-stop: entire race on Medium
strategies.append({
    "name": "0-stop: Full Medium",
    "stints": [
        {"laps": TARGET_RACE_LAPS, "compound": "Medium"}
    ]
})

# 1-stop: Soft -> Hard (split race)
strategies.append({
    "name": "1-stop: Soft → Hard",
    "stints": [
        {"laps": TARGET_RACE_LAPS // 2, "compound": "Soft"},
        {"laps": TARGET_RACE_LAPS - TARGET_RACE_LAPS // 2, "compound": "Hard"}
    ]
})

# 2-stop: Soft → Medium → Hard
strategies.append({
    "name": "2-stop: Soft → Medium → Hard",
    "stints": [
        {"laps": 7, "compound": "Soft"},
        {"laps": 7, "compound": "Medium"},
        {"laps": TARGET_RACE_LAPS - 14, "compound": "Hard"}
    ]
})

# ======================================
# EVALUATE STRATEGIES
# ======================================

strategy_rows = []

for strat in strategies:
    laps_covered, total_time, desc = simulate_strategy(strat["stints"], PIT_LOSS_SECONDS)

    if laps_covered != TARGET_RACE_LAPS:
        print(f"WARNING: Strategy '{strat['name']}' only covers {laps_covered} laps (target {TARGET_RACE_LAPS}).")

    strategy_rows.append({
        "strategy": strat["name"],
        "stints": desc,
        "total_time_s": total_time
    })

strategy_df = pd.DataFrame(strategy_rows).sort_values("total_time_s").reset_index(drop=True)

print("\n===== MULTI-STRATEGY COMPARISON (SIM) =====")
print(strategy_df.to_string(index=False))

best_row = strategy_df.iloc[0]
print("\n===== RECOMMENDED STRATEGY (ADVANCED MODEL) =====")
print(f"Target race length: {TARGET_RACE_LAPS} laps")
print(f"Assumed pit loss: {PIT_LOSS_SECONDS:.1f} s")
print(f"\nBest strategy: {best_row['strategy']}")
print(f"Stints: {best_row['stints']}")
print(f"Estimated total race time: {best_row['total_time_s']:.2f} s")