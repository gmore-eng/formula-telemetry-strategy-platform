import sys
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
from PyQt5.QtWidgets import QSlider
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


SIM_PATH = "data/sim_racing/processed_rio_race_engineering.csv"
F1_PATH = "data/fastf1/processed_fastf1_race_engineering.csv"


class TelemetryDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Motorsport Telemetry & Strategy Dashboard")
        self.setGeometry(100, 100, 1100, 700)

        # ==============================
        # LOAD DATA
        # ==============================

        self.sim_df = pd.read_csv(SIM_PATH)
        self.f1_df = pd.read_csv(F1_PATH)

        self.current_source = "SIM"
        self.current_lap = 0

        # ==============================
        # MAIN LAYOUT
        # ==============================

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # ==============================
        # LEFT CONTROL PANEL
        # ==============================

        control_panel = QVBoxLayout()

        title = QLabel("Telemetry Controls")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        control_panel.addWidget(title)

        # Data source selector
        self.source_selector = QComboBox()
        self.source_selector.addItems(["SIM", "F1"])
        self.source_selector.currentTextChanged.connect(self.change_source)

        control_panel.addWidget(QLabel("Data Source"))
        control_panel.addWidget(self.source_selector)

        # Lap selector (SIM only)
        self.lap_selector = QComboBox()
        self.populate_laps()
        self.lap_selector.currentIndexChanged.connect(self.change_lap)

        control_panel.addWidget(QLabel("Lap (SIM Only)"))
        control_panel.addWidget(self.lap_selector)

        # Refresh plots button
        refresh_btn = QPushButton("Update Plots")
        refresh_btn.clicked.connect(self.update_plots)

        control_panel.addWidget(refresh_btn)

        # ==============================
        # TIME SLIDER (3D REPLAY CONTROL)
        # ==============================

        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(100)   # will be updated dynamically
        self.time_slider.setValue(0)
        self.time_slider.valueChanged.connect(self.update_plots)

        control_panel.addWidget(QLabel("3D Replay Time"))
        control_panel.addWidget(self.time_slider)

        control_panel.addStretch()
        main_layout.addLayout(control_panel, 1)

        # ==============================
        # RIGHT PLOT AREA
        # ==============================

        plot_layout = QVBoxLayout()

        self.fig = Figure(figsize=(6, 8))
        self.canvas = FigureCanvas(self.fig)

        plot_layout.addWidget(self.canvas)
        main_layout.addLayout(plot_layout, 4)

        # Initial draw
        self.update_plots()

    # ==============================
    # UI CALLBACKS
    # ==============================

    def populate_laps(self):
        self.lap_selector.clear()
        laps = sorted(self.sim_df["lap"].unique())
        for lap in laps:
            self.lap_selector.addItem(str(lap))

    def change_source(self, source):
        self.current_source = source

        if source == "SIM":
            self.lap_selector.setEnabled(True)
        else:
            self.lap_selector.setEnabled(False)

        self.update_plots()

    def change_lap(self, idx):
        self.current_lap = idx
        self.update_plots()

    # ==============================
    # PLOTTING LOGIC
    # ==============================

    def update_plots(self):
        self.fig.clear()

        ax1 = self.fig.add_subplot(311)                 # Speed vs Distance
        ax2 = self.fig.add_subplot(312)                 # Accel vs Distance
        ax3 = self.fig.add_subplot(313, projection='3d')  # 3D Track View

        if self.current_source == "SIM":
            df = self.sim_df[self.sim_df["lap"] == self.current_lap]

            distance = df["distance_m"]
            speed = df["speed"]
            accel = df["long_accel"]
            brake = df["brake_event"]

            # ========================
            # 2D PLOTS
            # ========================

            ax1.plot(distance, speed, label=f"SIM Lap {self.current_lap}")
            braking_points = df[brake == 1]
            ax1.scatter(braking_points["distance_m"], braking_points["speed"], s=8)

            ax1.set_title("Speed vs Distance (SIM)")
            ax2.set_title("Acceleration vs Distance (SIM)")

            ax2.plot(distance, accel)

            # ========================
            # 3D TELEMETRY REPLAY (SIM)
            # ========================

            total_frames = len(df)
            self.time_slider.setMaximum(max(0, total_frames - 1))

            frame_idx = min(self.time_slider.value(), total_frames - 1)
            row = df.iloc[frame_idx]

            x = row["distance_m"]
            y = row["wheel_speed_avg"]
            z = row["speed"]

            is_braking = row["brake"] == 1
            color = "red" if is_braking else "green"

            ax3.scatter([x], [y], [z], c=color, s=80)

            ax3.set_title("3D Telemetry Replay (SIM)\nRed = Braking | Green = Throttle")
            ax3.set_xlabel("Distance (m)")
            ax3.set_ylabel("Wheel Speed Avg")
            ax3.set_zlabel("Speed (km/h)")

        else:
            df = self.f1_df

            distance = df["distance_m"]
            speed = df["speed"]
            accel = df["long_accel"]
            brake = df["brake"]

            # ========================
            # 2D PLOTS
            # ========================

            ax1.plot(distance, speed, label="F1 Telemetry")
            braking_points = df[brake == 1]
            ax1.scatter(braking_points["distance_m"], braking_points["speed"], s=8)

            ax1.set_title("Speed vs Distance (F1)")
            ax2.set_title("Acceleration vs Distance (F1)")

            ax2.plot(distance, accel)

            # ========================
            # 3D TELEMETRY REPLAY (F1)
            # ========================

            total_frames = len(df)
            self.time_slider.setMaximum(max(0, total_frames - 1))

            frame_idx = min(self.time_slider.value(), total_frames - 1)
            row = df.iloc[frame_idx]

            x = row["distance_m"]
            y = 0
            z = row["speed"]

            is_braking = row["brake"] == 1
            color = "red" if is_braking else "green"

            ax3.scatter([x], [y], [z], c=color, s=80)

            ax3.set_title("3D Telemetry Replay (F1)\nRed = Braking | Green = Throttle")
            ax3.set_xlabel("Distance (m)")
            ax3.set_ylabel("Track Axis")
            ax3.set_zlabel("Speed (km/h)")

        # ========================
        # Final formatting
        # ========================

        for ax in [ax1, ax2]:
            ax.set_xlabel("Distance (m)")
            ax.grid(True)

        self.fig.tight_layout()
        self.canvas.draw()

# ==============================
# APPLICATION ENTRY POINT
# ==============================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TelemetryDashboard()
    window.show()
    sys.exit(app.exec_())