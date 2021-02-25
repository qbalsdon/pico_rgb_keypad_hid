# SPDX-FileCopyrightText: 2020 Bryan Siepert, written for Adafruit Industries

# SPDX-License-Identifier: Unlicense
import time
import board
import adafruit_bh1750

i2c = board.I2C()

sensor = adafruit_bh1750.BH1750(i2c)

while True:
    print("%.2f Lux" % sensor.lux)
    time.sleep(1)
