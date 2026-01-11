# omen-fan (Community Fork)

A tool to control fans on HP Omen laptops on Unix. 

This fork adds compatibility tests to reduce risk before using fan control.

## ⚠️ Warning

Use at your own risk. Direct EC (Embedded Controller) access could cause instability, disable your fan control or even damage hardware. No warranty.

## Quick start

1. Clone the repo:

```bash
git clone https://github.com/alxfox/omen-fan
cd omen-fan
```

2. Install Python dependencies, I recommend using a virtual environment like this:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Note: These scripts require sudo, which means you must explicitly use `.venv/bin/python` instead of `python` every time you call the script:

```bash
sudo .venv/bin/python compatibility_check.py
```

3. Run the safe, read-only check first (attempts to read from EC memory):

```bash
sudo .venv/bin/python compatibility_check.py
```

4. If compatible, you may run the write test (attempts to write into EC memory, reads the value to see if it changed, then resets the values)

```bash
sudo .venv/bin/python ec_write_test.py
```

4. If both tests pass, you can use the main tool:

```bash
sudo .venv/bin/python omen-fan.py --help
```



## Tests (summary)

- compatibility_check.py — read-only checks (recommended first step).
- ec_write_test.py — writes to the EC (moderate to high risk). Use only if compatibility check passes.
- omen-fan.py — the actual fan control script; changes EC state and can override BIOS fan control.

## Install

Ensure EC module is loaded and install Python deps:

```bash
sudo modprobe ec_sys write_support=1
pip install click tomlkit click-aliases
```

## Configuration

Use the built-in `configure` command to view or update settings in `/etc/omen-fan/config.toml`. The command requires root.

The first time you use the command, a default configuration will be created.

- View current config:

```bash
sudo .venv/bin/python omen-fan.py configure --view
```

- Set values (examples):

```bash
sudo .venv/bin/python omen-fan.py configure --temp-curve 50,60,70,80,87,93 --speed-curve 20,40,60,70,85,100 --idle-speed 0
```

Editable settings

- TEMP_CURVE — list of temperature thresholds (must be ascending)
- SPEED_CURVE — list of fan speeds corresponding to TEMP_CURVE (same length required)
- IDLE_SPEED — fan speed when idle (0–100)
- POLL_INTERVAL — seconds between polls
- SPEED_COOLDOWN — seconds before allowing speed decreases
- SPEED_SMOOTHING — smoothing factor (0.1–1.0)
- SPEED_DEADBAND — minimum % change to trigger an update
- ENABLE_LOGGING — enable/disable detailed logging (True/False)
- LOG_INTERVAL — seconds between log entries
- BYPASS_DEVICE_CHECK — (script) allow running on unsupported devices

Validation notes

- `TEMP_CURVE` and `SPEED_CURVE` must have the same length and `TEMP_CURVE` must be in ascending order.
- The `configure` command performs basic validation and will raise an error on invalid input.

Starting the script

- Manual: start/stop the service with the `service` command:

```bash
sudo .venv/bin/python omen-fan.py service start
sudo .venv/bin/python omen-fan.py service stop
```

- Convenience script: `fan_control_service.sh`:

```bash
./fan_control_service.sh
```

The convenience script uses its own path and venv; use the venv Python directly if you run the service from a different location or from systemd.

## Emergency recovery

If something does goes wrong:

- Reboot - BIOS should restore fan control.
- You may use the script to return BIOS control with:

```bash
sudo python3 omen-fan.py bios-control 1
```

- If you disable/lower fan speed too much, your system might overheat. If you notice this, shut down immediately. On reboot, the fans should reset their settings.

## Contributing

Run `compatibility_check.py` and open an issue with your model and results.

## License and disclaimer

Provided as-is with no warranty. Authors are not responsible for damage or data loss.
