# SPDX-FileCopyrightText: 2020 Bryan Siepert, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
import board
import busio
from adafruit_tmp117 import TMP117, AverageCount

i2c = busio.I2C(board.SCL, board.SDA)

tmp117 = TMP117(i2c)

# uncomment different options below to see how it affects the reported temperature
# and measurement time

# tmp117.averaged_measurements = AverageCount.AVERAGE_1X
# tmp117.averaged_measurements = AverageCount.AVERAGE_8X
# tmp117.averaged_measurements = AverageCount.AVERAGE_32X
# tmp117.averaged_measurements = AverageCount.AVERAGE_64X

print(
    "Number of averaged samples per measurement:",
    AverageCount.string[tmp117.averaged_measurements],
)
print(
    "Reads should take approximately",
    AverageCount.string[tmp117.averaged_measurements] * 0.0155,
    "seconds",
)

while True:
    print("Single measurement: %.2f degrees C" % tmp117.take_single_measurememt())
    # time.sleep(1)
