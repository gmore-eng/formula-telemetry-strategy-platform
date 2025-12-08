import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.animation import FuncAnimation
import tkinter as tk
import matplotlib.gridspec as gridspec

def speed_to_color(speed, min_speed=0, max_speed=350):
    """Map speed to RGB color (blue → yellow → red)."""
    ratio = (speed - min_speed) / (max_speed - min_speed)
    ratio = np.clip(ratio, 0, 1)

    if ratio < 0.5:
        # Blue → Yellow
        r = ratio * 2
        g = ratio * 2
        b = 1 - ratio * 2
    else:
        # Yellow → Red
        r = 1
        g = 1 - (ratio - 0.5) * 2
        b = 0

    return (r, g, b)

# =====================================================
# CONFIG
# =====================================================

INPUT_PATH = "data/fastf1/bahrain_2023_verstappen.csv"

# How much to downsample for smoother UI (1 = use all points)
DOWNSAMPLE = 5

# =====================================================
# LOAD RAW FASTF1 TELEMETRY (WITH X/Y)
# =====================================================

df = pd.read_csv(INPUT_PATH)
print("Loaded FastF1 telemetry:", len(df), "samples")
print("Columns:", df.columns.tolist())

# We expect at least: Time, X, Y, Speed, Throttle, Brake
required_cols = ["Time", "X", "Y", "Speed", "Throttle", "Brake"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns in FastF1 CSV: {missing}")

# Handle Time column (can be string timedelta or numeric)
if df["Time"].dtype == object:
    time_s = pd.to_timedelta(df["Time"]).dt.total_seconds()
else:
    time_s = df["Time"].astype(float)

time_s = time_s - time_s.iloc[0]

# Downsample for performance
df_ds = df.iloc[::DOWNSAMPLE].reset_index(drop=True)
time_ds = time_s.iloc[::DOWNSAMPLE].reset_index(drop=True)

x = df_ds["X"].values
y = df_ds["Y"].values
speed = df_ds["Speed"].values
throttle = df_ds["Throttle"].values
brake = df_ds["Brake"].values

gear = df_ds["nGear"].values
rpm = df_ds["RPM"].values

n_samples = len(df_ds)
print("Using", n_samples, "samples after downsampling")

# =========================================
# AUTO-FIT FIGURE TO SCREEN SIZE
# =========================================

root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()

# Convert pixels → inches (assuming ~100 DPI)
fig_width = screen_width / 110
fig_height = (screen_height * 0.85) / 110  # leave room for taskbar

fig = plt.figure(figsize=(fig_width, fig_height))
gs = gridspec.GridSpec(
    2, 1,
    height_ratios=[12, 2],   # Top = plot, Bottom = controls
    hspace=0.05
)

ax = fig.add_subplot(gs[0])

# Plot full track colored by speed (faint background)
track = ax.scatter(x, y, c=speed, cmap="viridis", s=5, alpha=0.4)
cbar = fig.colorbar(track, ax=ax, fraction=0.025, pad=0.02)
cbar.set_label("Speed (km/h)")

# Store full track bounds for overview mode
x_range = x.max() - x.min()
y_range = y.max() - y.min()
PADDING = 0.05 * max(x_range, y_range)  # 5% padding

TRACK_X_MIN, TRACK_X_MAX = x.min() - PADDING, x.max() + PADDING
TRACK_Y_MIN, TRACK_Y_MAX = y.min() - PADDING, y.max() + PADDING

# Current car position (big dot)
current_point, = ax.plot(
    [x[0]],
    [y[0]],
    marker="o",
    markersize=14,
    color="red",
    markeredgecolor="black",
    markeredgewidth=2
)

ax.set_aspect("equal", adjustable="datalim")
ax.set_title("FastF1 Track Replay")
ax.set_xlabel("X position")
ax.set_ylabel("Y position")
ax.grid(True)

camera_follow_enabled = False

# Camera follow window size (meters)
CAMERA_RANGE = 400

# =====================================================
# INFO TEXT BOX
# =====================================================

info_text = ax.text(
    0.02,
    0.98,
    "",
    transform=ax.transAxes,
    va="top",
    ha="left",
    fontsize=10,
    bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7),
)

# Floating drivetrain label near the car
drivetrain_text = ax.text(
    x[0], y[0],
    "",
    fontsize=10,
    color="black",
    ha="left",
    va="bottom",
    bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.85)
)

