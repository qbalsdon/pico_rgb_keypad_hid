# SPDX-FileCopyrightText: 2020 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_bitbangio`
================================================================================

A library for adding bitbang I2C and SPI to CircuitPython without the built-in bitbangio module.
The interface is intended to be the same as bitbangio and therefore there is no bit order or chip
select functionality. If your board supports bitbangio, it is recommended to use that instead
as the timing should be more reliable.

* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

# imports
from time import monotonic, sleep
from digitalio import DigitalInOut

__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BitbangIO.git"

MSBFIRST = 0
LSBFIRST = 1


class _BitBangIO:
    """Base class for subclassing only"""

    def __init__(self):
        self._locked = False

    def try_lock(self):
        """Attempt to grab the lock. Return True on success, False if the lock is already taken."""
        if self._locked:
            return False
        self._locked = True
        return True

    def unlock(self):
        """Release the lock so others may use the resource."""
        if self._locked:
            self._locked = False
        else:
            raise ValueError("Not locked")

    def _check_lock(self):
        if not self._locked:
            raise RuntimeError("First call try_lock()")
        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.deinit()

    # pylint: disable=no-self-use
    def deinit(self):
        """Free any hardware used by the object."""
        return

    # pylint: enable=no-self-use


class I2C(_BitBangIO):
    """Software-based implementation of the I2C protocol over GPIO pins."""

    def __init__(self, scl, sda, *, frequency=400000, timeout=1):
        """Initialize bitbang (or software) based I2C.  Must provide the I2C
        clock, and data pin numbers.
        """
        super().__init__()

        # Set pins as outputs/inputs.
        self._scl = DigitalInOut(scl)
        self._scl.switch_to_output()
        self._scl.value = 1

        # SDA flips between being input and output
        self._sda = DigitalInOut(sda)
        self._sda.switch_to_output()
        self._sda.value = 1

        self._delay = 1 / frequency / 2
        self._timeout = timeout

    def deinit(self):
        """Free any hardware used by the object."""
        self._sda.deinit()
        self._scl.deinit()

    def scan(self):
        """Perform an I2C Device Scan"""
        found = []
        if self._check_lock():
            for address in range(0, 0x80):
                if self._probe(address):
                    found.append(address)
        return found

    def writeto(self, address, buffer, *, start=0, end=None):
        """Write data from the buffer to an address"""
        if end is None:
            end = len(buffer)
        if self._check_lock():
            self._write(address, buffer[start:end], True)

    def readfrom_into(self, address, buffer, *, start=0, end=None):
        """Read data from an address and into the buffer"""
        if end is None:
            end = len(buffer)

        if self._check_lock():
            readin = self._read(address, end - start)
            for i in range(end - start):
                buffer[i + start] = readin[i]

    def writeto_then_readfrom(
        self,
        address,
        buffer_out,
        buffer_in,
        *,
        out_start=0,
        out_end=None,
        in_start=0,
        in_end=None
    ):
        """Write data from buffer_out to an address and then
        read data from an address and into buffer_in
        """
        if out_end is None:
            out_end = len(buffer_out)
        if in_end is None:
            in_end = len(buffer_in)
        if self._check_lock():
            self.writeto(address, buffer_out, start=out_start, end=out_end)
            self.readfrom_into(address, buffer_in, start=in_start, end=in_end)

    def _scl_low(self):
        self._scl.value = 0

    def _sda_low(self):
        self._sda.value = 0

    def _scl_release(self):
        """Release and let the pullups lift"""
        # Use self._timeout to add clock stretching
        self._scl.value = 1

    def _sda_release(self):
        """Release and let the pullups lift"""
        # Use self._timeout to add clock stretching
        self._sda.value = 1

    def _start(self):
        self._sda_release()
        self._scl_release()
        sleep(self._delay)
        self._sda_low()
        sleep(self._delay)

    def _stop(self):
        self._scl_low()
        sleep(self._delay)
        self._sda_low()
        sleep(self._delay)
        self._scl_release()
        sleep(self._delay)
        self._sda_release()
        sleep(self._delay)

    def _repeated_start(self):
        self._scl_low()
        sleep(self._delay)
        self._sda_release()
        sleep(self._delay)
        self._scl_release()
        sleep(self._delay)
        self._sda_low()
        sleep(self._delay)

    def _write_byte(self, byte):
        for bit_position in range(8):
            self._scl_low()
            sleep(self._delay)
            if byte & (0x80 >> bit_position):
                self._sda_release()
            else:
                self._sda_low()
            sleep(self._delay)
            self._scl_release()
            sleep(self._delay)
        self._scl_low()
        sleep(self._delay * 2)

        self._scl_release()
        sleep(self._delay)

        self._sda.switch_to_input()
        ack = self._sda.value
        self._sda.switch_to_output()
        sleep(self._delay)

        self._scl_low()

        return not ack

    def _read_byte(self, ack=False):
        self._scl_low()
        sleep(self._delay)

        data = 0
        self._sda.switch_to_input()
        for _ in range(8):
            self._scl_release()
            sleep(self._delay)
            data = (data << 1) | int(self._sda.value)
            sleep(self._delay)
            self._scl_low()
            sleep(self._delay)
        self._sda.switch_to_output()

        if ack:
            self._sda_low()
        else:
            self._sda_release()
        sleep(self._delay)
        self._scl_release()
        sleep(self._delay)
        return data & 0xFF

    def _probe(self, address):
        self._start()
        ok = self._write_byte(address << 1)
        self._stop()
        return ok > 0

    def _write(self, address, buffer, transmit_stop):
        self._start()
        if not self._write_byte(address << 1):
            raise RuntimeError("Device not responding at 0x{:02X}".format(address))
        for byte in buffer:
            self._write_byte(byte)
        if transmit_stop:
            self._stop()

    def _read(self, address, length):
        self._start()
        if not self._write_byte(address << 1 | 1):
            raise RuntimeError("Device not responding at 0x{:02X}".format(address))
        buffer = bytearray(length)
        for byte_position in range(length):
            buffer[byte_position] = self._read_byte(ack=(byte_position != length - 1))
        self._stop()
        return buffer


