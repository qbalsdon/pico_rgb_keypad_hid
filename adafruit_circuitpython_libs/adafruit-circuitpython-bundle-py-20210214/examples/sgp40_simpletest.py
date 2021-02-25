# SPDX-FileCopyrightText: 2020 by Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
import time
import board
import busio
import adafruit_sgp40

i2c = busio.I2C(board.SCL, board.SDA)
sgp = adafruit_sgp40.SGP40(i2c)

while True:
    print("Raw Gas: ", sgp.raw)
    print("")
    time.sleep(1)
