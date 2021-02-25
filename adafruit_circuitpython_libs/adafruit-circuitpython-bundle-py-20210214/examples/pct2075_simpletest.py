# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import adafruit_pct2075

i2c = busio.I2C(board.SCL, board.SDA)

pct = adafruit_pct2075.PCT2075(i2c)

while True:
    print("Temperature: %.2f C" % pct.temperature)
    time.sleep(0.5)
