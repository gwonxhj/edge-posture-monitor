import json
import socket

HOST = "127.0.0.1"
PORT = 5000

s = socket.socket()
s.connect((HOST, PORT))

cmd = {
    "cmd": "submit_profile",
    "user_id": "user_001",
    "name": "test",
    "height_cm": 175,
    "weight_kg": 70,
    "rest_work_min": 60,
    "rest_break_min": 10
}

s.send(json.dumps(cmd).encode())