# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import adafruit_dps310

i2c = busio.I2C(board.SCL, board.SDA)

dps310 = adafruit_dps310.DPS310(i2c)

while True:
    print("Temperature = %.2f *C" % dps310.temperature)
    print("Pressure = %.2f hPa" % dps310.pressure)
    print("")
    time.sleep(1.0)
