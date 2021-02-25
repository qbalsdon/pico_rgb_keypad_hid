# SPDX-FileCopyrightText: 2020 by Bryan Siepert, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
import time
import board
import busio
import adafruit_ltr390

i2c = busio.I2C(board.SCL, board.SDA)

ltr = adafruit_ltr390.LTR390(i2c)

while True:
    print("UV:", ltr.uvs, "\t\tAmbient Light:", ltr.light)
    time.sleep(1.0)
