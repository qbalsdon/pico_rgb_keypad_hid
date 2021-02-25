# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_ms8607`
================================================================================

CircuitPython driver for the MS8607 PTH sensor


* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* `Adafruit MS8607 Breakout <https:#www.adafruit.com/products/4716>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https:#github.com/adafruit/circuitpython/releases

 * Adafruit's Bus Device library: https:#github.com/adafruit/Adafruit_CircuitPython_BusDevice
 * Adafruit's Register library: https:#github.com/adafruit/Adafruit_CircuitPython_Register

"""

__version__ = "1.0.4"
__repo__ = "https:#github.com/adafruit/Adafruit_CircuitPython_MS8607.git"


from struct import unpack_from
from time import sleep
from micropython import const
import adafruit_bus_device.i2c_device as i2c_device

_MS8607_HSENSOR_ADDR = const(0x40)  #
_MS8607_PTSENSOR_ADDR = const(0x76)  #


_MS8607_HUM_USR_REG_RESOLUTION_MASK = const(0x81)
_MS8607_HUM_USR_REG_HEATER_EN_MASK = const(0x4)
_MS8607_HUM_COEFF_MUL = const(125)  #
_MS8607_HUM_COEFF_ADD = const(-6)  #

_MS8607_HUM_CMD_READ_HOLD = const(0xE5)  #
_MS8607_HUM_CMD_READ_NO_HOLD = const(0xF5)  #
_MS8607_HUM_CMD_READ_USR = const(0xE7)
_MS8607_HUM_CMD_WRITE_USR = const(0xE6)
_MS8607_HUM_CMD_RESET = const(0xFE)  #


_MS8607_PT_CALIB_ROM_ADDR = const(0xA0)  #  16-bit registers through 0xAE
_MS8607_PT_CMD_RESET = const(0x1E)  # Command to reset pressure sensor
_MS8607_PT_CMD_PRESS_START = const(0x40)  # Command to start pressure ADC measurement
_MS8607_PT_CMD_TEMP_START = const(0x50)  # Command to start temperature ADC measurement
_MS8607_PT_CMD_READ_ADC = const(0x00)  # Temp and pressure ADC read command


class CV:
    """struct helper"""

    @classmethod
    def add_values(cls, value_tuples):
        """Add CV values to the class"""
        cls.string = {}
        cls.lsb = {}

        for value_tuple in value_tuples:
            name, value, string, lsb = value_tuple
            setattr(cls, name, value)
            cls.string[value] = string
            cls.lsb[value] = lsb

    @classmethod
    def is_valid(cls, value):
        """Validate that a given value is a member"""
        return value in cls.string


class HumidityResolution(CV):
    """Options for `pressure_resolution`"""

    pass  # pylint: disable=unnecessary-pass


HumidityResolution.add_values(
    (
        ("OSR_256", 0x01, 8, 0.003),
        ("OSR_1024", 0x80, 10, 0.005),
        ("OSR_2048", 0x81, 11, 0.009),
        ("OSR_4096", 0x00, 12, 0.016),
    )
)


class PressureResolution(CV):
    """Options for `pressure_resolution`"""

    pass  # pylint: disable=unnecessary-pass


PressureResolution.add_values(
    (
        ("OSR_256", 0, 256, 0.001),
        ("OSR_512", 1, 512, 0.002),
        ("OSR_1024", 2, 1024, 0.003),
        ("OSR_2048", 3, 2048, 0.005),
        ("OSR_4096", 4, 4096, 0.009),
        ("OSR_8192", 5, 8192, 0.019),
    )
)


class MS8607:
    """Library for the MS8607 Pressure Temperature and Humidity Sensor


        :param ~busio.I2C i2c_bus: The I2C bus the MS8607 is connected to.

    """

    def __init__(self, i2c_bus):

        self.humidity_i2c_device = i2c_device.I2CDevice(i2c_bus, _MS8607_HSENSOR_ADDR)
        self.pressure_i2c_device = i2c_device.I2CDevice(i2c_bus, _MS8607_PTSENSOR_ADDR)
        self._buffer = bytearray(4)
        self._calibration_constants = []
        self._pressure = None
        self._temperature = None
        self.reset()
        self.initialize()

    def reset(self):
        """Reset the sensor to an initial unconfigured state"""
        self._buffer[0] = _MS8607_HUM_CMD_RESET
        with self.humidity_i2c_device as i2c:
            i2c.write(self._buffer, end=1)

        sleep(0.015)
        self._buffer[0] = _MS8607_PT_CMD_RESET
        with self.pressure_i2c_device as i2c:
            i2c.write(self._buffer, end=1)

    def initialize(self):
        """Configure the sensors with the default settings and state.
        For use after calling `reset()`
        """
        self._set_calibration_consts()
        self.pressure_resolution = (
            PressureResolution.OSR_8192  # pylint:disable=no-member
        )
        self.humidity_resolution = (
            HumidityResolution.OSR_4096  # pylint:disable=no-member
        )

    def _set_calibration_consts(self):
        constants = []

        for i in range(7):
            offset = 2 * i
            self._buffer[0] = _MS8607_PT_CALIB_ROM_ADDR + offset
            with self.pressure_i2c_device as i2c:
                i2c.write_then_readinto(
                    self._buffer,
                    self._buffer,
                    out_start=0,
                    out_end=1,
                    in_start=0,
                    in_end=2,
                )

            constants.extend(unpack_from(">H", self._buffer[0:2]))

        crc_value = (constants[0] & 0xF000) >> 12
        constants.append(0)
        if not self._check_press_calibration_crc(constants, crc_value):
            raise RuntimeError("CRC Error reading humidity calibration constants")

        self._calibration_constants = constants

    @property
    def pressure_and_temperature(self):
        """Pressure and Temperature, measured at the same time"""
        raw_temperature, raw_pressure = self._read_temp_pressure()

        self._scale_temp_pressure(raw_temperature, raw_pressure)

        return (self._temperature, self._pressure)

    def _scale_temp_pressure(self, raw_temperature, raw_pressure):
        # See figure 7 'PRESSURE COMPENSATION (SECOND ORDER OVER TEMPERATURE)'
        # in the MS8607 datasheet
        delta_temp = self._dt(raw_temperature)

        initial_temp = 2000 + (delta_temp * self._calibration_constants[6] >> 23)

        temp2, offset2, sensitivity2 = self._corrections(initial_temp, delta_temp)

        self._temperature = (initial_temp - temp2) / 100
        offset = self._pressure_offset(delta_temp) - offset2

        sensitivity = self._pressure_scaling(delta_temp) - sensitivity2

        self._pressure = ((((raw_pressure * sensitivity) >> 21) - offset) >> 15) / 100

    @property
    def pressure_resolution(self):
        """The measurement resolution used for the pressure and temperature sensor"""

        return self._psensor_resolution_osr

    @pressure_resolution.setter
    def pressure_resolution(self, resolution):
        if not PressureResolution.is_valid(resolution):
            raise AttributeError(
                "pressure_resolution must be an `adafruit_ms8607.PressureResolution`"
            )

        self._psensor_resolution_osr = resolution

    @staticmethod
    def _corrections(initial_temp, delta_temp):
        # # Second order temperature compensation
        if initial_temp < 2000:
            delta_2k = initial_temp - 2000
            temp_factor = delta_2k ** 2 >> 4
            temp2 = (3 * delta_temp ** 2) >> 33
            offset2 = 61 * temp_factor
            sensitivity2 = 29 * temp_factor

            if initial_temp < -1500:
                delta_15k = initial_temp + 1500
                temp_factor = delta_15k ** 2

                offset2 += 17 * temp_factor
                sensitivity2 += 9 * temp_factor
            #
        else:
            temp2 = (5 * delta_temp ** 2) >> 38
            offset2 = 0
            sensitivity2 = 0
        return temp2, offset2, sensitivity2

    def _pressure_scaling(self, delta_temp):
        return (self._calibration_constants[1] << 16) + (
            (self._calibration_constants[3] * delta_temp) >> 7
        )

    def _pressure_offset(self, delta_temp):
        return ((self._calibration_constants[2]) << 17) + (
            (self._calibration_constants[4] * delta_temp) >> 6
        )

    def _read_temp_pressure(self):

        # First read temperature

        cmd = self._psensor_resolution_osr * 2
        cmd |= _MS8607_PT_CMD_TEMP_START
        self._buffer[0] = cmd
        with self.pressure_i2c_device as i2c:
            i2c.write(self._buffer, end=1)
        # re-purposing lsb for integration time
        integration_time = PressureResolution.lsb[self._psensor_resolution_osr]
        sleep(integration_time)
        self._buffer[0] = _MS8607_PT_CMD_READ_ADC
        with self.pressure_i2c_device as i2c:
            i2c.write_then_readinto(
                self._buffer, self._buffer, out_start=0, out_end=1, in_start=1, in_end=3
            )

        # temp is only 24 bits but unpack wants 4 bytes so add a forth byte
        self._buffer[0] = 0
        raw_temperature = unpack_from(">I", self._buffer)[0]

        # next read pressure
        cmd = self._psensor_resolution_osr * 2
        cmd |= _MS8607_PT_CMD_PRESS_START
        self._buffer[0] = cmd
        with self.pressure_i2c_device as i2c:
            i2c.write(self._buffer, end=1)

        sleep(integration_time)

        self._buffer[0] = _MS8607_PT_CMD_READ_ADC
        with self.pressure_i2c_device as i2c:
            i2c.write_then_readinto(
                self._buffer, self._buffer, out_start=0, out_end=1, in_start=1, in_end=3
            )
        # pressure is only 24 bits but unpack wants 4 bytes so add a forth byte
        self._buffer[0] = 0

        raw_pressure = unpack_from(">I", self._buffer)[0]
        return raw_temperature, raw_pressure

    def _dt(self, raw_temperature):

        ref_temp = self._calibration_constants[5]
        return raw_temperature - (ref_temp << 8)

    @property
    def temperature(self):
        """The current temperature in degrees Celcius"""
        return self.pressure_and_temperature[0]

    @property
    def pressure(self):
        """The current barometric pressure in hPa"""
        return self.pressure_and_temperature[1]

    @property
    def relative_humidity(self):
        """The current relative humidity in % rH"""

        self._buffer[0] = _MS8607_HUM_CMD_READ_NO_HOLD
        with self.humidity_i2c_device as i2c:
            i2c.write(self._buffer, end=1)
        sleep(0.016)

        with self.humidity_i2c_device as i2c:
            i2c.readinto(self._buffer, end=3)

        raw_humidity = unpack_from(">H", self._buffer)[0]
        crc_value = unpack_from(">B", self._buffer, offset=2)[0]
        humidity = (
            raw_humidity * (_MS8607_HUM_COEFF_MUL / (1 << 16))
        ) + _MS8607_HUM_COEFF_ADD
        if not self._check_humidity_crc(raw_humidity, crc_value):
            raise RuntimeError("CRC Error reading humidity data")
        return humidity

    @property
    def humidity_resolution(self):
        """The humidity sensor's measurement resolution"""
        return self._humidity_resolution

    @humidity_resolution.setter
    def humidity_resolution(self, resolution):
        if not HumidityResolution.is_valid(resolution):
            raise AttributeError("humidity_resolution must be a Humidity Resolution")

        self._humidity_resolution = resolution
        reg_value = self._read_hum_user_register()

        # Clear the resolution bits
        reg_value &= ~_MS8607_HUM_USR_REG_RESOLUTION_MASK
        # and then set them to the new value
        reg_value |= resolution & _MS8607_HUM_USR_REG_RESOLUTION_MASK

        self._set_hum_user_register(reg_value)

    def _read_hum_user_register(self):

        self._buffer[0] = _MS8607_HUM_CMD_READ_USR
        with self.humidity_i2c_device as i2c:
            i2c.write(self._buffer, end=1)

        with self.humidity_i2c_device as i2c:
            i2c.readinto(self._buffer, end=1)

        return self._buffer[0]

    def _set_hum_user_register(self, register_value):
        self._buffer[0] = _MS8607_HUM_CMD_WRITE_USR
        self._buffer[1] = register_value
        with self.humidity_i2c_device as i2c:
            # shouldn't this end at two?
            i2c.write(self._buffer, end=2)

    @staticmethod
    def _check_humidity_crc(value, crc):
        polynom = 0x988000  # x^8 + x^5 + x^4 + 1
        msb = 0x800000
        mask = 0xFF8000
        result = value << 8  # Pad with zeros as specified in spec

        while msb != 0x80:
            # Check if msb of current value is 1 and apply XOR mask
            if result & msb:
                result = ((result ^ polynom) & mask) | (result & ~mask)

            # Shift by one
            msb >>= 1
            mask >>= 1
            polynom >>= 1

        if result == crc:
            return True
        return False

    @staticmethod
    def _check_press_calibration_crc(calibration_int16s, crc):
        cnt = 0
        n_rem = 0
        n_rem = 0
        crc_read = calibration_int16s[0]
        calibration_int16s[7] = 0
        calibration_int16s[0] = 0x0FFF & (calibration_int16s[0])  # Clear the CRC byte

        for cnt in range(16):
            # Get next byte

            if cnt % 2 == 1:
                n_rem ^= calibration_int16s[cnt >> 1] & 0x00FF
            else:
                n_rem ^= calibration_int16s[cnt >> 1] >> 8

            for _i in range(8, 0, -1):
                if n_rem & 0x8000:
                    n_rem = (n_rem << 1) ^ 0x3000
                else:
                    n_rem <<= 1
                # we have to restrict to 16 bits
                n_rem &= 0xFFFF

        n_rem >>= 12
        calibration_int16s[0] = crc_read
        return n_rem == crc
