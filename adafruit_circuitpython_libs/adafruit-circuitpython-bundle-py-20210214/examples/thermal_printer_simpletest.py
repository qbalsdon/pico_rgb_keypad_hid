# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple demo of printer functionality.
# Author: Tony DiCola
import board
import busio

import adafruit_thermal_printer

# Pick which version thermal printer class to use depending on the version of
# your printer.  Hold the button on the printer as it's powered on and it will
# print a test page that displays the firmware version, like 2.64, 2.68, etc.
# Use this version in the get_printer_class function below.
ThermalPrinter = adafruit_thermal_printer.get_printer_class(2.69)

# Define RX and TX pins for the board's serial port connected to the printer.
# Only the TX pin needs to be configued, and note to take care NOT to connect
# the RX pin if your board doesn't support 5V inputs.  If RX is left unconnected
# the only loss in functionality is checking if the printer has paper--all other
# functions of the printer will work.
RX = board.RX
TX = board.TX

# Create a serial connection for the printer.  You must use the same baud rate
# as your printer is configured (print a test page by holding the button
# during power-up and it will show the baud rate).  Most printers use 19200.
uart = busio.UART(TX, RX, baudrate=19200)

# For a computer, use the pyserial library for uart access.
# import serial
# uart = serial.Serial("/dev/serial0", baudrate=19200, timeout=3000)

# Create the printer instance.
printer = ThermalPrinter(uart, auto_warm_up=False)

# Initialize the printer.  Note this will take a few seconds for the printer
# to warm up and be ready to accept commands (hence calling it explicitly vs.
# automatically in the initializer with the default auto_warm_up=True).
printer.warm_up()

# Check if the printer has paper.  This only works if the RX line is connected
# on your board (but BE CAREFUL as mentioned above this RX line is 5V!)
if printer.has_paper():
    print("Printer has paper!")
else:
    print("Printer might be out of paper, or RX is disconnected!")

# Print a test page:
printer.test_page()

# Move the paper forward two lines:
printer.feed(2)

# Print a line of text:
printer.print("Hello world!")

# Print a bold line of text:
printer.bold = True
printer.print("Bold hello world!")
printer.bold = False

# Print a normal/thin underline line of text:
printer.underline = adafruit_thermal_printer.UNDERLINE_THIN
printer.print("Thin underline!")

# Print a thick underline line of text:
printer.underline = adafruit_thermal_printer.UNDERLINE_THICK
printer.print("Thick underline!")

# Disable underlines.
printer.underline = None

# Print an inverted line.
printer.inverse = True
printer.print("Inverse hello world!")
printer.inverse = False

# Print an upside down line.
printer.upside_down = True
printer.print("Upside down hello!")
printer.upside_down = False

# Print a double height line.
printer.double_height = True
printer.print("Double height!")
printer.double_height = False

# Print a double width line.
printer.double_width = True
printer.print("Double width!")
printer.double_width = False

# Print a strike-through line.
printer.strike = True
printer.print("Strike-through hello!")
printer.strike = False

# Print medium size text.
printer.size = adafruit_thermal_printer.SIZE_MEDIUM
printer.print("Medium size text!")

# Print large size text.
printer.size = adafruit_thermal_printer.SIZE_LARGE
printer.print("Large size text!")

# Back to normal / small size text.
printer.size = adafruit_thermal_printer.SIZE_SMALL

# Print center justified text.
printer.justify = adafruit_thermal_printer.JUSTIFY_CENTER
printer.print("Center justified!")

# Print right justified text.
printer.justify = adafruit_thermal_printer.JUSTIFY_RIGHT
printer.print("Right justified!")

# Back to left justified / normal text.
printer.justify = adafruit_thermal_printer.JUSTIFY_LEFT

# Print a UPC barcode.
printer.print("UPCA barcode:")
printer.print_barcode("123456789012", printer.UPC_A)

# Feed a few lines to see everything.
printer.feed(2)
