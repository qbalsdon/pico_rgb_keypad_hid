# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from digitalio import DigitalInOut
from digitalio import Direction
import adafruit_requests as requests
import adafruit_espatcontrol.adafruit_espatcontrol_socket as socket
from adafruit_espatcontrol import adafruit_espatcontrol


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise


# With a Particle Argon
RX = board.ESP_TX
TX = board.ESP_RX
resetpin = DigitalInOut(board.ESP_WIFI_EN)
rtspin = DigitalInOut(board.ESP_CTS)
uart = busio.UART(TX, RX, timeout=0.1)
esp_boot = DigitalInOut(board.ESP_BOOT_MODE)
esp_boot.direction = Direction.OUTPUT
esp_boot.value = True


print("ESP AT commands")
esp = adafruit_espatcontrol.ESP_ATcontrol(
    uart, 115200, reset_pin=resetpin, rts_pin=rtspin, debug=False
)

URL = "http://wifitest.adafruit.com/testwifi/index.html"
print("ESP AT GET URL", URL)

print("Resetting ESP module")
esp.hard_reset()

requests.set_socket(socket, esp)

while True:
    try:
        print("Checking connection...")
        while not esp.is_connected:
            print("Connecting...")
            esp.connect(secrets)
        # great, lets get the data
        print("Retrieving URL...", end="")
        r = requests.get(URL)
        print("Status:", r.status_code)
        print("Content type:", r.headers["content-type"])
        print("Content size:", r.headers["content-length"])
        print("Encoding:", r.encoding)
        print("Text:", r.text)

        time.sleep(60)
    except (ValueError, RuntimeError, adafruit_espatcontrol.OKError) as e:
        print("Failed to get data, retrying\n", e)
        continue
