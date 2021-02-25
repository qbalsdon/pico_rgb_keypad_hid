# SPDX-FileCopyrightText: 2020 Bryan Siepert, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
import time
import board
import busio
import adafruit_tmp117

i2c = busio.I2C(board.SCL, board.SDA)

tmp117 = adafruit_tmp117.TMP117(i2c)

print("Temperature without offset: %.2f degrees C" % tmp117.temperature)
tmp117.temperature_offset = 10.0
while True:
    print("Temperature w/ offset: %.2f degrees C" % tmp117.temperature)
    time.sleep(1)
