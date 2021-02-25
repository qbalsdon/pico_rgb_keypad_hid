# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

from adafruit_simplemath import map_range, constrain

# Map, say, a sensor value, from a range of 0-255 to 0-1023.
print(map_range(30, 0, 255, 0, 1023))

# Constrain a value to a range.
print(constrain(0, 1, 3))  # prints 1
print(constrain(4, 1, 3))  # prints 3
print(constrain(2, 2, 3))  # prints 2
