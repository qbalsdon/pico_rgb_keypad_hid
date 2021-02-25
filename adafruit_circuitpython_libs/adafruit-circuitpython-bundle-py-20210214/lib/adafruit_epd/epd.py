# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.epd` - Adafruit EPD - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit ePaper display breakouts
* Author(s): Dean Miller
"""

import time
from micropython import const
from digitalio import Direction
from adafruit_epd import mcp_sram

__version__ = "2.7.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"


class Adafruit_EPD:  # pylint: disable=too-many-instance-attributes, too-many-public-methods
    """Base class for EPD displays"""

    BLACK = const(0)
    WHITE = const(1)
    INVERSE = const(2)
    RED = const(3)
    DARK = const(4)
    LIGHT = const(5)

    def __init__(
        self, width, height, spi, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin
    ):  # pylint: disable=too-many-arguments
        self._width = width
        self._height = height

        # Setup reset pin, if we have one
        self._rst = rst_pin
        if rst_pin:
            self._rst.direction = Direction.OUTPUT

        # Setup busy pin, if we have one
        self._busy = busy_pin
        if busy_pin:
            self._busy.direction = Direction.INPUT

        # Setup dc pin (required)
        self._dc = dc_pin
        self._dc.direction = Direction.OUTPUT
        self._dc.value = False

        # Setup cs pin (required)
        self._cs = cs_pin
        self._cs.direction = Direction.OUTPUT
        self._cs.value = True

        # SPI interface (required)
        self.spi_device = spi
        while not self.spi_device.try_lock():
            time.sleep(0.01)
        self.spi_device.configure(baudrate=1000000)  # 1 Mhz
        self.spi_device.unlock()

        self._spibuf = bytearray(1)
        self._single_byte_tx = False

        self.sram = None
        if sramcs_pin:
            self.sram = mcp_sram.Adafruit_MCP_SRAM(sramcs_pin, spi)

        self._buf = bytearray(3)
        self._buffer1_size = self._buffer2_size = 0
        self._buffer1 = self._buffer2 = None
        self._framebuf1 = self._framebuf2 = None
        self._colorframebuf = self._blackframebuf = None
        self._black_inverted = self._color_inverted = True
        self.hardware_reset()

    def display(self):  # pylint: disable=too-many-branches
        """show the contents of the display buffer"""
        self.power_up()

        self.set_ram_address(0, 0)

        if self.sram:
            while not self.spi_device.try_lock():
                time.sleep(0.01)
            self.sram.cs_pin.value = False
            # send read command
            self._buf[0] = mcp_sram.Adafruit_MCP_SRAM.SRAM_READ
            # send start address
            self._buf[1] = 0
            self._buf[2] = 0
            self.spi_device.write(self._buf, end=3)
            self.spi_device.unlock()

        # first data byte from SRAM will be transfered in at the
        # same time as the EPD command is transferred out
        databyte = self.write_ram(0)

        while not self.spi_device.try_lock():
            time.sleep(0.01)
        self._dc.value = True

        if self.sram:
            for _ in range(self._buffer1_size):
                databyte = self._spi_transfer(databyte)
            self.sram.cs_pin.value = True
        else:
            for databyte in self._buffer1:
                self._spi_transfer(databyte)

        self._cs.value = True
        self.spi_device.unlock()
        time.sleep(0.002)

        if self.sram:
            while not self.spi_device.try_lock():
                time.sleep(0.01)
            self.sram.cs_pin.value = False
            # send read command
            self._buf[0] = mcp_sram.Adafruit_MCP_SRAM.SRAM_READ
            # send start address
            self._buf[1] = (self._buffer1_size >> 8) & 0xFF
            self._buf[2] = self._buffer1_size & 0xFF
            self.spi_device.write(self._buf, end=3)
            self.spi_device.unlock()

        if self._buffer2_size != 0:
            # first data byte from SRAM will be transfered in at the
            # same time as the EPD command is transferred out
            databyte = self.write_ram(1)

            while not self.spi_device.try_lock():
                time.sleep(0.01)
            self._dc.value = True

            if self.sram:
                for _ in range(self._buffer2_size):
                    databyte = self._spi_transfer(databyte)
                self.sram.cs_pin.value = True
            else:
                for databyte in self._buffer2:
                    self._spi_transfer(databyte)

            self._cs.value = True
            self.spi_device.unlock()
        else:
            if self.sram:
                self.sram.cs_pin.value = True

        self.update()

    def hardware_reset(self):
        """If we have a reset pin, do a hardware reset by toggling it"""
        if self._rst:
            self._rst.value = False
            time.sleep(0.1)
            self._rst.value = True
            time.sleep(0.1)

    def command(self, cmd, data=None, end=True):
        """Send command byte to display."""
        self._cs.value = True
        self._dc.value = False
        self._cs.value = False

        while not self.spi_device.try_lock():
            time.sleep(0.01)
        ret = self._spi_transfer(cmd)

        if data is not None:
            self._dc.value = True
            for b in data:
                self._spi_transfer(b)
        if end:
            self._cs.value = True
        self.spi_device.unlock()

        return ret

    def _spi_transfer(self, databyte):
        """Transfer one byte, toggling the cs pin if required by the EPD chipset"""
        self._spibuf[0] = databyte
        if self._single_byte_tx:
            self._cs.value = False
        self.spi_device.write_readinto(self._spibuf, self._spibuf)
        if self._single_byte_tx:
            self._cs.value = True
        return self._spibuf[0]

    def power_up(self):
        """Power up the display in preparation for writing RAM and updating.
        must be implemented in subclass"""
        raise NotImplementedError()

    def power_down(self):
        """Power down the display, must be implemented in subclass"""
        raise NotImplementedError()

    def update(self):
        """Update the display from internal memory, must be implemented in subclass"""
        raise NotImplementedError()

    def write_ram(self, index):
        """Send the one byte command for starting the RAM write process. Returns
        the byte read at the same time over SPI. index is the RAM buffer, can be
        0 or 1 for tri-color displays. must be implemented in subclass"""
        raise NotImplementedError()

    def set_ram_address(self, x, y):
        """Set the RAM address location, must be implemented in subclass"""
        raise NotImplementedError()

    def set_black_buffer(self, index, inverted):
        """Set the index for the black buffer data (0 or 1) and whether its inverted"""
        if index == 0:
            self._blackframebuf = self._framebuf1
        elif index == 1:
            self._blackframebuf = self._framebuf2
        else:
            raise RuntimeError("Buffer index must be 0 or 1")
        self._black_inverted = inverted

    def set_color_buffer(self, index, inverted):
        """Set the index for the color buffer data (0 or 1) and whether its inverted"""
        if index == 0:
            self._colorframebuf = self._framebuf1
        elif index == 1:
            self._colorframebuf = self._framebuf2
        else:
            raise RuntimeError("Buffer index must be 0 or 1")
        self._color_inverted = inverted

    def _color_dup(self, func, args, color):
        black = getattr(self._blackframebuf, func)
        red = getattr(self._colorframebuf, func)
        if self._blackframebuf is self._colorframebuf:  # monochrome
            black(*args, color=(color != Adafruit_EPD.WHITE) != self._black_inverted)
        else:
            black(*args, color=(color == Adafruit_EPD.BLACK) != self._black_inverted)
            red(*args, color=(color == Adafruit_EPD.RED) != self._color_inverted)

    def pixel(self, x, y, color):
        """draw a single pixel in the display buffer"""
        self._color_dup("pixel", (x, y), color)

    def fill(self, color):
        """fill the screen with the passed color"""
        red_fill = ((color == Adafruit_EPD.RED) != self._color_inverted) * 0xFF
        black_fill = ((color == Adafruit_EPD.BLACK) != self._black_inverted) * 0xFF

        if self.sram:
            self.sram.erase(0x00, self._buffer1_size, black_fill)
            self.sram.erase(self._buffer1_size, self._buffer2_size, red_fill)
        else:
            self._blackframebuf.fill(black_fill)
            self._colorframebuf.fill(red_fill)

    def rect(self, x, y, width, height, color):  # pylint: disable=too-many-arguments
        """draw a rectangle"""
        self._color_dup("rect", (x, y, width, height), color)

    def fill_rect(
        self, x, y, width, height, color
    ):  # pylint: disable=too-many-arguments
        """fill a rectangle with the passed color"""
        self._color_dup("fill_rect", (x, y, width, height), color)

    def line(self, x_0, y_0, x_1, y_1, color):  # pylint: disable=too-many-arguments
        """Draw a line from (x_0, y_0) to (x_1, y_1) in passed color"""
        self._color_dup("line", (x_0, y_0, x_1, y_1), color)

    def text(self, string, x, y, color, *, font_name="font5x8.bin"):
        """Write text string at location (x, y) in given color, using font file"""
        if self._blackframebuf is self._colorframebuf:  # monochrome
            self._blackframebuf.text(
                string,
                x,
                y,
                font_name=font_name,
                color=(color != Adafruit_EPD.WHITE) != self._black_inverted,
            )
        else:
            self._blackframebuf.text(
                string,
                x,
                y,
                font_name=font_name,
                color=(color == Adafruit_EPD.BLACK) != self._black_inverted,
            )
            self._colorframebuf.text(
                string,
                x,
                y,
                font_name=font_name,
                color=(color == Adafruit_EPD.RED) != self._color_inverted,
            )

    @property
    def width(self):
        """The width of the display, accounting for rotation"""
        if self.rotation in (0, 2):
            return self._width
        return self._height

    @property
    def height(self):
        """The height of the display, accounting for rotation"""
        if self.rotation in (0, 2):
            return self._height
        return self._width

    @property
    def rotation(self):
        """The rotation of the display, can be one of (0, 1, 2, 3)"""
        return self._framebuf1.rotation

    @rotation.setter
    def rotation(self, val):
        self._framebuf1.rotation = val
        if self._framebuf2:
            self._framebuf2.rotation = val

    def hline(self, x, y, width, color):
        """draw a horizontal line"""
        self.fill_rect(x, y, width, 1, color)

    def vline(self, x, y, height, color):
        """draw a vertical line"""
        self.fill_rect(x, y, 1, height, color)

    def image(self, image):
        """Set buffer to value of Python Imaging Library image.  The image should
        be in RGB mode and a size equal to the display size.
        """
        imwidth, imheight = image.size
        if imwidth != self.width or imheight != self.height:
            raise ValueError(
                "Image must be same dimensions as display ({0}x{1}).".format(
                    self.width, self.height
                )
            )
        if self.sram:
            raise RuntimeError("PIL image is not for use with SRAM assist")
        # Grab all the pixels from the image, faster than getpixel.
        pix = image.load()
        # clear out any display buffers
        self.fill(Adafruit_EPD.WHITE)

        if image.mode == "RGB":  # RGB Mode
            for y in range(image.size[1]):
                for x in range(image.size[0]):
                    pixel = pix[x, y]
                    if (pixel[1] < 0x80 <= pixel[0]) and (pixel[2] < 0x80):
                        # reddish
                        self.pixel(x, y, Adafruit_EPD.RED)
                    elif (pixel[0] < 0x80) and (pixel[1] < 0x80) and (pixel[2] < 0x80):
                        # dark
                        self.pixel(x, y, Adafruit_EPD.BLACK)
        elif image.mode == "L":  # Grayscale
            for y in range(image.size[1]):
                for x in range(image.size[0]):
                    pixel = pix[x, y]
                    if pixel < 0x80:
                        self.pixel(x, y, Adafruit_EPD.BLACK)
        else:
            raise ValueError("Image must be in mode RGB or mode L.")
