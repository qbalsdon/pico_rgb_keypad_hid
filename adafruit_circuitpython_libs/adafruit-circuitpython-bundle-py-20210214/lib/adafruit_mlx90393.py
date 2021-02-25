# SPDX-FileCopyrightText: 2018 Kevin Townsend for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_mlx90393`
====================================================

This is a breakout for the Adafruit MLX90393 magnetometer sensor breakout.

* Author(s): ktown

Implementation Notes
--------------------

**Hardware:**

* Adafruit `MLX90393 Magnetometer Sensor Breakout Board
  <https://www.adafruit.com/product/4022>`_ (Product ID: 4022)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""

import time

try:
    import struct
except ImportError:
    import ustruct as struct

from adafruit_bus_device.i2c_device import I2CDevice
from micropython import const

__version__ = "2.0.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MLX90393.git"

_CMD_SB = const(0b00010000)  # Start burst mode
_CMD_SW = const(0b00100000)  # Start wakeup on change mode
_CMD_SM = const(0b00110000)  # Start single-measurement mode
_CMD_RM = const(0b01000000)  # Read measurement
_CMD_RR = const(0b01010000)  # Read register
_CMD_WR = const(0b01100000)  # Write register
_CMD_EX = const(0b10000000)  # Exit mode
_CMD_HR = const(0b11010000)  # Memory recall
_CMD_HS = const(0b11100000)  # Memory store
_CMD_RT = const(0b11110000)  # Reset
_CMD_NOP = const(0x00)  # NOP

_CMD_AXIS_ALL = const(0xE)  # X+Y+Z axis bits for commands

_CMD_REG_CONF1 = const(0x00)  # Gain
_CMD_REG_CONF2 = const(0x01)  # Burst, comm mode
_CMD_REG_CONF3 = const(0x02)  # Oversampling, Filter, Resolution
_CMD_REG_CONF4 = const(0x03)  # Sensitivity drift

# Gain settings
GAIN_5X = 0x0
GAIN_4X = 0x1
GAIN_3X = 0x2
GAIN_2_5X = 0x3
GAIN_2X = 0x4
GAIN_1_67X = 0x5
GAIN_1_33X = 0x6
GAIN_1X = 0x7
_GAIN_SHIFT = const(4)

# Resolution settings
RESOLUTION_16 = 0x0
RESOLUTION_17 = 0x1
RESOLUTION_18 = 0x2
RESOLUTION_19 = 0x3

# Filter settings
FILTER_0 = 0x0
FILTER_1 = 0x1
FILTER_2 = 0x2
FILTER_3 = 0x3
FILTER_4 = 0x4
FILTER_5 = 0x5
FILTER_6 = 0x6
FILTER_7 = 0x7

# Oversampling settings
OSR_0 = 0x0
OSR_1 = 0x1
OSR_2 = 0x2
OSR_3 = 0x3

_HALLCONF = const(0x0C)  # Hall plate spinning rate adjust.

STATUS_OK = 0x3

# The lookup table below allows you to convert raw sensor data to uT
# using the appropriate (gain/resolution-dependant) lsb-per-uT
# coefficient below. Note that the z axis has a different coefficient
# than the x and y axis. Assumes HALLCONF = 0x0C!
_LSB_LOOKUP = (
    # 5x gain: res0(xy)(z), res1(xy)(z), res2(xy)(z), res3(xy)(z)
    ((0.751, 1.210), (1.502, 2.420), (3.004, 4.840), (6.009, 9.680)),
    # 4x gain: res0(xy)(z), res1(xy)(z), res2(xy)(z), res3(xy)(z)
    ((0.601, 0.968), (1.202, 1.936), (2.403, 3.872), (4.840, 7.744)),
    # 3x gain: res0(xy)(z), res1(xy)(z), res2(xy)(z), res3(xy)(z)
    ((0.451, 0.726), (0.901, 1.452), (1.803, 2.904), (3.605, 5.808)),
    # 2.5x gain: res0(xy)(z), res1(xy)(z), res2(xy)(z), res3(xy)(z)
    ((0.376, 0.605), (0.751, 1.210), (1.502, 2.420), (3.004, 4.840)),
    # 2x gain: res0(xy)(z), res1(xy)(z), res2(xy)(z), res3(xy)(z)
    ((0.300, 0.484), (0.601, 0.968), (1.202, 1.936), (2.403, 3.872)),
    # 1.667x gain: res0(xy)(z), res1(xy)(z), res2(xy)(z), res3(xy)(z)
    ((0.250, 0.403), (0.501, 0.807), (1.001, 1.613), (2.003, 3.227)),
    # 1.333x gain: res0(xy)(z), res1(xy)(z), res2(xy)(z), res3(xy)(z)
    ((0.200, 0.323), (0.401, 0.645), (0.801, 1.291), (1.602, 2.581)),
    # 1x gain: res0(xy)(z), res1(xy)(z), res2(xy)(z), res3(xy)(z)
    ((0.150, 0.242), (0.300, 0.484), (0.601, 0.968), (1.202, 1.936)),
)

