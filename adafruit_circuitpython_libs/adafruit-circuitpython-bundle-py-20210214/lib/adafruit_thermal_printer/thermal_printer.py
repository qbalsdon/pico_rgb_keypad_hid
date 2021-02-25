# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_thermal_printer.thermal_printer` - Thermal Printer Driver
=====================================================================

Thermal printer control module built to work with small serial thermal
receipt printers.  Note that these printers have many different firmware
versions and care must be taken to select the appropriate module inside this
package for your firmware printer:

* thermal_printer = The latest printers with firmware version 2.68+
* thermal_printer_264 = Printers with firmware version 2.64 up to 2.68.
* thermal_printer_legacy = Printers with firmware version before 2.64.

* Author(s): Tony DiCola

Implementation Notes
--------------------

**Hardware:**

* Mini `Thermal Receipt Printer
  <https://www.adafruit.com/product/597>`_ (Product ID: 597)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases

"""
import time

from micropython import const


__version__ = "1.3.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Thermal_Printer.git"


# Internally used constants.
_UPDOWN_MASK = const(1 << 2)
_BOLD_MASK = const(1 << 3)
_DOUBLE_HEIGHT_MASK = const(1 << 4)
_DOUBLE_WIDTH_MASK = const(1 << 5)
_STRIKE_MASK = const(1 << 6)

# External constants:
JUSTIFY_LEFT = const(0)
JUSTIFY_CENTER = const(1)
JUSTIFY_RIGHT = const(2)
SIZE_SMALL = const(0)
SIZE_MEDIUM = const(1)
SIZE_LARGE = const(2)
UNDERLINE_THIN = const(0)
UNDERLINE_THICK = const(1)


# Disable too many instance members warning.  This is not something pylint can
# reasonably infer--the complexity of instance variables is required for proper
# printer function.  Disable this warning.
# pylint: disable=too-many-instance-attributes

# Disable too many public members warning.  Again this is not something pylint
# can reasonably decide.  Thermal printers require lots of control functions.
# Disable this warning.
# pylint: disable=too-many-public-methods

# Thermal printer class for printers with firmware version 2.68 and higher.
# Do not modify this class without fully understanding its coupling to the
# legacy and 2.64+ version printer which inherit from it.  These legacy printer
# classes override specific functions which have different requirements of
# behavior between different versions of printer firmware.  Firmware printers
# vary _greatly_ in their command set--there is not a clean abstraction.  The
# assumption here is that this class is the master with logic for the most
# recent (2.68+) firmware printers.  Older firmware versions inherit and
# override behavior where necessary.  It is highly, HIGHLY recommended you
# carefully study the Arduino thermal printer library code and fully
# understand all the firmware differences (notice where the library changes
# behavior with the firmware version define):
# https://github.com/adafruit/Adafruit-Thermal-Printer-Library
# Bottom line: don't touch this code without understanding the big picture or
# else it will be very easy to break or introduce subtle incompatibilities with
# older firmware printers.
class ThermalPrinter:
    """Thermal printer for printers with firmware version from 2.68 and below 2.168"""

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

    class _PrintModeBit:
        # Internal descriptor class to simplify printer mode change properties.
        # This is tightly coupled to the ThermalPrinter implementation--do not
        # change it without fully understanding these dependencies on the
        # internal _set_print_mode and other methods!

        # pylint doesn't have the context to realize this internal class is
        # explicitly tightly coupled to the parent class implementation.
        # Therefore disable its warnings about protected access--this access
        # is required and by design.
        # pylint: disable=protected-access

        # Another odd pylint case, it seems to not realize this is a descriptor
        # which by design only implements get, set, init.  As a result workaround
        # this pylint issue by disabling the warning.
        # pylint: disable=too-few-public-methods
        def __init__(self, mask):
            self._mask = mask

        def __get__(self, obj, objtype):
            return obj._print_mode & self._mask > 0

        def __set__(self, obj, val):
            if val:
                obj._set_print_mode(self._mask)
            else:
                obj._unset_print_mode(self._mask)

        # pylint: enable=protected-access
        # pylint: enable=too-few-public-methods

    def __init__(
        self,
        uart,
        *,
        byte_delay_s=0.00057346,
        dot_feed_s=0.0021,
        dot_print_s=0.03,
        auto_warm_up=True
    ):
        """Thermal printer class.  Requires a serial UART connection with at
        least the TX pin connected.  Take care connecting RX as the printer
        will output a 5V signal which can damage boards!  If RX is unconnected
        the only loss in functionality is the has_paper function, all other
        printer functions will continue to work.  The byte_delay_s, dot_feed_s,
        and dot_print_s values are delays which are used to prevent overloading
        the printer with data.  Use the default delays unless you fully
        understand the workings of the printer and how delays, baud rate,
        number of dots, heat time, etc. relate to each other.  Can set
        auto_warm_up to a boolean value (default True) to automatically call
        the warm_up function which will initialize the printer (but can take a
        significant amount of time, on the order 0.5-5 seconds, be warned!).
        """
        self.max_chunk_height = 255
        self._resume = 0
        self._uart = uart
        self._print_mode = 0
        self._column = 0
        self._max_column = 32
        self._char_height = 24
        self._line_spacing = 6
        self._barcode_height = 50
        self.up_down_mode = True
        # pylint: disable=line-too-long
        # Byte delay calculated based on assumption of 19200 baud.
        # From Arduino library code, see formula here:
        #   https://github.com/adafruit/Adafruit-Thermal-Printer-Library/blob/master/Adafruit_Thermal.cpp#L50-L53
        # pylint: enable=line-too-long
        self._byte_delay_s = byte_delay_s
        self._dot_feed_s = dot_feed_s
        self._dot_print_s = dot_print_s
        self.reset()
        if auto_warm_up:
            self.warm_up()

    def _set_timeout(self, period_s):
        # Set a timeout before future commands can be sent.
        self._resume = time.monotonic() + period_s

    def _wait_timeout(self):
        # Ensure the timeout that was previously set has passed (will busy wait).
        while time.monotonic() < self._resume:
            pass

    def _write_char(self, char):
        # Write a single character to the printer.
        if char == "\r":
            return  # Strip carriage returns by skipping them.
        self._wait_timeout()
        self._uart.write(bytes(char, "ascii"))
        delay = self._byte_delay_s
        # Add extra delay for newlines or moving past the last column.
        if char == "\n" or self._column == self._max_column:
            if self._column == 0:
                # Feed line delay
                delay += (self._char_height + self._line_spacing) * self._dot_feed_s
            else:
                # Text line delay
                delay += (self._char_height * self._dot_print_s) + (
                    self._line_spacing * self._dot_feed_s
                )
            self._column = 0
        else:
            self._column += 1
        self._set_timeout(delay)

    def _write_print_mode(self):
        # Write the printer mode to the printer.
        self.send_command(
            "\x1B!{0}".format(chr(self._print_mode))
        )  # ESC + '!' + print mode byte
        # Adjust character height and column count based on print mode.
        self._char_height = 48 if self._print_mode & _DOUBLE_HEIGHT_MASK else 24
        self._max_column = 16 if self._print_mode & _DOUBLE_WIDTH_MASK else 32

    def _set_print_mode(self, mask):
        # Enable the specified bits of the print mode.
        self._print_mode |= mask & 0xFF
        self._write_print_mode()

    def _unset_print_mode(self, mask):
        # Disable the specified bits of the print mode.
        self._print_mode &= ~(mask & 0xFF)
        self._write_print_mode()

    def send_command(self, command):
        """Send a command string to the printer."""
        self._uart.write(bytes(command, "ascii"))

    # Do initialization in warm_up instead of the initializer because this
    # initialization takes a long time (5 seconds) and shouldn't happen during
    # object creation (users need explicit control of when to start it).
    def warm_up(self, heat_time=120):
        """Initialize the printer.  Can specify an optional heat_time keyword
        to override the default heating timing of 1.2 ms.  See the datasheet
        for details on the heating time value (duration in 10uS increments).
        Note that calling this function will take about half a second for the
        printer to intialize and warm up.
        """
        assert 0 <= heat_time <= 255
        self._set_timeout(0.5)  # Half second delay for printer to initialize.
        self.reset()
        # ESC 7 n1 n2 n3 Setting Control Parameter Command
        # n1 = "max heating dots" 0-255 -- max number of thermal print head
        #      elements that will fire simultaneously.  Units = 8 dots (minus 1).
        #      Printer default is 7 (64 dots, or 1/6 of 384-dot width), this code
        #      sets it to 11 (96 dots, or 1/4 of width).
        # n2 = "heating time" 3-255 -- duration that heating dots are fired.
        #      Units = 10 us.  Printer default is 80 (800 us), this code sets it
        #      to value passed (default 120, or 1.2 ms -- a little longer than
        #      the default because we've increased the max heating dots).
        # n3 = "heating interval" 0-255 -- recovery time between groups of
        #      heating dots on line; possibly a function of power supply.
        #      Units = 10 us.  Printer default is 2 (20 us), this code sets it
        #      to 40 (throttled back due to 2A supply).
        # More heating dots = more peak current, but faster printing speed.
        # More heating time = darker print, but slower printing speed and
        # possibly paper 'stiction'.  More heating interval = clearer print,
        # but slower printing speed.
        # Send ESC + '7' (print settings) + heating dots, heat time, heat interval.
        self.send_command("\x1B7\x0B{0}\x28".format(chr(heat_time)))
        # Print density description from manual:
        # DC2 # n Set printing density
        # D4..D0 of n is used to set the printing density.  Density is
        # 50% + 5% * n(D4-D0) printing density.
        # D7..D5 of n is used to set the printing break time.  Break time
        # is n(D7-D5)*250us.
        print_density = 10  # 100% (? can go higher, text is darker but fuzzy)
        print_break_time = 2  # 500 uS
        dc2_value = (print_break_time << 5) | print_density
        self.send_command("\x12#{0}".format(chr(dc2_value)))  # DC2 + '#' + value

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
        # Configure tab stops on recent printers.
        # ESC + 'D' + tab stop value list ending with null to terminate.
        self.send_command("\x1BD\x04\x08\x10\x14\x18\x1C\x00")

    def print(self, text, end="\n"):
        """Print a line of text.  Optionally specify the end keyword to
        override the new line printed after the text (set to None to disable
        the new line entirely).
        """
        for char in text:
            self._write_char(char)
        if end is not None:
            self._write_char(end)

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
        # Write length and then string (note this only works with 2.64+).
        self.send_command(chr(len(text)))
        self.send_command(text)
        self._set_timeout((self._barcode_height + 40) * self._dot_print_s)
        self._column = 0

    def _print_bitmap(self, width, height, data):
        """Print a bitmap image of the specified width, height and data bytes.
        Data bytes must be in 1-bit per pixel format, i.e. each byte represents
        8 pixels of image data along a row of the image.  You will want to
        pre-process your images with a script, you CANNOT send .jpg/.bmp/etc.
        image formats.  See this Processing sketch for preprocessing:
        https://github.com/adafruit/Adafruit-Thermal-Printer-Library/blob/master/processing/bitmapImageConvert/bitmapImageConvert.pde

        .. note:: This is currently not working because it appears the bytes are
        sent too slowly and the printer gets confused with not enough data being
        sent to it in the expected time.
        """
        assert len(data) >= (width // 8) * height
        row_bytes = (width + 7) // 8  # Round up to next byte boundary.
        row_bytes_clipped = min(row_bytes, 48)  # 384 pixels max width.
        chunk_height_limit = 256 // row_bytes_clipped
        # Clip chunk height within the 1 to max range.
        chunk_height_limit = max(1, min(self.max_chunk_height, chunk_height_limit))
        i = 0
        for row_start in range(0, height, chunk_height_limit):
            # Issue up to chunkHeightLimit rows at a time.
            chunk_height = min(height - row_start, chunk_height_limit)
            self.send_command(
                "\x12*{0}{1}".format(chr(chunk_height), chr(row_bytes_clipped))
            )
            for _ in range(chunk_height):
                for _ in range(row_bytes_clipped):
                    # Drop down to low level UART access to avoid newline and
                    # other bitmap values being misinterpreted.
                    self._wait_timeout()
                    self._uart.write(chr(data[i]))
                    i += 1
                i += row_bytes - row_bytes_clipped
            self._set_timeout(chunk_height * self._dot_print_s)
        self._column = 0

    def test_page(self):
        """Print a test page."""
        self.send_command("\x12T")  # DC2 + 'T' for test page
        # Delay for 26 lines w/text (ea. 24 dots high) +
        # 26 text lines (feed 6 dots) + blank line
        self._set_timeout(
            self._dot_print_s * 24 * 26 + self._dot_feed_s * (6 * 26 + 30)
        )

    def set_defaults(self):
        """Set default printing and text options.  This is useful to reset back
        to a good state after printing different size, weight, etc. text.
        """
        self.online()
        self.justify = JUSTIFY_LEFT
        self.size = SIZE_SMALL
        self.underline = None
        self.inverse = False
        self.upside_down = False
        # this should work in 2.68 according to user manual v 4.0
        # but it does't work with 2.168 hence i implemented the below
        self.up_down_mode = True
        self.double_height = False
        self.double_width = False
        self.strike = False
        self.bold = False
        self._set_line_height(30)
        self._set_barcode_height(50)
        self._set_charset()
        self._set_code_page()

    def _set_justify(self, val):
        assert 0 <= val <= 2
        if val == JUSTIFY_LEFT:
            self.send_command("\x1Ba\x00")  # ESC + 'a' + 0
        elif val == JUSTIFY_CENTER:
            self.send_command("\x1Ba\x01")  # ESC + 'a' + 1
        elif val == JUSTIFY_RIGHT:
            self.send_command("\x1Ba\x02")  # ESC + 'a' + 2

    # pylint: disable=line-too-long
    # Write-only property, can't assume we can read state from the printer
    # since there is no command for it and hooking up RX is discouraged
    # (5V will damage many boards).
    justify = property(
        None,
        _set_justify,
        None,
        "Set the justification of text, must be a value of JUSTIFY_LEFT, JUSTIFY_CENTER, or JUSTIFY_RIGHT.",
    )
    # pylint: enable=line-too-long

    def _set_size(self, val):
        assert 0 <= val <= 2
        if val == SIZE_SMALL:
            self._char_height = 24
            self._max_column = 32
            self.send_command("\x1D!\x00")  # ASCII GS + '!' + 0x00
        elif val == SIZE_MEDIUM:
            self._char_height = 48
            self._max_column = 32
            self.send_command("\x1D!\x01")  # ASCII GS + '!' + 0x01
        elif val == SIZE_LARGE:
            self._char_height = 48
            self._max_column = 16
            self.send_command("\x1D!\x11")  # ASCII GS + '!' + 0x11
        self._column = 0

    # pylint: disable=line-too-long
    # Write-only property, can't assume we can read state from the printer
    # since there is no command for it and hooking up RX is discouraged
    # (5V will damage many boards).
    size = property(
        None,
        _set_size,
        None,
        "Set the size of text, must be a value of SIZE_SMALL, SIZE_MEDIUM, or SIZE_LARGE.",
    )
    # pylint: enable=line-too-long

    def _set_underline(self, val):
        assert val is None or (0 <= val <= 1)
        if val is None:
            # Turn off underline.
            self.send_command("\x1B-\x00")  # ESC + '-' + 0
        elif val == UNDERLINE_THIN:
            self.send_command("\x1B-\x01")  # ESC + '-' + 1
        elif val == UNDERLINE_THICK:
            self.send_command("\x1B-\x02")  # ESC + '-' + 2

    # pylint: disable=line-too-long
    # Write-only property, can't assume we can read state from the printer
    # since there is no command for it and hooking up RX is discouraged
    # (5V will damage many boards).
    underline = property(
        None,
        _set_underline,
        None,
        "Set the underline state of the text, must be None (off), UNDERLINE_THIN, or UNDERLINE_THICK.",
    )
    # pylint: enable=line-too-long

    def _set_inverse(self, inverse):
        # Set the inverse printing state to enabled disabled with the specified
        # boolean value.  This requires printer firmare 2.68+
        if inverse:
            self.send_command("\x1DB\x01")  # ESC + 'B' + 1
        else:
            self.send_command("\x1DB\x00")  # ESC + 'B' + 0

    # pylint: disable=line-too-long
    # Write-only property, can't assume we can read inverse state from the
    # printer since there is no command for it and hooking up RX is discouraged
    # (5V will damage many boards).
    inverse = property(
        None,
        _set_inverse,
        None,
        "Set the inverse printing mode boolean to enable or disable inverse printing.",
    )
    # pylint: enable=line-too-long

    def _set_up_down_mode(self, up_down_mode):
        if up_down_mode:
            self.send_command("\x1B{\x01")

        else:
            self.send_command("\x1B{\x00")

    up_down_mode = property(
        None, _set_up_down_mode, None, "Turns on/off upside-down printing mode"
    )
    # The above Should work in 2.68 so its here and not in 2.168 module

    upside_down = _PrintModeBit(_UPDOWN_MASK)  # Don't work in 2.168 hence the above

    double_height = _PrintModeBit(_DOUBLE_HEIGHT_MASK)

    double_width = _PrintModeBit(_DOUBLE_WIDTH_MASK)

    strike = _PrintModeBit(_STRIKE_MASK)

    bold = _PrintModeBit(_BOLD_MASK)

    def feed(self, lines):
        """Advance paper by specified number of blank lines."""
        assert 0 <= lines <= 255
        self.send_command("\x1Bd{0}".format(chr(lines)))
        self._set_timeout(self._dot_feed_s * self._char_height)
        self._column = 0

    def feed_rows(self, rows):
        """Advance paper by specified number of pixel rows."""
        assert 0 <= rows <= 255
        self.send_command("\x1BJ{0}".format(chr(rows)))
        self._set_timeout(rows * self._dot_feed_s)
        self._column = 0

    def flush(self):
        """Flush data pending in the printer."""
        self.send_command("\f")

    def offline(self):
        """Put the printer into an offline state.  No other commands can be
        sent until an online call is made.
        """
        self.send_command("\x1B=\x00")  # ESC + '=' + 0

    def online(self):
        """Put the printer into an online state after previously put offline."""
        self.send_command("\x1B=\x01")  # ESC + '=' + 1

    def has_paper(self):
        """Return a boolean indicating if the printer has paper.  You MUST have
        the serial RX line hooked up for this to work.  NOTE: be VERY CAREFUL
        to ensure your board can handle a 5V serial input before hooking up
        the RX line!
        """
        # This only works with firmware 2.64+:
        self.send_command("\x1Bv\x00")  # ESC + 'v' + 0
        status = self._uart.read(1)
        if status is None:
            return False
        return not status[0] & 0b00000100

    def _set_line_height(self, height):
        """Set the line height in pixels.  This is the total amount of space
        between lines, including the height of text.  The smallest value is 24
        and the largest is 255.
        """
        assert 24 <= height <= 255
        self._line_spacing = height - 24
        self.send_command("\x1B3{0}".format(chr(height)))  # ESC + '3' + height

    def _set_barcode_height(self, height):
        """Set the barcode height in pixels.  Must be a value 1 - 255."""
        assert 1 <= height <= 255
        self._barcode_height = height
        self.send_command("\x1Dh{0}".format(chr(height)))  # ASCII GS + 'h' + height

    def _set_charset(self, charset=0):
        """Alters the character set for ASCII characters 0x23-0x7E.  See
        datasheet for details on character set values (0-15).  Note this is only
        supported on more recent firmware printers!
        """
        assert 0 <= charset <= 15
        self.send_command("\x1BR{0}".format(chr(charset)))  # ESC + 'R' + charset

    def _set_code_page(self, code_page=0):
        """Select alternate code page for upper ASCII symbols 0x80-0xFF.  See
        datasheet for code page values (0 - 47).  Note this is only supported
        on more recent firmware printers!
        """
        assert 0 <= code_page <= 47
        self.send_command("\x1Bt{0}".format(chr(code_page)))  # ESC + 't' + code page

    def tab(self):
        """Print a tab (i.e. move to next 4 character block).  Note this is
        only supported on more recent firmware printers!"""
        self.send_command("\t")
        # Increment to the next position that's every 4 spaces.
        # I.e. increment by 4 and go to the floor/first position of the block.
        self._column = (self._column + 4) & 0b11111100
