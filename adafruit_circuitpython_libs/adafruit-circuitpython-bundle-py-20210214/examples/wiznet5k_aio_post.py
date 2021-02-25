# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from digitalio import DigitalInOut
import adafruit_requests as requests
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

# Get Adafruit.io details from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

cs = DigitalInOut(board.D10)
spi_bus = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs)
requests.set_socket(socket, eth)

counter = 0

while True:
    print("Posting data...", end="")
    data = counter
    feed = "test"
    payload = {"value": data}
    response = requests.post(
        "http://io.adafruit.com/api/v2/"
        + secrets["aio_username"]
        + "/feeds/"
        + feed
        + "/data",
        json=payload,
        headers={"X-AIO-KEY": secrets["aio_key"]},
    )
    print(response.json())
    response.close()
    counter = counter + 1
    print("OK")
    response = None
    time.sleep(15)
