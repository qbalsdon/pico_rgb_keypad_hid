# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import adafruit_rgbled

# Pin the Red LED is connected to
RED_LED = board.D5

# Pin the Green LED is connected to
GREEN_LED = board.D6

# Pin the Blue LED is connected to
BLUE_LED = board.D7

# Create the RGB LED object
led = adafruit_rgbled.RGBLED(RED_LED, GREEN_LED, BLUE_LED)

# Optionally, you can also create the RGB LED object with inverted PWM
# led = adafruit_rgbled.RGBLED(RED_LED, GREEN_LED, BLUE_LED, invert_pwm=True)


def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return 0, 0, 0
    if pos < 85:
        return int(255 - pos * 3), int(pos * 3), 0
    if pos < 170:
        pos -= 85
        return 0, int(255 - pos * 3), int(pos * 3)
    pos -= 170
    return int(pos * 3), 0, int(255 - (pos * 3))


def rainbow_cycle(wait):
    for i in range(255):
        i = (i + 1) % 256
        led.color = wheel(i)
        time.sleep(wait)


while True:
    # setting RGB LED color to RGB Tuples (R, G, B)
    led.color = (255, 0, 0)
    time.sleep(1)

    led.color = (0, 255, 0)
    time.sleep(1)

    led.color = (0, 0, 255)
    time.sleep(1)

    # setting RGB LED color to 24-bit integer values
    led.color = 0xFF0000
    time.sleep(1)

    led.color = 0x00FF00
    time.sleep(1)

    led.color = 0x0000FF
    time.sleep(1)

    # rainbow cycle the RGB LED
    rainbow_cycle(0.1)
