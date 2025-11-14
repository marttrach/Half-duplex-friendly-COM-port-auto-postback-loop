# Half-duplex-friendly-COM-port-auto-postback-loop
This script listens on a serial port (default COM7) and writes back every payload it receives, but only after the line has been idle for a configurable period. That way, a half-duplex device under test receives the response only after it finishes transmitting
