# SPDX-FileCopyrightText: 2018 Michael Schroeder for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_fram`
====================================================

CircuitPython/Python library to support the I2C and SPI FRAM Breakouts.

* Author(s): Michael Schroeder

Implementation Notes
--------------------

**Hardware:**

 * Adafruit `I2C Non-Volatile FRAM Breakout
   <https://www.adafruit.com/product/1895>`_ (Product ID: 1895)
 * Adafruit `SPI Non-Volatile FRAM Breakout
   <https://www.adafruit.com/product/1897>`_ (Product ID: 1897)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

 * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

# imports
from micropython import const

__version__ = "1.3.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FRAM.git"

_MAX_SIZE_I2C = const(0x8000)
_MAX_SIZE_SPI = const(0x2000)

_I2C_MANF_ID = const(0x0A)
_I2C_PROD_ID = const(0x510)

_SPI_MANF_ID = const(0x04)
_SPI_PROD_ID = const(0x302)

_SPI_OPCODE_WREN = const(0x6)  # Set write enable latch
_SPI_OPCODE_WRDI = const(0x4)  # Reset write enable latch
_SPI_OPCODE_RDSR = const(0x5)  # Read status register
_SPI_OPCODE_WRSR = const(0x1)  # Write status register
_SPI_OPCODE_READ = const(0x3)  # Read memory code
_SPI_OPCODE_WRITE = const(0x2)  # Write memory code
_SPI_OPCODE_RDID = const(0x9F)  # Read device ID


class FRAM:
    """
    Driver base for the FRAM Breakout.
    """

    def __init__(self, max_size, write_protect=False, wp_pin=None):
        self._max_size = max_size
        self._wp = write_protect
        self._wraparound = False
        if not wp_pin is None:
            self._wp_pin = wp_pin
            # Make sure write_prot is set to output
            self._wp_pin.switch_to_output()
            self._wp_pin.value = self._wp
        else:
            self._wp_pin = wp_pin

    @property
    def write_wraparound(self):
        """Determines if sequential writes will wrapaound highest memory address
        (``len(FRAM) - 1``) address. If ``False``, and a requested write will
        extend beyond the maximum size, an exception is raised.
        """
        return self._wraparound

    @write_wraparound.setter
    def write_wraparound(self, value):
        if not value in (True, False):
            raise ValueError("Write wraparound must be 'True' or 'False'.")
        self._wraparound = value

    @property
    def write_protected(self):
        """The status of write protection. Default value on initialization is
        ``False``.

        When a ``WP`` pin is supplied during initialization, or using
        ``write_protect_pin``, the status is tied to that pin and enables
        hardware-level protection.

        When no ``WP`` pin is supplied, protection is only at the software
        level in this library.
        """
        return self._wp if self._wp_pin is None else self._wp_pin.value

    def __len__(self):
        """The size of the current FRAM chip. This is one more than the highest
        address location that can be read or written to.

        .. code-block:: python

            fram = adafruit_fram.FRAM_xxx() # xxx = 'I2C' or 'SPI'

            # size returned by len()
            len(fram)

            # can be used with range
            for i in range(0, len(fram))
        """
        return self._max_size

    def __getitem__(self, address):
        """Read the value at the given index, or values in a slice.

        .. code-block:: python

            # read single index
            fram[0]

            # read values 0 thru 9 with a slice
            fram[0:9]
        """
        if isinstance(address, int):
            if not 0 <= address < self._max_size:
                raise ValueError(
                    "Address '{0}' out of range. It must be 0 <= address < {1}.".format(
                        address, self._max_size
                    )
                )
            buffer = bytearray(1)
            read_buffer = self._read_address(address, buffer)
        elif isinstance(address, slice):
            if address.step is not None:
                raise ValueError("Slice stepping is not currently available.")

            regs = list(
                range(
                    address.start if address.start is not None else 0,
                    address.stop + 1 if address.stop is not None else self._max_size,
                )
            )
            if regs[0] < 0 or (regs[0] + len(regs)) > self._max_size:
                raise ValueError(
                    "Address slice out of range. It must be 0 <= [starting address"
                    ":stopping address] < {0}.".format(self._max_size)
                )

            buffer = bytearray(len(regs))
            read_buffer = self._read_address(regs[0], buffer)

        return read_buffer

    def __setitem__(self, address, value):
        """Write the value at the given starting index.

        .. code-block:: python

            # write single index
            fram[0] = 1

            # write values 0 thru 4 with a list
            fram[0] = [0,1,2,3]
        """
        if self.write_protected:
            raise RuntimeError("FRAM currently write protected.")

        if isinstance(address, int):
            if not isinstance(value, (int, bytearray, list, tuple)):
                raise ValueError(
                    "Data must be a single integer, or a bytearray," " list, or tuple."
                )
            if not 0 <= address < self._max_size:
                raise ValueError(
                    "Address '{0}' out of range. It must be 0 <= address < {1}.".format(
                        address, self._max_size
                    )
                )

            self._write(address, value, self._wraparound)

        elif isinstance(address, slice):
            raise ValueError("Slicing not available during write operations.")

    def _read_address(self, address, read_buffer):
        # Implemented by subclass
        raise NotImplementedError

    def _write(self, start_address, data, wraparound):
        # Implemened by subclass
        raise NotImplementedError


