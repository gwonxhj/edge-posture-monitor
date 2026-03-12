# src/ble_constants.py

DEVICE_NAME = "PostureChair-RPi"

# Custom Service UUID
POSTURE_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"

# App -> RPi (write)
CONTROL_RX_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

# RPi -> App (notify)
STATUS_TX_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"

# RPi -> App (read / notify)
REPORT_TX_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef3"

# Optional: connection / version / heartbeat
META_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef4"