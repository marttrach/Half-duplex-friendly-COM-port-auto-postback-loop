
## COM Port Auto Postback

`com_port_autopostback.py` is a tiny utility that keeps a serial port open, buffers all incoming bytes, and then echoes the payload back only after the line has been idle for a configurable number of milliseconds. The delay makes the script safe for half‑duplex devices under test because the response never collides with the original transmission.

The code relies solely on [pyserial](https://pyserial.readthedocs.io/) and works on Windows, macOS, and Linux as long as the target serial device is accessible.

---

### Requirements

- Python 3.9+ with `pip` (or [uv](https://github.com/astral-sh/uv))
- The `pyserial` package
- Access to the COM/tty device you want to loop back

---

### Setup

#### Option 1: `uv`

```bash
uv venv
uv pip install pyserial
# (Windows) .\.venv\Scripts\activate
# (Unix)    source .venv/bin/activate
```

#### Option 2: Standard `pip`

```bash
python -m venv .venv
# (Windows) .\.venv\Scripts\activate
# (Unix)    source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pyserial
```

You can skip the virtual environment steps if you prefer a system-wide installation, but using a venv keeps the dependency isolated.

---

### Running the script

```bash
python com_port_autopostback.py --port COM7 --baud 115200 --idle-ms 10
```

The script prints a line every time it loops back a payload. Press `Ctrl+C` to exit.

If you are on Linux/macOS replace `COM7` with your `/dev/ttyUSB0` (or similar) device name. When the `--echo-hex` flag is set, the payload is printed both as raw bytes and as hexadecimal pairs for easy inspection.

---

### Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--port` | `COM7` | Serial port name to open. Use the appropriate `/dev/tty*` device on Unix-like systems. |
| `--baud` | `115200` | Baud rate used when opening the port. |
| `--timeout` | `0.5` | Read and write timeout in seconds. Increase if you expect long pauses. |
| `--idle-ms` | `10.0` | Minimum silent period, in milliseconds, that must pass after the last byte before the buffered payload is echoed back. |
| `--poll-interval-ms` | `0.1` | Sleep duration, in milliseconds, for the idle poll loop. Lower values reduce latency but increase CPU usage. |
| `--echo-hex` | `False` | When set, prints the echoed payload both as `repr(bytes)` and as a space-separated hex string. |

---

### Workflow tips

- Test your wiring with a direct loopback plug before involving the device under test.
- Start with a generous `--idle-ms` (for example 20 ms) if you are unsure about how much silence the remote device needs, then decrease once things work reliably.
- Combine the script with a serial monitor (e.g., `uv pip install miniterm`) to observe traffic if you need deeper debugging.
