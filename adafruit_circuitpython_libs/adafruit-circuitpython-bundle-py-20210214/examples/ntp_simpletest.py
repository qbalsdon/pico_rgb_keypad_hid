# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_ntp import NTP

# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

# If you have an externally connected ESP32:
# esp32_cs = DigitalInOut(board.D9)
# esp32_ready = DigitalInOut(board.D10)
# esp32_reset = DigitalInOut(board.D5)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(b"WIFI_SSID", b"WIFI_PASS")
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue

# Initialize the NTP object
ntp = NTP(esp)

# Fetch and set the microcontroller's current UTC time
# keep retrying until a valid time is returned
while not ntp.valid_time:
    ntp.set_time()
    print("Failed to obtain time, retrying in 5 seconds...")
    time.sleep(5)

# Get the current time in seconds since Jan 1, 1970
current_time = time.time()
print("Seconds since Jan 1, 1970: {} seconds".format(current_time))

# Convert the current time in seconds since Jan 1, 1970 to a struct_time
now = time.localtime(current_time)
print(now)

# Pretty-parse the struct_time
print(
    "It is currently {}/{}/{} at {}:{}:{} UTC".format(
        now.tm_mon, now.tm_mday, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec
    )
)
