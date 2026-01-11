#!/usr/bin/env python3

import os
import signal
import sys
from time import sleep, time, strftime
import tomlkit
from bisect import bisect_left

ECIO_FILE = "/sys/kernel/debug/ec/ec0/io"
IPC_FILE = "/tmp/omen-fand.PID"
LOG_FILE = "/tmp/omen-fand.log"
CONFIG_FILE = "/etc/omen-fan/config.toml"

FAN1_OFFSET = 52  # 0x34
FAN2_OFFSET = 53  # 0x35
BIOS_OFFSET = 98  # 0x62
TIMER_OFFSET = 99  # 0x63
CPU_TEMP_OFFSET = 87  # 0x57
GPU_TEMP_OFFSET = 183  # 0xB7

FAN1_MAX = 50
FAN2_MAX = 50

with open(CONFIG_FILE, "r") as file:
    doc = tomlkit.loads(file.read())
    TEMP_CURVE = doc["service"]["TEMP_CURVE"].unwrap()
    SPEED_CURVE = doc["service"]["SPEED_CURVE"].unwrap()
    IDLE_SPEED = doc["service"]["IDLE_SPEED"].unwrap()
    POLL_INTERVAL = doc["service"]["POLL_INTERVAL"].unwrap()

    # Get cooldown period from config, default to 15 seconds if not set
    SPEED_COOLDOWN = doc["service"].get("SPEED_COOLDOWN", 15)

    # Get smoothing and deadband settings
    SPEED_SMOOTHING = doc["service"].get(
        "SPEED_SMOOTHING", 0.3
    )  # Smoothing factor (0.1-1.0)
    SPEED_DEADBAND = doc["service"].get(
        "SPEED_DEADBAND", 3
    )  # Minimum % change to adjust

    # Get logging settings
    ENABLE_LOGGING = doc["service"].get(
        "ENABLE_LOGGING", False
    )  # Enable detailed logging
    LOG_INTERVAL = doc["service"].get("LOG_INTERVAL", 5)  # Log every N seconds

# Precalculate slopes to reduce compute time.
slope = []
for i in range(1, len(TEMP_CURVE)):
    speed_diff = SPEED_CURVE[i] - SPEED_CURVE[i - 1]
    temp_diff = TEMP_CURVE[i] - TEMP_CURVE[i - 1]
    slope_val = round(speed_diff / temp_diff, 2)
    slope.append(slope_val)


def is_root():
    if os.geteuid() != 0:
        print("  Root access is required for this service.")
        print("  Please run this service as root.")
        sys.exit(1)


def sig_handler(signum, frame):
    log_message("Service stopped")
    os.remove(IPC_FILE)
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    bios_control(True)
    sys.exit()


def update_fan(speed1, speed2):
    with open(ECIO_FILE, "r+b") as ec:
        ec.seek(FAN1_OFFSET)
        ec.write(bytes([int(speed1)]))
        ec.seek(FAN2_OFFSET)
        ec.write(bytes([int(speed2)]))


def log_message(message):
    """Write a timestamped message to the log file"""
    if ENABLE_LOGGING:
        timestamp = strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as log:
                log.write(f"[{timestamp}] {message}\n")
                log.flush()  # Ensure immediate write
        except Exception:
            pass  # Fail silently if logging fails


def get_temp():
    with open(ECIO_FILE, "rb") as ec:
        ec.seek(CPU_TEMP_OFFSET)
        temp_c = int.from_bytes(ec.read(1), "big")
        ec.seek(GPU_TEMP_OFFSET)
        temp_g = int.from_bytes(ec.read(1), "big")
    return temp_c, temp_g, max(temp_c, temp_g)


def bios_control(enabled):
    if enabled is False:
        with open(ECIO_FILE, "r+b") as ec:
            ec.seek(BIOS_OFFSET)
            ec.write(bytes([6]))
            sleep(0.1)
            ec.seek(TIMER_OFFSET)
            ec.write(bytes([0]))
    elif enabled is True:
        with open(ECIO_FILE, "r+b") as ec:
            ec.seek(BIOS_OFFSET)
            ec.write(bytes([0]))
            ec.seek(FAN1_OFFSET)
            ec.write(bytes([0]))
            ec.seek(FAN2_OFFSET)
            ec.write(bytes([0]))


