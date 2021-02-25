# SPDX-FileCopyrightText: 2019 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ssd1305`
================================================================================

Framebuf (non-displayio) driver for SSD1305 displays

* Author(s): Melissa LeBlanc-Williamns, Bryan Siepert, Tony DiCola, Michael McWethy

Display init commands taken from
    https://www.buydisplay.com/download/democode/ER-OLED022-1_I2C_DemoCode.txt

Implementation Notes
--------------------
**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's framebuf library: https://github.com/adafruit/Adafruit_CircuitPython_framebuf

"""

# imports

__version__ = "1.3.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SSD1305.git"


import time

from micropython import const
from adafruit_bus_device import i2c_device, spi_device

try:
    import framebuf
except ImportError:
    import adafruit_framebuf as framebuf

__version__ = "1.3.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SSD1305.git"

# register definitions
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_LUT = const(0x91)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_MASTER_CONFIG = const(0xAD)
SET_COM_OUT_DIR = const(0xC0)
SET_COMSCAN_DEC = const(0xC8)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_AREA_COLOR = const(0xD8)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)


class _SSD1305(framebuf.FrameBuffer):
    """Base class for SSD1305 display driver"""

    # pylint: disable-msg=too-many-arguments
    def __init__(self, buffer, width, height, *, external_vcc, reset):
        super().__init__(buffer, width, height)
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        # reset may be None if not needed
        self.reset_pin = reset
        if self.reset_pin:
            self.reset_pin.switch_to_output(value=0)
        self.pages = self.height // 8
        self._column_offset = 0
        if self.height == 32:
            self._column_offset = 4  # hardcoded for now...
        # Note the subclass must initialize self.framebuf to a framebuffer.
        # This is necessary because the underlying data buffer is different
        # between I2C and SPI implementations (I2C needs an extra byte).
        self.poweron()
        self.init_display()

    def init_display(self):
        """Base class to initialize display"""
        for cmd in (
            SET_DISP | 0x00,  # off
            # timing and driving scheme
            SET_DISP_CLK_DIV,
            0x80,  # SET_DISP_CLK_DIV
            SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0 SET_SEG_REMAP
            SET_MUX_RATIO,
            self.height - 1,  # SET_MUX_RATIO
            SET_DISP_OFFSET,
            0x00,  # SET_DISP_OFFSET
            SET_MASTER_CONFIG,
            0x8E,  # Set Master Configuration
            SET_AREA_COLOR,
            0x05,  # Set Area Color Mode On/Off & Low Power Display Mode
            SET_MEM_ADDR,
            0x00,  # horizontal SET_MEM_ADDR ADD
            SET_DISP_START_LINE | 0x00,
            0x2E,  # SET_DISP_START_LINE ADD
            SET_COMSCAN_DEC,  # Set COM Output Scan Direction 64 to 1
            SET_COM_PIN_CFG,
            0x12,  # SET_COM_PIN_CFG
            SET_LUT,
            0x3F,
            0x3F,
            0x3F,
            0x3F,  # Current drive pulse width of BANK0, Color A, B, C
            SET_CONTRAST,
            0xFF,  # maximum SET_CONTRAST to maximum
            SET_PRECHARGE,
            0xD2,  # SET_PRECHARGE orig: 0xd9, 0x22 if self.external_vcc else 0xf1,
            SET_VCOM_DESEL,
            0x34,  # SET_VCOM_DESEL 0xdb, 0x30, $ 0.83* Vcc
            SET_NORM_INV,  # not inverted SET_NORM_INV
            SET_ENTIRE_ON,  # output follows RAM contents  SET_ENTIRE_ON
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,  # SET_CHARGE_PUMP
            SET_DISP | 0x01,
        ):  # //--turn on oled panel
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        """Turn off the display (nothing visible)"""
        self.write_cmd(SET_DISP | 0x00)

    def contrast(self, contrast):
        """Adjust the contrast"""
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        """Invert all pixels on the display"""
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def write_framebuf(self):
        """Derived class must implement this"""
        raise NotImplementedError

    def write_cmd(self, cmd):
        """Derived class must implement this"""
        raise NotImplementedError

    def poweron(self):
        "Reset device and turn on the display."
        if self.reset_pin:
            self.reset_pin.value = 1
            time.sleep(0.001)
            self.reset_pin.value = 0
            time.sleep(0.010)
            self.reset_pin.value = 1
            time.sleep(0.010)
        self.write_cmd(SET_DISP | 0x01)

    def show(self):
        """Update the display"""
        xpos0 = 0
        xpos1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            xpos0 += 32
            xpos1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(xpos0 + self._column_offset)
        self.write_cmd(xpos1 + self._column_offset)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_framebuf()


class SSD1305_I2C(_SSD1305):
    """
    I2C class for SSD1305

    :param width: the width of the physical screen in pixels,
    :param height: the height of the physical screen in pixels,
    :param i2c: the I2C peripheral to use,
    :param addr: the 8-bit bus address of the device,
    :param external_vcc: whether external high-voltage source is connected.
    :param reset: if needed, DigitalInOut designating reset pin
    """

    def __init__(
        self, width, height, i2c, *, addr=0x3C, external_vcc=False, reset=None
    ):
        self.i2c_device = i2c_device.I2CDevice(i2c, addr)
        self.addr = addr
        self.temp = bytearray(2)
        # Add an extra byte to the data buffer to hold an I2C data/command byte
        # to use hardware-compatible I2C transactions.  A memoryview of the
        # buffer is used to mask this byte from the framebuffer operations
        # (without a major memory hit as memoryview doesn't copy to a separate
        # buffer).
        self.buffer = bytearray(((height // 8) * width) + 1)
        self.buffer[0] = 0x40  # Set first byte of data buffer to Co=0, D/C=1
        super().__init__(
            memoryview(self.buffer)[1:],
            width,
            height,
            external_vcc=external_vcc,
            reset=reset,
        )

    def write_cmd(self, cmd):
        """Send a command to the SPI device"""
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        with self.i2c_device:
            self.i2c_device.write(self.temp)

    def write_framebuf(self):
        """Blast out the frame buffer using a single I2C transaction to support
        hardware I2C interfaces."""
        with self.i2c_device:
            self.i2c_device.write(self.buffer)


# pylint: disable-msg=too-many-arguments
class SSD1305_SPI(_SSD1305):
    """
    SPI class for SSD1305

    :param width: the width of the physical screen in pixels,
    :param height: the height of the physical screen in pixels,
    :param spi: the SPI peripheral to use,
    :param dc: the data/command pin to use (often labeled "D/C"),
    :param reset: the reset pin to use,
    :param cs: the chip-select pin to use (sometimes labeled "SS").
    """

    # pylint: disable=no-member
    # Disable should be reconsidered when refactor can be tested.
    def __init__(
        self,
        width,
        height,
        spi,
        dc,
        reset,
        cs,
        *,
        external_vcc=False,
        baudrate=8000000,
        polarity=0,
        phase=0
    ):
        self.rate = 10 * 1024 * 1024
        dc.switch_to_output(value=0)
        self.spi_device = spi_device.SPIDevice(
            spi, cs, baudrate=baudrate, polarity=polarity, phase=phase
        )
        self.dc_pin = dc
        self.buffer = bytearray((height // 8) * width)
        super().__init__(
            memoryview(self.buffer),
            width,
            height,
            external_vcc=external_vcc,
            reset=reset,
        )

    def write_cmd(self, cmd):
        """Send a command to the SPI device"""
        self.dc_pin.value = 0
        with self.spi_device as spi:
            spi.write(bytearray([cmd]))

    def write_framebuf(self):
        """write to the frame buffer via SPI"""
        self.dc_pin.value = 1
        with self.spi_device as spi:
            spi.write(self.buffer)
