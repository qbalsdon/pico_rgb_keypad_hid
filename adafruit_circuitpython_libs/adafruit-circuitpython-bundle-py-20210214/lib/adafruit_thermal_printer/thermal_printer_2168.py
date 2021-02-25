# SPDX-FileCopyrightText: 2020 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Grzegorz Nowicki for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_thermal_printer.thermal_printer_2168.ThermalPrinter`
==============================================================

Thermal printer control module built to work with small serial thermal
receipt printers.  Note that these printers have many different firmware
versions and care must be taken to select the appropriate module inside this
package for your firmware printer:

* thermal_printer_2168 = Printers with firmware version 2.168+.
* thermal_printer = The latest printers with firmware version 2.68 up to 2.168
* thermal_printer_264 = Printers with firmware version 2.64 up to 2.68.
* thermal_printer_legacy = Printers with firmware version before 2.64.

* Author(s): Tony DiCola, Grzegorz Nowicki
"""


import adafruit_thermal_printer.thermal_printer as thermal_printer


# pylint: disable=too-many-arguments
class ThermalPrinter(thermal_printer.ThermalPrinter):
    """Thermal printer for printers with firmware version from 2.168"""

    # Barcode types.  These vary based on the firmware version so are made
    # as class-level variables that users can reference (i.e.
    # ThermalPrinter.UPC_A, etc) and write code that is independent of the
    # printer firmware version.
    UPC_A = 65
    UPC_E = 66
    EAN13 = 67
    EAN8 = 68
    CODE39 = 69
    ITF = 70
    CODABAR = 71
    CODE93 = 72
    CODE128 = 73

    def __init__(
        self,
        uart,
        byte_delay_s=0.00057346,
        dot_feed_s=0.0021,
        dot_print_s=0.03,
        auto_warm_up=True,
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
            auto_warm_up=auto_warm_up,
        )

    def warm_up(self, heat_time=120):
        """Apparently there are no parameters for setting darkness in 2.168
        (at least commands from 2.68 dont work), So it is little
        compatibility method to reuse older code.
        """
        self._set_timeout(0.5)  # Half second delay for printer to initialize.
        self.reset()
