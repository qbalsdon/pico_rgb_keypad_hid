# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import board
import busio
import adafruit_is31fl3731

i2c = busio.I2C(board.SCL, board.SDA)

sweep = [
    1,
    2,
    3,
    4,
    6,
    8,
    10,
    15,
    20,
    30,
    40,
    60,
    60,
    40,
    30,
    20,
    15,
    10,
    8,
    6,
    4,
    3,
    2,
    1,
]

frame = 0

# initialize display using Feather CharlieWing LED 15 x 7
display = adafruit_is31fl3731.CharlieWing(i2c)
# uncomment next line if you are using Adafruit 16x9 Charlieplexed PWM LED Matrix
# display = adafruit_is31fl3731.Matrix(i2c)
# uncomment next line if you are using Adafruit 16x8 Charlieplexed Bonnet
# display = adafruit_is31fl3731.CharlieBonnet(i2c)
# initial display using Pimoroni Scroll Phat HD LED 17 x 7
# display = adafruit_is31fl3731.ScrollPhatHD(i2c)

while True:
    for incr in range(24):
        # to reduce update flicker, use two frames
        # make a frame active, don't show it yet
        display.frame(frame, show=False)
        # fill the display with the next frame
        for x in range(display.width):
            for y in range(display.height):
                display.pixel(x, y, sweep[(x + y + incr) % 24])
        # show the next frame
        display.frame(frame, show=True)
        if frame:
            frame = 0
        else:
            frame = 1
