"""Half-duplex friendly COM port auto-postback loop.

This script listens on a serial port (default COM7) and writes back every
payload it receives, but only after the line has been idle for a configurable
period. That way, a half-duplex device under test receives the response only
after it finishes transmitting.
"""
import argparse
import sys
import time

try:
    import serial
except ImportError as exc:  # pragma: no cover - best effort guidance
    print("Missing dependency: pyserial. Install with `pip install pyserial`.", file=sys.stderr)
    raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Half-duplex aware serial auto-postback utility.")
    parser.add_argument("--port", default="COM7", help="Serial port name (default: COM7).")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200).")
    parser.add_argument("--timeout", type=float, default=0.5, help="Read timeout in seconds (default: 0.5).")
    parser.add_argument(
        "--idle-ms",
        type=float,
        default=10.0,
        help="Minimum silent period before echoing data back (default: 10 ms).",
    )
    parser.add_argument(
        "--poll-interval-ms",
        type=float,
        default=0.1,
        help="Sleep interval when idle; keep small to avoid latency (default: 0.1 ms).",
    )
    parser.add_argument(
        "--echo-hex",
        action="store_true",
        help="Also print echoed payload in hex alongside the raw bytes.",
    )
    return parser.parse_args()


def _write_all(port: serial.Serial, payload: bytes) -> int:
    """Ensure the full payload is written back to the port."""
    view = memoryview(payload)
    total = 0
    while total < len(payload):
        try:
            written = port.write(view[total:])
        except serial.SerialTimeoutException:
            written = 0
        if written is None:
            written = 0
        if written == 0:
            time.sleep(0.001)
            continue
        total += written
    port.flush()
    return total


def main() -> int:
    args = parse_args()

    try:
        serial_port = serial.Serial(
            args.port,
            args.baud,
            timeout=args.timeout,
            write_timeout=args.timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )
        serial_port.reset_input_buffer()
        serial_port.reset_output_buffer()
    except serial.SerialException as exc:
        print(f"Failed to open {args.port}: {exc}", file=sys.stderr)
        return 1

    print(f"Listening on {serial_port.port} at {serial_port.baudrate} baud. Press Ctrl+C to stop.")
    idle_threshold = max(args.idle_ms, 0.0) / 1000.0
    poll_sleep = max(args.poll_interval_ms, 0.0) / 1000.0
    rx_buffer = bytearray()
    last_rx_ts = None
    try:
        while True:
            waiting = serial_port.in_waiting
            if waiting:
                data = serial_port.read(waiting)
                if data:
                    rx_buffer.extend(data)
                    last_rx_ts = time.monotonic()
            else:
                now = time.monotonic()
                if rx_buffer and last_rx_ts is not None and (now - last_rx_ts) >= idle_threshold:
                    payload = bytes(rx_buffer)
                    quiet_ms = (now - last_rx_ts) * 1000.0
                    time.sleep(0.01)
                    _write_all(serial_port, payload)
                    if args.echo_hex:
                        hex_repr = " ".join(f"{byte:02X}" for byte in payload)
                        print(f"Looped back {payload!r} | hex: {hex_repr} | idle {quiet_ms:.2f} ms")
                    else:
                        print(f"Looped back {payload!r} after {quiet_ms:.2f} ms idle")
                    rx_buffer.clear()
                    last_rx_ts = None

                if poll_sleep:
                    time.sleep(poll_sleep)
    except KeyboardInterrupt:
        print("\nStopping auto-postback.")
    finally:
        serial_port.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