# Lookup table for conversion times for different filter and
# oversampling settings. Values taken from datasheet.
_TCONV_LOOKUP = (
    # OSR = 0      1       2       3
    (1.27, 1.84, 3.00, 5.30),  # DIG_FILT = 0
    (1.46, 2.23, 3.76, 6.84),  # DIG_FILT = 1
    (1.84, 3.00, 5.30, 9.91),  # DIG_FILT = 2
    (2.61, 4.53, 8.37, 16.05),  # DIG_FILT = 3
    (4.15, 7.60, 14.52, 28.34),  # DIG_FILT = 4
    (7.22, 13.75, 26.80, 52.92),  # DIG_FILT = 5
    (13.36, 26.04, 51.38, 102.07),  # DIG_FILT = 6
    (25.65, 50.61, 100.53, 200.37),  # DIF_FILT = 7
)


class MLX90393:  # pylint: disable=too-many-instance-attributes
    """
    Driver for the MLX90393 magnetometer.
    :param i2c_bus: The `busio.I2C` object to use. This is the only
    required parameter.
    :param int address: (optional) The I2C address of the device.
    :param int gain: (optional) The gain level to apply.
    :param bool debug: (optional) Enable debug output.
    """

    def __init__(
        self,
        i2c_bus,
        address=0x0C,
        gain=GAIN_1X,
        resolution=RESOLUTION_16,
        filt=FILTER_7,
        oversampling=OSR_3,
        debug=False,
    ):  # pylint: disable=too-many-arguments
        self.i2c_device = I2CDevice(i2c_bus, address)
        self._debug = debug
        self._status_last = 0
        self._res_x = self._res_y = self._res_z = resolution
        self._filter = filt
        self._osr = oversampling
        self._gain_current = gain

        # Put the device in a known state to start
        self.reset()

        # Set resolution to the supplied level
        self.resolution_x = self._res_x
        self.resolution_y = self._res_y
        self.resolution_z = self._res_z

        # Set filter to the supplied level
        self.filter = self._filter

        # Set oversampling to the supplied level
        self.oversampling = self._osr

        # Set gain to the supplied level
        self.gain = self._gain_current

    def _transceive(self, payload, rxlen=0):
        """
        Writes the specified 'payload' to the sensor
        Returns the results of the write attempt.
        :param bytearray payload: The byte array to write to the sensor
        :param rxlen: (optional) The numbers of bytes to read back (default=0)
        """
        # Read the response (+1 to account for the mandatory status byte!)
        data = bytearray(rxlen + 1)

        if len(payload) == 1:
            # Transceive with repeated start
            with self.i2c_device as i2c:
                i2c.write_then_readinto(payload, data)
        else:
            # Write 'value' to the specified register
            # TODO: Check this. It's weird that the write is accepted but the read is naked.
            with self.i2c_device as i2c:
                i2c.write(payload)

                while True:
                    try:
                        i2c.readinto(data)
                        if data[0]:
                            break
                    except OSError:
                        pass

        # Track status byte
        self._status_last = data[0]
        # Unpack data (status byte, big-endian 16-bit register value)
        if self._debug:
            print("\t[{}]".format(time.monotonic()))
            print("\t Writing :", [hex(b) for b in payload])
            print("\tResponse :", [hex(b) for b in data])
            print("\t  Status :", hex(data[0]))
        return data

    @property
    def last_status(self):
        """
        The last status byte received from the sensor.
        """
        return self._status_last

    @property
    def gain(self):
        """
        The gain setting for the device.
        """
        return self._gain_current

    @gain.setter
    def gain(self, value):
        if value > GAIN_1X or value < GAIN_5X:
            raise ValueError("Invalid GAIN setting")
        if self._debug:
            print("\tSetting gain: {}".format(value))
        self._gain_current = value
        self._transceive(
            bytes(
                [
                    _CMD_WR,
                    0x00,
                    self._gain_current << _GAIN_SHIFT | _HALLCONF,
                    (_CMD_REG_CONF1 & 0x3F) << 2,
                ]
            )
        )

    @property
    def resolution_x(self):
        """The X axis resolution."""
        return self._res_x

    @resolution_x.setter
    def resolution_x(self, resolution):
        self._set_resolution(0, resolution)
        self._res_x = resolution

    @property
    def resolution_y(self):
        """The Y axis resolution."""
        return self._res_y

    @resolution_y.setter
    def resolution_y(self, resolution):
        self._set_resolution(1, resolution)
        self._res_y = resolution

    @property
    def resolution_z(self):
        """The Z axis resolution."""
        return self._res_z

    @resolution_z.setter
    def resolution_z(self, resolution):
        self._set_resolution(2, resolution)
        self._res_z = resolution

    def _set_resolution(self, axis, resolution):
        if resolution not in (
            RESOLUTION_16,
            RESOLUTION_17,
            RESOLUTION_18,
            RESOLUTION_19,
        ):
            raise ValueError("Incorrect resolution setting.")
        shift = (5, 7, 9)[axis]
        mask = (0xFF9F, 0xFE7F, 0xF9FF)[axis]
        reg = self.read_reg(_CMD_REG_CONF3)
        reg &= mask
        reg |= (resolution & 0x3) << shift
        self.write_reg(_CMD_REG_CONF3, reg)

    @property
    def filter(self):
        """The filter level."""
        return self._filter

    @filter.setter
    def filter(self, level):
        if level not in range(8):
            raise ValueError("Incorrect filter level.")
        reg = self.read_reg(_CMD_REG_CONF3)
        reg &= 0xFFE3
        reg |= (level & 0x7) << 2
        self.write_reg(_CMD_REG_CONF3, reg)
        self._filter = level

    @property
    def oversampling(self):
        """The oversampling level."""
        return self._osr

    @oversampling.setter
    def oversampling(self, level):
        if level not in range(4):
            raise ValueError("Incorrect oversampling level.")
        reg = self.read_reg(_CMD_REG_CONF3)
        reg &= 0xFFFC
        reg |= level & 0x3
        self.write_reg(_CMD_REG_CONF3, reg)
        self._osr = level

    def display_status(self):
        """
        Prints out the content of the last status byte in a human-readble
        format.
        """
        avail = 0
        if self._status_last & 0b11 > 0:
            avail = 2 * (self._status_last & 0b11) + 2
        print("STATUS register = 0x{0:02X}".format(self._status_last))
        print("BURST Mode               :", (self._status_last & (1 << 7)) > 0)
        print("WOC Mode                 :", (self._status_last & (1 << 6)) > 0)
        print("SM Mode                  :", (self._status_last & (1 << 5)) > 0)
        print("Error                    :", (self._status_last & (1 << 4)) > 0)
        print("Single error detection   :", (self._status_last & (1 << 3)) > 0)
        print("Reset status             :", (self._status_last & (1 << 2)) > 0)
        print("Response bytes available :", avail)

    def read_reg(self, reg):
        """
        Gets the current value of the specified register.
        """
        # Write 'value' to the specified register
        payload = bytes([_CMD_RR, reg << 2])
        with self.i2c_device as i2c:
            i2c.write(payload)

        # Read the response (+1 to account for the mandatory status byte!)
        data = bytearray(3)
        with self.i2c_device as i2c:
            i2c.readinto(data)
        # Unpack data (status byte, big-endian 16-bit register value)
        self._status_last, val = struct.unpack(">BH", data)
        if self._debug:
            print("\t[{}]".format(time.monotonic()))
            print("\t Writing :", [hex(b) for b in payload])
            print("\tResponse :", [hex(b) for b in data])
            print("\t  Status :", hex(data[0]))
        return val

    def write_reg(self, reg, value):
        """
        Writes the 16-bit value to the supplied register.
        """
        self._transceive(
            bytes(
                [
                    _CMD_WR,
                    value >> 8,  # high byte
                    value & 0xFF,  # low byte
                    reg << 2,  # the register
                ]
            )
        )

    def reset(self):
        """
        Performs a software reset of the sensor.
        """
        if self._debug:
            print("Resetting sensor")
        time.sleep(2)
        self._transceive(bytes([_CMD_RT]))
        # burn a read post reset
        try:
            self.magnetic
        except OSError:
            pass
        return self._status_last

    @property
    def read_data(self):
        """
        Reads a single X/Y/Z sample from the magnetometer.
        """
        # Set conversion delay based on filter and oversampling
        delay = _TCONV_LOOKUP[self._filter][self._osr] / 1000  # per datasheet
        delay *= 1.1  # plus a little

        # Set the device to single measurement mode
        self._transceive(bytes([_CMD_SM | _CMD_AXIS_ALL]))

        # Insert a delay since we aren't using INTs for DRDY
        time.sleep(delay)

        # Read the 'XYZ' data
        data = self._transceive(bytes([_CMD_RM | _CMD_AXIS_ALL]), 6)

        # Unpack status and raw int values
        self._status_last = data[0]
        m_x = self._unpack_axis_data(self._res_x, data[1:3])
        m_y = self._unpack_axis_data(self._res_y, data[3:5])
        m_z = self._unpack_axis_data(self._res_z, data[5:7])

        # Return the raw int values if requested
        return m_x, m_y, m_z

    # pylint: disable=no-self-use
    def _unpack_axis_data(self, resolution, data):
        # see datasheet
        if resolution == RESOLUTION_19:
            (value,) = struct.unpack(">H", data)
            value -= 0x4000
        elif resolution == RESOLUTION_18:
            (value,) = struct.unpack(">H", data)
            value -= 0x8000
        else:
            value = struct.unpack(">h", data)[0]
        return value

    @property
    def magnetic(self):
        """
        The processed magnetometer sensor values.
        A 3-tuple of X, Y, Z axis values in microteslas that are signed floats.
        """
        x, y, z = self.read_data

        # Convert the raw integer values to uT based on gain and resolution
        x *= _LSB_LOOKUP[self._gain_current][self._res_x][0]
        y *= _LSB_LOOKUP[self._gain_current][self._res_y][0]
        z *= _LSB_LOOKUP[self._gain_current][self._res_z][1]

        return x, y, z
