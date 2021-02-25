# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_sgp40`
================================================================================

CircuitPython library for the Adafruit SGP40 Air Quality Sensor / VOC Index Sensor Breakouts


* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* Adafruit SGP40 Breakout <https://www.adafruit.com/product/4829>

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases



 * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
 * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register

"""
from time import sleep
from struct import unpack_from
import adafruit_bus_device.i2c_device as i2c_device

__version__ = "1.0.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SGP40.git"

_WORD_LEN = 2
# no point in generating this each time
_READ_CMD = [0x26, 0x0F, 0x7F, 0xFF, 0x8F, 0x66, 0x66, 0x93]


class SGP40:
    """Class to use the SGP40 Ambient Light and UV sensor"""

    def __init__(self, i2c, address=0x59):
        self.i2c_device = i2c_device.I2CDevice(i2c, address)
        self._command_buffer = bytearray(2)

        self.initialize()

    def initialize(self):
        """Reset the sensor to it's initial unconfigured state and configure it with sensible
        defaults so it can be used"""
        # check serial number
        self._command_buffer[0] = 0x36
        self._command_buffer[1] = 0x82
        serialnumber = self._read_word_from_command(3)

        if serialnumber[0] != 0x0000:
            raise RuntimeError("Serial number does not match")

        # Check feature set
        self._command_buffer[0] = 0x20
        self._command_buffer[1] = 0x2F
        featureset = self._read_word_from_command()
        if featureset[0] != 0x3220:

            raise RuntimeError("Feature set does not match: %s" % hex(featureset[0]))

        # VocAlgorithm_init(&voc_algorithm_params)

        # Self Test
        self._command_buffer[0] = 0x28
        self._command_buffer[1] = 0x0E
        self_test = self._read_word_from_command(delay_ms=250)
        if self_test[0] != 0xD400:
            raise RuntimeError("Self test failed")
        self._reset()

    def _reset(self):
        # This is a general call Reset. Several sensors may see this and it doesn't appear to
        # ACK before resetting
        self._command_buffer[0] = 0x00
        self._command_buffer[1] = 0x06
        try:
            self._read_word_from_command(delay_ms=50)
        except OSError:
            # print("\tGot expected OSError from reset")
            pass
        sleep(1)

    @property
    def raw(self):
        """The raw gas value"""
        # recycle a single buffer
        self._command_buffer = bytearray(_READ_CMD)
        read_value = self._read_word_from_command(delay_ms=250)
        self._command_buffer = bytearray(2)
        return read_value[0]

    def _read_word_from_command(
        self,
        delay_ms=10,
        readlen=1,
    ):
        """_read_word_from_command - send a given command code and read the result back

        Args:
            delay_ms (int, optional): The delay between write and read, in milliseconds.
                Defaults to 10ms
            readlen (int, optional): The number of bytes to read. Defaults to 1.
        """
        # TODO: Take 2-byte command as int (0x280E, 0x0006) and packinto command buffer

        with self.i2c_device as i2c:
            i2c.write(self._command_buffer)

        sleep(round(delay_ms * 0.001, 3))

        if readlen is None:
            return None
        readdata_buffer = []

        # The number of bytes to rad back, based on the number of words to read
        replylen = readlen * (_WORD_LEN + 1)
        # recycle buffer for read/write w/length
        replybuffer = bytearray(replylen)

        with self.i2c_device as i2c:
            i2c.readinto(replybuffer, end=replylen)

        # print("Buffer:")
        # print(["0x{:02X}".format(i) for i in replybuffer])

        for i in range(0, replylen, 3):
            if not self._check_crc8(replybuffer[i : i + 2], replybuffer[i + 2]):
                raise RuntimeError("CRC check failed while reading data")
            readdata_buffer.append(unpack_from(">H", replybuffer[i : i + 2])[0])

        return readdata_buffer

    @staticmethod
    def _check_crc8(crc_buffer, crc_value):
        crc = 0xFF
        for byte in crc_buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc_value == (crc & 0xFF)  # check against the bottom 8 bits
