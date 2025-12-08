import pandas as pd
import numpy as np
import pyvista as pv
import time

# =========================
# LOAD DATA
# =========================

INPUT_PATH = "data/fastf1/bahrain_2023_verstappen.csv"
df = pd.read_csv(INPUT_PATH)

x = df["X"].values
y = df["Y"].values
z = np.zeros_like(x)

speed = df["Speed"].values
gear = df["nGear"].values
brake = df["Brake"].values

points = np.column_stack((x, y, z))
n_points = len(points)

# =========================
# TRACK
# =========================

lines = np.hstack(([n_points], np.arange(n_points)))
track = pv.PolyData(points, lines=lines)
track["speed"] = speed
track_tube = track.tube(radius=25)

# =========================
# CAR
# =========================

car = pv.Sphere(radius=80)
car.translate(points[0])

# =========================
# PLOTTER
# =========================

plotter = pv.Plotter(window_size=(1400, 900))
plotter.set_background("white")

plotter.add_mesh(
    track_tube,
    scalars="speed",
    cmap="turbo",
    smooth_shading=True,
    show_scalar_bar=True,
)

car_actor = plotter.add_mesh(car, color="red", smooth_shading=True)
plotter.camera_position = "iso"

# =========================
# HUD
# =========================

hud = plotter.add_text(
    "Speed: 0 km/h\nGear: 0",
    position="upper_left",
    font_size=20,
    color="black",
)

# =========================
# SHOW WINDOW ONCE
# =========================

# plotter.show(auto_close=False)

# =========================
# ANIMATION STATE
# =========================

frame = 0
stride = 2
is_playing = False


# =========================
# ANIMATION FUNCTION
# =========================

def animate():
    global frame, is_playing

    if not is_playing:
        return

    if frame >= n_points:
        frame = 0

    new_pos = points[frame]
    car_actor.SetPosition(new_pos.tolist())

    v = float(speed[frame])
    g = int(gear[frame])
    b = float(brake[frame])

    # Brake tint
    if b > 0.05:
        car_actor.prop.color = (0.8, 0.1, 0.1)
    else:
        if v < 120:
            car_actor.prop.color = (0.1, 0.4, 1.0)
        elif v < 230:
            car_actor.prop.color = (1.0, 1.0, 0.1)
        else:
            car_actor.prop.color = (1.0, 0.1, 0.1)

    hud.SetText(0, f"Speed: {v:6.1f} km/h\nGear: {g}")

    frame += stride
    plotter.render()


# =========================
# SPACE BAR TOGGLE
# =========================

def toggle_play():
    global is_playing
    is_playing = not is_playing
    print("Playing" if is_playing else "Paused")


plotter.add_key_event("space", toggle_play)


# =========================
# TIMER (CALLS ANIMATE)
# =========================

plotter.add_callback(animate, interval=10)


# =========================
# START WINDOW
# =========================

plotter.show()