class FRAM_I2C(FRAM):
    """I2C class for FRAM.

    :param: ~busio.I2C i2c_bus: The I2C bus the FRAM is connected to.
    :param: int address: I2C address of FRAM. Default address is ``0x50``.
    :param: bool write_protect: Turns on/off initial write protection.
                                Default is ``False``.
    :param: wp_pin: (Optional) Physical pin connected to the ``WP`` breakout pin.
                    Must be a ``digitalio.DigitalInOut`` object.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, i2c_bus, address=0x50, write_protect=False, wp_pin=None):
        from adafruit_bus_device.i2c_device import (  # pylint: disable=import-outside-toplevel
            I2CDevice as i2cdev,
        )

        dev_id_addr = 0xF8 >> 1
        read_buf = bytearray(3)
        with i2cdev(i2c_bus, dev_id_addr) as dev_id:
            dev_id.write_then_readinto(bytearray([(address << 1)]), read_buf)
        manf_id = (read_buf[0] << 4) + (read_buf[1] >> 4)
        prod_id = ((read_buf[1] & 0x0F) << 8) + read_buf[2]
        if (manf_id != _I2C_MANF_ID) and (prod_id != _I2C_PROD_ID):
            raise OSError("FRAM I2C device not found.")

        self._i2c = i2cdev(i2c_bus, address)
        super().__init__(_MAX_SIZE_I2C, write_protect, wp_pin)

    def _read_address(self, address, read_buffer):
        write_buffer = bytearray(2)
        write_buffer[0] = address >> 8
        write_buffer[1] = address & 0xFF
        with self._i2c as i2c:
            i2c.write_then_readinto(write_buffer, read_buffer)
        return read_buffer

    def _write(self, start_address, data, wraparound=False):
        # Decided against using the chip's "Page Write", since that would require
        # doubling the memory usage by creating a buffer that includes the passed
        # in data so that it can be sent all in one `i2c.write`. The single-write
        # method is slower, and forces us to handle wraparound, but I feel this
        # is a better tradeoff for limiting the memory required for large writes.
        buffer = bytearray(3)
        if not isinstance(data, int):
            data_length = len(data)
        else:
            data_length = 1
            data = [data]
        if (start_address + data_length) > self._max_size:
            if wraparound:
                pass
            else:
                raise ValueError(
                    "Starting address + data length extends beyond"
                    " FRAM maximum address. Use ``write_wraparound`` to"
                    " override this warning."
                )
        with self._i2c as i2c:
            for i in range(0, data_length):
                if not (start_address + i) > self._max_size - 1:
                    buffer[0] = (start_address + i) >> 8
                    buffer[1] = (start_address + i) & 0xFF
                else:
                    buffer[0] = ((start_address + i) - self._max_size + 1) >> 8
                    buffer[1] = ((start_address + i) - self._max_size + 1) & 0xFF
                buffer[2] = data[i]
                i2c.write(buffer)

    # pylint: disable=no-member
    @FRAM.write_protected.setter
    def write_protected(self, value):
        if value not in (True, False):
            raise ValueError("Write protected value must be 'True' or 'False'.")
        self._wp = value
        if not self._wp_pin is None:
            self._wp_pin.value = value


class FRAM_SPI(FRAM):
    """SPI class for FRAM.

    :param: ~busio.SPI spi_bus: The SPI bus the FRAM is connected to.
    :param: ~digitalio.DigitalInOut spi_cs: The SPI CS pin.
    :param: bool write_protect: Turns on/off initial write protection.
                                Default is ``False``.
    :param: wp_pin: (Optional) Physical pin connected to the ``WP`` breakout pin.
                    Must be a ``digitalio.DigitalInOut`` object.
    :param int baudrate: SPI baudrate to use. Default is ``1000000``.
    :param int max_size: Size of FRAM in Bytes. Default is ``8192``.
    """

    # pylint: disable=too-many-arguments,too-many-locals
    def __init__(
        self,
        spi_bus,
        spi_cs,
        write_protect=False,
        wp_pin=None,
        baudrate=100000,
        max_size=_MAX_SIZE_SPI,
    ):
        from adafruit_bus_device.spi_device import (  # pylint: disable=import-outside-toplevel
            SPIDevice as spidev,
        )

        _spi = spidev(spi_bus, spi_cs, baudrate=baudrate)

        read_buffer = bytearray(4)
        with _spi as spi:
            spi.write(bytearray([_SPI_OPCODE_RDID]))
            spi.readinto(read_buffer)
        prod_id = (read_buffer[3] << 8) + (read_buffer[2])
        if (read_buffer[0] != _SPI_MANF_ID) and (prod_id != _SPI_PROD_ID):
            raise OSError("FRAM SPI device not found.")

        self._spi = _spi
        super().__init__(max_size, write_protect, wp_pin)

    def _read_address(self, address, read_buffer):
        write_buffer = bytearray(4)
        write_buffer[0] = _SPI_OPCODE_READ
        if self._max_size > 0xFFFF:
            write_buffer[1] = (address >> 16) & 0xFF
            write_buffer[2] = (address >> 8) & 0xFF
            write_buffer[3] = address & 0xFF
        else:
            write_buffer[1] = (address >> 8) & 0xFF
            write_buffer[2] = address & 0xFF

        with self._spi as spi:
            spi.write(write_buffer)
            spi.readinto(read_buffer)
        return read_buffer

    def _write(self, start_address, data, wraparound=False):
        buffer = bytearray(4)
        if not isinstance(data, int):
            data_length = len(data)
        else:
            data_length = 1
            data = [data]
        if (start_address + data_length) > self._max_size:
            if wraparound:
                pass
            else:
                raise ValueError(
                    "Starting address + data length extends beyond"
                    " FRAM maximum address. Use 'wraparound=True' to"
                    " override this warning."
                )
        with self._spi as spi:
            spi.write(bytearray([_SPI_OPCODE_WREN]))
        with self._spi as spi:
            buffer[0] = _SPI_OPCODE_WRITE
            if self._max_size > 0xFFFF:
                buffer[1] = (start_address >> 16) & 0xFF
                buffer[2] = (start_address >> 8) & 0xFF
                buffer[3] = start_address & 0xFF
            else:
                buffer[1] = (start_address >> 8) & 0xFF
                buffer[2] = start_address & 0xFF
            spi.write(buffer)
            for i in range(0, data_length):
                spi.write(bytearray([data[i]]))
        with self._spi as spi:
            spi.write(bytearray([_SPI_OPCODE_WRDI]))

    @FRAM.write_protected.setter
    def write_protected(self, value):
        # While it is possible to protect block ranges on the SPI chip,
        # it seems superfluous to do so. So, block protection always protects
        # the entire memory (BP0 and BP1).
        if value not in (True, False):
            raise ValueError("Write protected value must be 'True' or 'False'.")
        self._wp = value
        write_buffer = bytearray(2)
        write_buffer[0] = _SPI_OPCODE_WRSR
        if value:
            write_buffer[1] = 0x8C  # set WPEN, BP0, and BP1
        else:
            write_buffer[1] = 0x00  # clear WPEN, BP0, and BP1
        with self._spi as spi:
            spi.write(write_buffer)
        if self._wp_pin is not None:
            self._wp_pin.value = value
