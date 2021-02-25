# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_thermal_printer.thermal_printer_legacy.ThermalPrinter`
=================================================================

Thermal printer control module built to work with small serial thermal
receipt printers.  Note that these printers have many different firmware
versions and care must be taken to select the appropriate module inside this
package for your firmware printer:

* thermal_printer_2168 = Printers with firmware version 2.168+.
* thermal_printer = The latest printers with firmware version 2.68 up to 2.168
* thermal_printer_264 = Printers with firmware version 2.64 up to 2.68.
* thermal_printer_legacy = Printers with firmware version before 2.64.

* Author(s): Tony DiCola
"""
from micropython import const

import adafruit_thermal_printer.thermal_printer as thermal_printer


__version__ = "1.3.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Thermal_Printer.git"


# Internally used constants.
_INVERSE_MASK = const(1 << 1)  # Not in 2.6.8 firmware


# Legacy behavior class for printers with firmware before 2.64.
# See the comments in thermal_printer.py to understand how this class overrides
# methods which change for older firmware printers!
class ThermalPrinter(thermal_printer.ThermalPrinter):
    """Thermal printer for printers with firmware version before 2.64."""

    # Barcode types.  These vary based on the firmware version so are made
    # as class-level variables that users can reference (i.e.
    # ThermalPrinter.UPC_A, etc) and write code that is independent of the
    # printer firmware version.
    UPC_A = 0
    UPC_E = 1
    EAN13 = 2
    EAN8 = 3
    CODE39 = 4
    I25 = 5
    CODEBAR = 6
    CODE93 = 7
    CODE128 = 8
    CODE11 = 9
    MSI = 10

    def __init__(
        self, uart, byte_delay_s=0.00057346, dot_feed_s=0.0021, dot_print_s=0.03
    ):
        """Thermal printer class.  Requires a serial UART connection with at
        least the TX pin connected.  Take care connecting RX as the printer
        will output a 5V signal which can damage boards!  If RX is unconnected
        the only loss in functionality is the has_paper function, all other
        printer functions will continue to work.  The byte_delay_s, dot_feed_s,
        and dot_print_s values are delays which are used to prevent overloading
        the printer with data.  Use the default delays unless you fully
        understand the workings of the printer and how delays, baud rate,
        number of dots, heat time, etc. relate to each other.
        """
        super().__init__(
            uart,
            byte_delay_s=byte_delay_s,
            dot_feed_s=dot_feed_s,
            dot_print_s=dot_print_s,
        )

    def print_barcode(self, text, barcode_type):
        """Print a barcode with the specified text/number (the meaning
        varies based on the type of barcode) and type.  Type is a value from
        the datasheet or class-level variables like UPC_A, etc. for
        convenience.  Note the type value changes depending on the firmware
        version so use class-level values where possible!
        """
        assert 0 <= barcode_type <= 255
        assert 0 <= len(text) <= 255
        self.feed(1)  # Recent firmware can't print barcode w/o feed first???
        self.send_command("\x1DH\x02")  # Print label below barcode
        self.send_command("\x1Dw\x03")  # Barcode width 3 (0.375/1.0mm thin/thick)
        self.send_command("\x1Dk{0}".format(chr(barcode_type)))  # Barcode type
        # Pre-2.64 firmware prints the text and then a null character to end.
        # Instead of the length of text as a prefix.
        self.send_command(text)
        self.send_command("\x00")
        self._set_timeout((self._barcode_height + 40) * self._dot_print_s)
        self._column = 0

    def reset(self):
        """Reset the printer."""
        # Issue a reset command to the printer. (ESC + @)
        self.send_command("\x1B@")
        # Reset internal state:
        self._column = 0
        self._max_column = 32
        self._char_height = 24
        self._line_spacing = 6
        self._barcode_height = 50
        # Skip tab configuration on older printers.

    def feed(self, lines):
        """Advance paper by specified number of blank lines."""
        # Just send line feeds for older printers.
        for _ in range(lines):
            self._write_char("\n")

    def has_paper(self):
        """Return a boolean indicating if the printer has paper.  You MUST have
        the serial RX line hooked up for this to work.

        .. note::

            be VERY CAREFUL to ensure your board can handle a 5V serial
            input before hooking up the RX line!

        """
        # The paper check command is different for older firmware:
        self.send_command("\x1Br\x00")  # ESC + 'r' + 0
        status = self._uart.read(1)
        if status is None:
            return False
        return not status[0] & 0b00000100

    # Inverse on older printers (pre 2.68) uses a print mode bit instead of
    # specific commands.
    inverse = thermal_printer.ThermalPrinter._PrintModeBit(_INVERSE_MASK)
