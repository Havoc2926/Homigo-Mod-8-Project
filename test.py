import serial
import requests
import random
import time
import json
import os

# ------------------------ CONFIG ------------------------

PORT = '/dev/ttyACM0'
BAUD = 115200
API_KEY = "f66377a4-4aeb-487e-8685-bf07293f48bc"
SCENE_FILE = "/home/pi/homigo/scenes.json"  # Update this if needed

HEADERS = {
    "Govee-API-Key": API_KEY,
    "Content-Type": "application/json"
}

URL = "https://developer-api.govee.com/v1/devices/control"

# Your devices
DEVICES = [
    {'mac': 'A1:44:D0:C9:07:7F:F4:54', 'model': 'H6008'},
    {'mac': '38:8F:D0:C9:07:8A:FB:8A', 'model': 'H6008'}
]

# ------------------------ UTILITIES ------------------------

def load_scenes():
    if not os.path.exists(SCENE_FILE):
        print("Scene file not found.")
        return {}
    with open(SCENE_FILE, "r") as f:
        return json.load(f)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16)
    )

def set_scene(scene_name):
    scenes = load_scenes()
    scene = scenes.get(scene_name)
    if not scene:
        print(f"Scene '{scene_name}' not found.")
        return

    for device in DEVICES:
        mac = device['mac']
        model = device['model']
        if mac in scene:
            hex_color = scene[mac]
            r, g, b = hex_to_rgb(hex_color)
            payload = {
                'device': mac,
                'model': model,
                'cmd': {
                    'name': 'color',
                    'value': {'r': r, 'g': g, 'b': b}
                }
            }
            response = requests.put(URL, headers=HEADERS, json=payload)
            print(f"{scene_name.title()} → {mac} → {hex_color} → Status: {response.status_code}")
        else:
            print(f"{mac} not found in '{scene_name}' scene.")

# ------------------------ LIGHT CONTROL ------------------------

def turn_lights(on=True):
    state = "on" if on else "off"
    for device in DEVICES:
        payload = {
            "device": device['mac'],
            "model": device['model'],
            "cmd": {
                "name": "turn",
                "value": state
            }
        }
        response = requests.put(URL, headers=HEADERS, json=payload)
        print(f"Turned {state} → {device['mac']} → Status: {response.status_code}")

# ------------------------ KEYWORD HANDLER ------------------------

def homigoReceived():
    start = time.time()
    while time.time() - start < 3:
        line = ser.readline().decode('utf-8', errors='ignore').strip()

        if line.startswith("on:"):
            try:
                confidence = float(line.split(":")[1].strip())
                if confidence > 0.9:
                    print("Keyword: ON")
                    turn_lights(True)
                    return
            except ValueError:
                pass

        elif line.startswith("off:"):
            try:
                confidence = float(line.split(":")[1].strip())
                if confidence > 0.9:
                    print("Keyword: OFF")
                    turn_lights(False)
                    return
            except ValueError:
                pass

        elif any(line.startswith(f"{scene}:") for scene in ["happy", "focus", "party"]):
            try:
                keyword, confidence = line.split(":")
                confidence = float(confidence.strip())
                if confidence > 0.85:
                    print(f"Keyword: {keyword.upper()}")
                    set_scene(keyword)
                    return
            except ValueError:
                pass

# ------------------------ MAIN LOOP ------------------------

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print("Listening for keywords...\n")

    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            print(f"[Arduino] {line}")
            if line.startswith("homigo:"):
                try:
                    confidence = float(line.split(":")[1].strip())
                    if confidence > 0.9:
                        print("\n" + "@" * 20)
                        print("HOMIGO ACTIVATED → Listening for command...")
                        print("@" * 20 + "\n")
                        homigoReceived()
                except ValueError:
                    pass
except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    ser.close()
