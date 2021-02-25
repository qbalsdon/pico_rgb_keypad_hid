# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from adafruit_htu21d import HTU21D

# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
sensor = HTU21D(i2c)


while True:
    print("\nTemperature: %0.1f C" % sensor.temperature)
    print("Humidity: %0.1f %%" % sensor.relative_humidity)
    time.sleep(2)
