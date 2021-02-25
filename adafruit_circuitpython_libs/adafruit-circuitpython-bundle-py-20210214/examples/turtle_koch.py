# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import board
from adafruit_turtle import turtle


def f(side_length, depth, generation):
    if depth != 0:
        side = lambda: f(side_length / 3, depth - 1, generation + 1)
        side()
        turtle.left(60)
        side()
        turtle.right(120)
        side()
        turtle.left(60)
        side()


turtle = turtle(board.DISPLAY)

unit = min(board.DISPLAY.width / 3, board.DISPLAY.height / 4)
top_len = unit * 3
print(top_len)
turtle.penup()
turtle.goto(-1.5 * unit, unit)
turtle.pendown()

num_generations = 3
top_side = lambda: f(top_len, num_generations, 0)

top_side()
turtle.right(120)
top_side()
turtle.right(120)
top_side()

while True:
    pass
