# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""Test your Trellis M4 Express without needing the serial output.
Press any button and the rest will light up the same color!"""
import time
import adafruit_trellism4

trellis = adafruit_trellism4.TrellisM4Express()


def wheel(pos):
    if pos < 0 or pos > 255:
        return 0, 0, 0
    if pos < 85:
        return int(255 - pos * 3), int(pos * 3), 0
    if pos < 170:
        pos -= 85
        return 0, int(255 - pos * 3), int(pos * 3)
    pos -= 170
    return int(pos * 3), 0, int(255 - (pos * 3))


for x in range(trellis.pixels.width):
    for y in range(trellis.pixels.height):
        pixel_index = ((y * 8) + x) * 256 // 32
        trellis.pixels[x, y] = wheel(pixel_index & 255)


current_press = set()
while True:
    pressed = set(trellis.pressed_keys)
    for press in pressed - current_press:
        if press:
            print("Pressed:", press)
            pixel = (press[1] * 8) + press[0]
            pixel_index = pixel * 256 // 32
            trellis.pixels.fill(wheel(pixel_index & 255))
    for release in current_press - pressed:
        if release:
            print("Released:", release)
            for x in range(trellis.pixels.width):
                for y in range(trellis.pixels.height):
                    pixel_index = ((y * 8) + x) * 256 // 32
                    trellis.pixels[x, y] = wheel(pixel_index & 255)
    time.sleep(0.08)
    current_press = pressed