# Bottom UI area
ui_ax = fig.add_subplot(gs[1])
ui_ax.axis("off")

# Slider
slider_ax = fig.add_axes([0.1, 0.08, 0.8, 0.03])
frame_slider = Slider(
    ax=slider_ax,
    label="Replay Position",
    valmin=0,
    valmax=n_samples - 1,
    valinit=0,
)

def update(frame_val):
    """Update car position and info when slider moves."""
    idx = int(frame_val)
    idx = max(0, min(n_samples - 1, idx))

    cx = x[idx]
    cy = y[idx]
    cspeed = speed[idx]
    cthrottle = throttle[idx]
    cbrake = brake[idx]
    t = time_ds[idx]
    
    # =========================
    # CAMERA MODE
    # =========================

    if camera_follow_enabled:
        ax.set_xlim(cx - CAMERA_RANGE, cx + CAMERA_RANGE)
        ax.set_ylim(cy - CAMERA_RANGE, cy + CAMERA_RANGE)
    else:
        ax.set_xlim(TRACK_X_MIN, TRACK_X_MAX)
        ax.set_ylim(TRACK_Y_MIN, TRACK_Y_MAX)

    # Move car marker
    current_point.set_data([cx], [cy])
    current_point.set_markersize(8 + cspeed / 40)

    # =========================
    # CAR HEAT COLORING (SPEED BASED)
    # =========================

    if cbrake > 0:
        # Braking overrides everything
        current_point.set_color("red")
    else:
        heat_color = speed_to_color(cspeed)
        current_point.set_color(heat_color)

    # Update corner info box
    info_text.set_text(
        f"t = {t:6.2f} s\n"
        f"Speed = {cspeed:6.1f} km/h\n"
        f"Throttle = {cthrottle:5.1f}\n"
        f"Brake = {cbrake}"
    )

    # =========================
    # GEAR + RPM OVERLAY (NEAR CAR)
    # =========================

    current_gear = int(gear[idx])
    current_rpm = int(rpm[idx])

    # Slight offset so it doesn't overlap the dot
    label_offset_x = 80
    label_offset_y = 80

    drivetrain_text.set_position((cx + label_offset_x, cy + label_offset_y))
    drivetrain_text.set_text(
        f"G: {current_gear}\nRPM: {current_rpm:,}"
    )

    fig.canvas.draw_idle()

# =====================================================
# PLAY ANIMATION
# =====================================================

is_playing = False

def play_animation(frame):
    global is_playing, ani

    if not is_playing:
        return

    # Get playback speed (0.25x → 5x)
    speed_factor = speed_slider.val

    # Dynamically adjust animation interval (smaller = faster)
    interval_ms = int(40 / speed_factor)
    interval_ms = max(5, interval_ms)  # safety clamp

    # Update animation timer speed LIVE
    ani.event_source.interval = interval_ms

    current = int(frame_slider.val)
    next_frame = current + 1

    if next_frame >= n_samples:
        is_playing = False
        play_button.label.set_text("▶ Play")
        return

    frame_slider.set_val(next_frame)

# Play button
play_ax = fig.add_axes([0.35, 0.025, 0.12, 0.04])
play_button = plt.Button(play_ax, "▶ Play")

# Camera mode toggle button
cam_ax = fig.add_axes([0.75, 0.025, 0.2, 0.04])
cam_button = plt.Button(cam_ax, "Follow Cam: ON")

def toggle_camera(event):
    global camera_follow_enabled
    camera_follow_enabled = not camera_follow_enabled
    cam_button.label.set_text(
        "Follow Cam: ON" if camera_follow_enabled else "🗺️ Overview Cam"
    )
    update(frame_slider.val)

# Speed control slider
speed_ax = fig.add_axes([0.1, 0.005, 0.8, 0.02])
speed_slider = Slider(
    ax=speed_ax,
    label="Playback Speed",
    valmin=0.25,
    valmax=5.0,
    valinit=1.0,
)

def toggle_play(event):
    global is_playing
    is_playing = not is_playing
    play_button.label.set_text("⏸ Pause" if is_playing else "▶ Play")

play_button.on_clicked(toggle_play)

ani = FuncAnimation(fig, play_animation, interval=40)

cam_button.on_clicked(toggle_camera)

frame_slider.on_changed(update)

# Initialize once
update(0)

plt.show()