# SPDX-FileCopyrightText: 2020 by Bryan Siepert, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
# pylint:disable=unused-import
import time
import board
import busio
from adafruit_ltr390 import LTR390, UV, ALS

THRESHOLD_VALUE = 100

i2c = busio.I2C(board.SCL, board.SDA)
ltr = LTR390(i2c)

ltr.high_threshold = THRESHOLD_VALUE
ltr.enable_alerts(True, UV, 1)

while True:

    if ltr.threshold_passed:
        print("UV:", ltr.uvs)
        print("threshold", THRESHOLD_VALUE, "passed!")
        print("")
    else:
        print("threshold not passed yet")

    time.sleep(1)
