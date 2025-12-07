import time
import random

def generate_telemetry():
    """Simulates live Formula-style telemetry data"""
    telemetry = {
        "speed_kmh": random.uniform(80, 320),
        "rpm": random.uniform(3000, 15000),
        "throttle_pct": random.uniform(0, 100),
        "brake_pct": random.uniform(0, 100),
        "tire_temp_c": [
            random.uniform(70, 110),
            random.uniform(70, 110),
            random.uniform(70, 110),
            random.uniform(70, 110),
        ]
    }
    return telemetry

if __name__ == "__main__":
    print("Starting telemetry stream...\n")

    while True:
        data = generate_telemetry()
        print(data)
        time.sleep(0.5)