signal.signal(signal.SIGTERM, sig_handler)

with open(IPC_FILE, "w", encoding="utf-8") as ipc:
    ipc.write(str(os.getpid()))

# Clear previous log file
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

speed_old = -1
last_speed_increase_time = 0  # Track when we last increased speed
current_speed = 0  # Track current applied speed for hysteresis
smoothed_speed = 0  # Track smoothed speed to reduce oscillation
last_log_time = 0  # Track when we last logged
is_root()

log_message(f"Service started - PID: {os.getpid()}")
log_message(f"Config: TEMP_CURVE={TEMP_CURVE}, SPEED_CURVE={SPEED_CURVE}")
log_message(
    f"Settings: COOLDOWN={SPEED_COOLDOWN}s, SMOOTHING={SPEED_SMOOTHING}, DEADBAND={SPEED_DEADBAND}%"
)

while True:
    cpu_temp, gpu_temp, temp = get_temp()
    current_time = time()

    # Calculate target speed based on temperature curve
    if temp <= TEMP_CURVE[0]:
        target_speed = IDLE_SPEED
    elif temp >= TEMP_CURVE[-1]:
        target_speed = SPEED_CURVE[-1]
    else:
        i = bisect_left(TEMP_CURVE, temp)
        y0 = SPEED_CURVE[i - 1]
        x0 = TEMP_CURVE[i - 1]
        target_speed = y0 + slope[i - 1] * (temp - x0)

    # Apply exponential smoothing to reduce rapid changes
    if smoothed_speed == 0:
        # First iteration - initialize smoothed speed
        smoothed_speed = target_speed
    else:
        # Smooth the target speed to reduce oscillation
        smoothed_speed = (SPEED_SMOOTHING * target_speed) + (
            (1 - SPEED_SMOOTHING) * smoothed_speed
        )

    # Hysteresis logic: Always allow speed increases, but delay decreases
    hysteresis_action = ""
    if smoothed_speed > current_speed:
        # Speed increase - always allow immediately
        proposed_speed = smoothed_speed
        last_speed_increase_time = current_time
        current_speed = proposed_speed
        hysteresis_action = "INCREASE"
    elif smoothed_speed < current_speed:
        # Speed decrease - only allow after cooldown period
        time_since_increase = current_time - last_speed_increase_time
        if time_since_increase >= SPEED_COOLDOWN:
            # Cooldown period has passed, allow decrease
            proposed_speed = smoothed_speed
            current_speed = proposed_speed
            hysteresis_action = "DECREASE"
        else:
            # Still in cooldown, maintain current speed
            proposed_speed = current_speed
            hysteresis_action = (
                f"COOLDOWN({int(SPEED_COOLDOWN - time_since_increase)}s)"
            )
    else:
        # Speed unchanged
        proposed_speed = smoothed_speed
        current_speed = proposed_speed
        hysteresis_action = "MAINTAIN"

    # Apply deadband filter - only change if difference is significant
    speed_difference = abs(proposed_speed - speed_old)
    deadband_applied = False
    if speed_difference >= SPEED_DEADBAND or speed_old == -1:
        # Round to nearest 5% to create stable speed steps
        final_speed = round(proposed_speed / 5) * 5

        # Ensure we stay within bounds
        final_speed = max(0, min(100, final_speed))

        # Only update fans if speed actually changed
        if speed_old != final_speed:
            speed_old = final_speed
            update_fan(FAN1_MAX * final_speed / 100, FAN2_MAX * final_speed / 100)
            log_message(
                f"SPEED CHANGE: CPU={cpu_temp}°C GPU={gpu_temp}°C Max={temp}°C | Target={target_speed:.1f}% Smoothed={smoothed_speed:.1f}% Final={final_speed}% | Action={hysteresis_action}"
            )
    else:
        deadband_applied = True

    # Log periodic status updates
    if current_time - last_log_time >= LOG_INTERVAL:
        status = "DEADBAND" if deadband_applied else hysteresis_action
        log_message(
            f"STATUS: CPU={cpu_temp}°C GPU={gpu_temp}°C Max={temp}°C | Target={target_speed:.1f}% Smoothed={smoothed_speed:.1f}% Current={speed_old}% | {status}"
        )
        last_log_time = current_time

    bios_control(False)
    sleep(POLL_INTERVAL)
