# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import board
import busio
import adafruit_is31fl3731

i2c = busio.I2C(board.SCL, board.SDA)

# initialize display using Feather CharlieWing LED 15 x 7
display = adafruit_is31fl3731.CharlieWing(i2c)

# uncomment next line if you are using Adafruit 16x9 Charlieplexed PWM LED Matrix
# display = adafruit_is31fl3731.Matrix(i2c)

# uncomment next line if you are using Adafruit 16x8 Charlieplexed Bonnet
# display = adafruit_is31fl3731.CharlieBonnet(i2c)

# initial display using Pimoroni Scroll Phat HD LED 17 x 7
# display = adafruit_is31fl3731.ScrollPhatHD(i2c)

# draw a box on the display
# first draw the top and bottom edges
for x in range(display.width):
    display.pixel(x, 0, 50)
    display.pixel(x, display.height - 1, 50)
# now draw the left and right edges
for y in range(display.height):
    display.pixel(0, y, 50)
    display.pixel(display.width - 1, y, 50)
