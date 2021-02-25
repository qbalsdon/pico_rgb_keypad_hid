# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import adafruit_pixie

# For use with CircuitPython:
uart = busio.UART(board.TX, rx=None, baudrate=115200)

# For use on Raspberry Pi/Linux with Adafruit_Blinka:
# import serial
# uart = serial.Serial("/dev/ttyS0", baudrate=115200, timeout=3000)

num_pixies = 2  # Change this to the number of Pixie LEDs you have.
pixies = adafruit_pixie.Pixie(uart, num_pixies, brightness=0.2, auto_write=False)


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


while True:
    for i in range(255):
        for pixie in range(num_pixies):
            pixies[pixie] = wheel(i)
        pixies.show()
    time.sleep(2)
    pixies[0] = (0, 255, 0)
    pixies[1] = (0, 0, 255)
    pixies.show()
    time.sleep(1)
    pixies.fill((255, 0, 0))
    pixies.show()
    time.sleep(1)
    pixies[::2] = [(255, 0, 100)] * (2 // 2)
    pixies[1::2] = [(0, 255, 255)] * (2 // 2)
    pixies.show()
    time.sleep(1)
