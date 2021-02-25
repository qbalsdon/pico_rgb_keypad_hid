# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from adafruit_lis331 import LIS331HH, Rate, Frequency

i2c = busio.I2C(board.SCL, board.SDA)

# un-comment the sensor you are using
# lis = H3LIS331(i2c)
lis = LIS331HH(i2c)

# `data_rate` must be a `LOWPOWER` rate to use the low-pass filter
lis.data_rate = Rate.RATE_LOWPOWER_10_HZ
# next set the cutoff frequency. Anything changing faster than
# the specified frequency will be filtered out
lis.lpf_cutoff = Frequency.FREQ_74_HZ

# Once you've seen the filter do its thing, you can comment out the
# lines above to use the default data rate without the low pass filter
# and see the difference it makes

while True:
    print(lis.acceleration)  # plotter friendly printing
    time.sleep(0.002)