class SPI(_BitBangIO):
    """Software-based implementation of the SPI protocol over GPIO pins."""

    def __init__(self, clock, MOSI=None, MISO=None):
        """Initialize bit bang (or software) based SPI.  Must provide the SPI
        clock, and optionally MOSI and MISO pin numbers. If MOSI is set to None
        then writes will be disabled and fail with an error, likewise for MISO
        reads will be disabled.
        """
        super().__init__()

        while self.try_lock():
            pass

        self._mosi = None
        self._miso = None

        self.configure()
        self.unlock()

        # Set pins as outputs/inputs.
        self._sclk = DigitalInOut(clock)
        self._sclk.switch_to_output()

        if MOSI is not None:
            self._mosi = DigitalInOut(MOSI)
            self._mosi.switch_to_output()

        if MISO is not None:
            self._miso = DigitalInOut(MISO)
            self._miso.switch_to_input()

    def deinit(self):
        """Free any hardware used by the object."""
        self._sclk.deinit()
        if self._miso:
            self._miso.deinit()
        if self._mosi:
            self._mosi.deinit()

    def configure(self, *, baudrate=100000, polarity=0, phase=0, bits=8):
        """Configures the SPI bus. Only valid when locked."""
        if self._check_lock():
            if not isinstance(baudrate, int):
                raise ValueError("baudrate must be an integer")
            if not isinstance(bits, int):
                raise ValueError("bits must be an integer")
            if bits < 1 or bits > 8:
                raise ValueError("bits must be in the range of 1-8")
            if polarity not in (0, 1):
                raise ValueError("polarity must be either 0 or 1")
            if phase not in (0, 1):
                raise ValueError("phase must be either 0 or 1")
            self._baudrate = baudrate
            self._polarity = polarity
            self._phase = phase
            self._bits = bits
            self._half_period = (1 / self._baudrate) / 2  # 50% Duty Cyle delay

    def _wait(self, start=None):
        """Wait for up to one half cycle"""
        while (start + self._half_period) > monotonic():
            pass
        return monotonic()  # Return current time

    def write(self, buffer, start=0, end=None):
        """Write the data contained in buf. Requires the SPI being locked.
        If the buffer is empty, nothing happens.
        """
        # Fail MOSI is not specified.
        if self._mosi is None:
            raise RuntimeError("Write attempted with no MOSI pin specified.")
        if end is None:
            end = len(buffer)

        if self._check_lock():
            start_time = monotonic()
            for byte in buffer[start:end]:
                for bit_position in range(self._bits):
                    bit_value = byte & 0x80 >> bit_position
                    # Set clock to base
                    if not self._phase:  # Mode 0, 2
                        self._mosi.value = bit_value
                    self._sclk.value = self._polarity
                    start_time = self._wait(start_time)

                    # Flip clock off base
                    if self._phase:  # Mode 1, 3
                        self._mosi.value = bit_value
                    self._sclk.value = not self._polarity
                    start_time = self._wait(start_time)

            # Return pins to base positions
            self._mosi.value = 0
            self._sclk.value = self._polarity

    # pylint: disable=too-many-branches
    def readinto(self, buffer, start=0, end=None, write_value=0):
        """Read into the buffer specified by buf while writing zeroes. Requires the SPI being
        locked. If the number of bytes to read is 0, nothing happens.
        """
        if self._miso is None:
            raise RuntimeError("Read attempted with no MISO pin specified.")
        if end is None:
            end = len(buffer)

        if self._check_lock():
            start_time = monotonic()
            for byte_position, _ in enumerate(buffer[start:end]):
                for bit_position in range(self._bits):
                    bit_mask = 0x80 >> bit_position
                    bit_value = write_value & 0x80 >> bit_position
                    # Return clock to base
                    self._sclk.value = self._polarity
                    start_time = self._wait(start_time)
                    # Handle read on leading edge of clock.
                    if not self._phase:  # Mode 0, 2
                        if self._mosi is not None:
                            self._mosi.value = bit_value
                        if self._miso.value:
                            # Set bit to 1 at appropriate location.
                            buffer[byte_position] |= bit_mask
                        else:
                            # Set bit to 0 at appropriate location.
                            buffer[byte_position] &= ~bit_mask
                    # Flip clock off base
                    self._sclk.value = not self._polarity
                    start_time = self._wait(start_time)
                    # Handle read on trailing edge of clock.
                    if self._phase:  # Mode 1, 3
                        if self._mosi is not None:
                            self._mosi.value = bit_value
                        if self._miso.value:
                            # Set bit to 1 at appropriate location.
                            buffer[byte_position] |= bit_mask
                        else:
                            # Set bit to 0 at appropriate location.
                            buffer[byte_position] &= ~bit_mask

            # Return pins to base positions
            self._mosi.value = 0
            self._sclk.value = self._polarity

    def write_readinto(
        self,
        buffer_out,
        buffer_in,
        *,
        out_start=0,
        out_end=None,
        in_start=0,
        in_end=None
    ):
        """Write out the data in buffer_out while simultaneously reading data into buffer_in.
        The lengths of the slices defined by buffer_out[out_start:out_end] and
        buffer_in[in_start:in_end] must be equal. If buffer slice lengths are
        both 0, nothing happens.
        """
        if self._mosi is None:
            raise RuntimeError("Write attempted with no MOSI pin specified.")
        if self._miso is None:
            raise RuntimeError("Read attempted with no MISO pin specified.")
        if out_end is None:
            out_end = len(buffer_out)
        if in_end is None:
            in_end = len(buffer_in)
        if len(buffer_out[out_start:out_end]) != len(buffer_in[in_start:in_end]):
            raise RuntimeError("Buffer slices must be equal length")

        if self._check_lock():
            start_time = monotonic()
            for byte_position, _ in enumerate(buffer_out[out_start:out_end]):
                for bit_position in range(self._bits):
                    bit_mask = 0x80 >> bit_position
                    bit_value = (
                        buffer_out[byte_position + out_start] & 0x80 >> bit_position
                    )
                    in_byte_position = byte_position + in_start
                    # Return clock to 0
                    self._sclk.value = self._polarity
                    start_time = self._wait(start_time)
                    # Handle read on leading edge of clock.
                    if not self._phase:  # Mode 0, 2
                        self._mosi.value = bit_value
                        if self._miso.value:
                            # Set bit to 1 at appropriate location.
                            buffer_in[in_byte_position] |= bit_mask
                        else:
                            # Set bit to 0 at appropriate location.
                            buffer_in[in_byte_position] &= ~bit_mask
                    # Flip clock off base
                    self._sclk.value = not self._polarity
                    start_time = self._wait(start_time)
                    # Handle read on trailing edge of clock.
                    if self._phase:  # Mode 1, 3
                        self._mosi.value = bit_value
                        if self._miso.value:
                            # Set bit to 1 at appropriate location.
                            buffer_in[in_byte_position] |= bit_mask
                        else:
                            # Set bit to 0 at appropriate location.
                            buffer_in[in_byte_position] &= ~bit_mask

            # Return pins to base positions
            self._mosi.value = 0
            self._sclk.value = self._polarity

    # pylint: enable=too-many-branches

    @property
    def frequency(self):
        """Return the currently configured baud rate"""
        return self._baudrate
