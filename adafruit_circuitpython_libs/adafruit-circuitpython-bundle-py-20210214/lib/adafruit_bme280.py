# SPDX-FileCopyrightText: 2017 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_bme280` - Adafruit BME280 - Temperature, Humidity & Barometic Pressure Sensor
=========================================================================================

CircuitPython driver from BME280 Temperature, Humidity and Barometic Pressure sensor

* Author(s): ladyada
"""
import math
from time import sleep
from micropython import const

try:
    import struct
except ImportError:
    import ustruct as struct


__version__ = "2.5.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BME280.git"

#    I2C ADDRESS/BITS/SETTINGS
#    -----------------------------------------------------------------------
_BME280_ADDRESS = const(0x77)
_BME280_CHIPID = const(0x60)

_BME280_REGISTER_CHIPID = const(0xD0)
_BME280_REGISTER_DIG_T1 = const(0x88)
_BME280_REGISTER_DIG_H1 = const(0xA1)
_BME280_REGISTER_DIG_H2 = const(0xE1)
_BME280_REGISTER_DIG_H3 = const(0xE3)
_BME280_REGISTER_DIG_H4 = const(0xE4)
_BME280_REGISTER_DIG_H5 = const(0xE5)
_BME280_REGISTER_DIG_H6 = const(0xE7)

_BME280_REGISTER_SOFTRESET = const(0xE0)
_BME280_REGISTER_CTRL_HUM = const(0xF2)
_BME280_REGISTER_STATUS = const(0xF3)
_BME280_REGISTER_CTRL_MEAS = const(0xF4)
_BME280_REGISTER_CONFIG = const(0xF5)
_BME280_REGISTER_PRESSUREDATA = const(0xF7)
_BME280_REGISTER_TEMPDATA = const(0xFA)
_BME280_REGISTER_HUMIDDATA = const(0xFD)

_BME280_PRESSURE_MIN_HPA = const(300)
_BME280_PRESSURE_MAX_HPA = const(1100)
_BME280_HUMIDITY_MIN = const(0)
_BME280_HUMIDITY_MAX = const(100)

"""iir_filter values"""
IIR_FILTER_DISABLE = const(0)
IIR_FILTER_X2 = const(0x01)
IIR_FILTER_X4 = const(0x02)
IIR_FILTER_X8 = const(0x03)
IIR_FILTER_X16 = const(0x04)

_BME280_IIR_FILTERS = (
    IIR_FILTER_DISABLE,
    IIR_FILTER_X2,
    IIR_FILTER_X4,
    IIR_FILTER_X8,
    IIR_FILTER_X16,
)

"""overscan values for temperature, pressure, and humidity"""
OVERSCAN_DISABLE = const(0x00)
OVERSCAN_X1 = const(0x01)
OVERSCAN_X2 = const(0x02)
OVERSCAN_X4 = const(0x03)
OVERSCAN_X8 = const(0x04)
OVERSCAN_X16 = const(0x05)

_BME280_OVERSCANS = {
    OVERSCAN_DISABLE: 0,
    OVERSCAN_X1: 1,
    OVERSCAN_X2: 2,
    OVERSCAN_X4: 4,
    OVERSCAN_X8: 8,
    OVERSCAN_X16: 16,
}

"""mode values"""
MODE_SLEEP = const(0x00)
MODE_FORCE = const(0x01)
MODE_NORMAL = const(0x03)

_BME280_MODES = (MODE_SLEEP, MODE_FORCE, MODE_NORMAL)
"""
standby timeconstant values
TC_X[_Y] where X=milliseconds and Y=tenths of a millisecond
"""
STANDBY_TC_0_5 = const(0x00)  # 0.5ms
STANDBY_TC_10 = const(0x06)  # 10ms
STANDBY_TC_20 = const(0x07)  # 20ms
STANDBY_TC_62_5 = const(0x01)  # 62.5ms
STANDBY_TC_125 = const(0x02)  # 125ms
STANDBY_TC_250 = const(0x03)  # 250ms
STANDBY_TC_500 = const(0x04)  # 500ms
STANDBY_TC_1000 = const(0x05)  # 1000ms

_BME280_STANDBY_TCS = (
    STANDBY_TC_0_5,
    STANDBY_TC_10,
    STANDBY_TC_20,
    STANDBY_TC_62_5,
    STANDBY_TC_125,
    STANDBY_TC_250,
    STANDBY_TC_500,
    STANDBY_TC_1000,
)


class Adafruit_BME280:
    """Driver from BME280 Temperature, Humidity and Barometic Pressure sensor"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        """Check the BME280 was found, read the coefficients and enable the sensor"""
        # Check device ID.
        chip_id = self._read_byte(_BME280_REGISTER_CHIPID)
        if _BME280_CHIPID != chip_id:
            raise RuntimeError("Failed to find BME280! Chip ID 0x%x" % chip_id)
        # Set some reasonable defaults.
        self._iir_filter = IIR_FILTER_DISABLE
        self._overscan_humidity = OVERSCAN_X1
        self._overscan_temperature = OVERSCAN_X1
        self._overscan_pressure = OVERSCAN_X16
        self._t_standby = STANDBY_TC_125
        self._mode = MODE_SLEEP
        self._reset()
        self._read_coefficients()
        self._write_ctrl_meas()
        self._write_config()
        self.sea_level_pressure = 1013.25
        """Pressure in hectoPascals at sea level. Used to calibrate `altitude`."""
        self._t_fine = None

    def _read_temperature(self):
        # perform one measurement
        if self.mode != MODE_NORMAL:
            self.mode = MODE_FORCE
            # Wait for conversion to complete
            while self._get_status() & 0x08:
                sleep(0.002)
        raw_temperature = (
            self._read24(_BME280_REGISTER_TEMPDATA) / 16
        )  # lowest 4 bits get dropped
        # print("raw temp: ", UT)
        var1 = (
            raw_temperature / 16384.0 - self._temp_calib[0] / 1024.0
        ) * self._temp_calib[1]
        # print(var1)
        var2 = (
            (raw_temperature / 131072.0 - self._temp_calib[0] / 8192.0)
            * (raw_temperature / 131072.0 - self._temp_calib[0] / 8192.0)
        ) * self._temp_calib[2]
        # print(var2)

        self._t_fine = int(var1 + var2)
        # print("t_fine: ", self.t_fine)

    def _reset(self):
        """Soft reset the sensor"""
        self._write_register_byte(_BME280_REGISTER_SOFTRESET, 0xB6)
        sleep(0.004)  # Datasheet says 2ms.  Using 4ms just to be safe

    def _write_ctrl_meas(self):
        """
        Write the values to the ctrl_meas and ctrl_hum registers in the device
        ctrl_meas sets the pressure and temperature data acquistion options
        ctrl_hum sets the humidty oversampling and must be written to first
        """
        self._write_register_byte(_BME280_REGISTER_CTRL_HUM, self.overscan_humidity)
        self._write_register_byte(_BME280_REGISTER_CTRL_MEAS, self._ctrl_meas)

    def _get_status(self):
        """Get the value from the status register in the device """
        return self._read_byte(_BME280_REGISTER_STATUS)

    def _read_config(self):
        """Read the value from the config register in the device """
        return self._read_byte(_BME280_REGISTER_CONFIG)

    def _write_config(self):
        """Write the value to the config register in the device """
        normal_flag = False
        if self._mode == MODE_NORMAL:
            # Writes to the config register may be ignored while in Normal mode
            normal_flag = True
            self.mode = MODE_SLEEP  # So we switch to Sleep mode first
        self._write_register_byte(_BME280_REGISTER_CONFIG, self._config)
        if normal_flag:
            self.mode = MODE_NORMAL

    @property
    def mode(self):
        """
        Operation mode
        Allowed values are the constants MODE_*
        """
        return self._mode

    @mode.setter
    def mode(self, value):
        if not value in _BME280_MODES:
            raise ValueError("Mode '%s' not supported" % (value))
        self._mode = value
        self._write_ctrl_meas()

    @property
    def standby_period(self):
        """
        Control the inactive period when in Normal mode
        Allowed standby periods are the constants STANDBY_TC_*
        """
        return self._t_standby

    @standby_period.setter
    def standby_period(self, value):
        if not value in _BME280_STANDBY_TCS:
            raise ValueError("Standby Period '%s' not supported" % (value))
        if self._t_standby == value:
            return
        self._t_standby = value
        self._write_config()

    @property
    def overscan_humidity(self):
        """
        Humidity Oversampling
        Allowed values are the constants OVERSCAN_*
        """
        return self._overscan_humidity

    @overscan_humidity.setter
    def overscan_humidity(self, value):
        if not value in _BME280_OVERSCANS:
            raise ValueError("Overscan value '%s' not supported" % (value))
        self._overscan_humidity = value
        self._write_ctrl_meas()

    @property
    def overscan_temperature(self):
        """
        Temperature Oversampling
        Allowed values are the constants OVERSCAN_*
        """
        return self._overscan_temperature

    @overscan_temperature.setter
    def overscan_temperature(self, value):
        if not value in _BME280_OVERSCANS:
            raise ValueError("Overscan value '%s' not supported" % (value))
        self._overscan_temperature = value
        self._write_ctrl_meas()

    @property
    def overscan_pressure(self):
        """
        Pressure Oversampling
        Allowed values are the constants OVERSCAN_*
        """
        return self._overscan_pressure

    @overscan_pressure.setter
    def overscan_pressure(self, value):
        if not value in _BME280_OVERSCANS:
            raise ValueError("Overscan value '%s' not supported" % (value))
        self._overscan_pressure = value
        self._write_ctrl_meas()

    @property
    def iir_filter(self):
        """
        Controls the time constant of the IIR filter
        Allowed values are the constants IIR_FILTER_*
        """
        return self._iir_filter

    @iir_filter.setter
    def iir_filter(self, value):
        if not value in _BME280_IIR_FILTERS:
            raise ValueError("IIR Filter '%s' not supported" % (value))
        self._iir_filter = value
        self._write_config()

    @property
    def _config(self):
        """Value to be written to the device's config register """
        config = 0
        if self.mode == MODE_NORMAL:
            config += self._t_standby << 5
        if self._iir_filter:
            config += self._iir_filter << 2
        return config

    @property
    def _ctrl_meas(self):
        """Value to be written to the device's ctrl_meas register """
        ctrl_meas = self.overscan_temperature << 5
        ctrl_meas += self.overscan_pressure << 2
        ctrl_meas += self.mode
        return ctrl_meas

    @property
    def measurement_time_typical(self):
        """Typical time in milliseconds required to complete a measurement in normal mode"""
        meas_time_ms = 1.0
        if self.overscan_temperature != OVERSCAN_DISABLE:
            meas_time_ms += 2 * _BME280_OVERSCANS.get(self.overscan_temperature)
        if self.overscan_pressure != OVERSCAN_DISABLE:
            meas_time_ms += 2 * _BME280_OVERSCANS.get(self.overscan_pressure) + 0.5
        if self.overscan_humidity != OVERSCAN_DISABLE:
            meas_time_ms += 2 * _BME280_OVERSCANS.get(self.overscan_humidity) + 0.5
        return meas_time_ms

    @property
    def measurement_time_max(self):
        """Maximum time in milliseconds required to complete a measurement in normal mode"""
        meas_time_ms = 1.25
        if self.overscan_temperature != OVERSCAN_DISABLE:
            meas_time_ms += 2.3 * _BME280_OVERSCANS.get(self.overscan_temperature)
        if self.overscan_pressure != OVERSCAN_DISABLE:
            meas_time_ms += 2.3 * _BME280_OVERSCANS.get(self.overscan_pressure) + 0.575
        if self.overscan_humidity != OVERSCAN_DISABLE:
            meas_time_ms += 2.3 * _BME280_OVERSCANS.get(self.overscan_humidity) + 0.575
        return meas_time_ms

    @property
    def temperature(self):
        """The compensated temperature in degrees celsius."""
        self._read_temperature()
        return self._t_fine / 5120.0

    @property
    def pressure(self):
        """
        The compensated pressure in hectoPascals.
        returns None if pressure measurement is disabled
        """
        self._read_temperature()

        # Algorithm from the BME280 driver
        # https://github.com/BoschSensortec/BME280_driver/blob/master/bme280.c
        adc = (
            self._read24(_BME280_REGISTER_PRESSUREDATA) / 16
        )  # lowest 4 bits get dropped
        var1 = float(self._t_fine) / 2.0 - 64000.0
        var2 = var1 * var1 * self._pressure_calib[5] / 32768.0
        var2 = var2 + var1 * self._pressure_calib[4] * 2.0
        var2 = var2 / 4.0 + self._pressure_calib[3] * 65536.0
        var3 = self._pressure_calib[2] * var1 * var1 / 524288.0
        var1 = (var3 + self._pressure_calib[1] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self._pressure_calib[0]
        if not var1:  # avoid exception caused by division by zero
            raise ArithmeticError(
                "Invalid result possibly related to error while \
reading the calibration registers"
            )
        pressure = 1048576.0 - adc
        pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
        var1 = self._pressure_calib[8] * pressure * pressure / 2147483648.0
        var2 = pressure * self._pressure_calib[7] / 32768.0
        pressure = pressure + (var1 + var2 + self._pressure_calib[6]) / 16.0

        pressure /= 100
        if pressure < _BME280_PRESSURE_MIN_HPA:
            return _BME280_PRESSURE_MIN_HPA
        if pressure > _BME280_PRESSURE_MAX_HPA:
            return _BME280_PRESSURE_MAX_HPA
        return pressure

    @property
    def relative_humidity(self):
        """
        The relative humidity in RH %
        returns None if humidity measurement is disabled
        """
        return self.humidity

    @property
    def humidity(self):
        """
        The relative humidity in RH %
        returns None if humidity measurement is disabled
        """
        self._read_temperature()
        hum = self._read_register(_BME280_REGISTER_HUMIDDATA, 2)
        # print("Humidity data: ", hum)
        adc = float(hum[0] << 8 | hum[1])
        # print("adc:", adc)

        # Algorithm from the BME280 driver
        # https://github.com/BoschSensortec/BME280_driver/blob/master/bme280.c
        var1 = float(self._t_fine) - 76800.0
        # print("var1 ", var1)
        var2 = (
            self._humidity_calib[3] * 64.0 + (self._humidity_calib[4] / 16384.0) * var1
        )
        # print("var2 ",var2)
        var3 = adc - var2
        # print("var3 ",var3)
        var4 = self._humidity_calib[1] / 65536.0
        # print("var4 ",var4)
        var5 = 1.0 + (self._humidity_calib[2] / 67108864.0) * var1
        # print("var5 ",var5)
        var6 = 1.0 + (self._humidity_calib[5] / 67108864.0) * var1 * var5
        # print("var6 ",var6)
        var6 = var3 * var4 * (var5 * var6)
        humidity = var6 * (1.0 - self._humidity_calib[0] * var6 / 524288.0)

        if humidity > _BME280_HUMIDITY_MAX:
            return _BME280_HUMIDITY_MAX
        if humidity < _BME280_HUMIDITY_MIN:
            return _BME280_HUMIDITY_MIN
        # else...
        return humidity

    @property
    def altitude(self):
        """The altitude based on current ``pressure`` versus the sea level pressure
        (``sea_level_pressure``) - which you must enter ahead of time)"""
        pressure = self.pressure  # in Si units for hPascal
        return 44330 * (1.0 - math.pow(pressure / self.sea_level_pressure, 0.1903))

    def _read_coefficients(self):
        """Read & save the calibration coefficients"""
        coeff = self._read_register(_BME280_REGISTER_DIG_T1, 24)
        coeff = list(struct.unpack("<HhhHhhhhhhhh", bytes(coeff)))
        coeff = [float(i) for i in coeff]
        self._temp_calib = coeff[:3]
        self._pressure_calib = coeff[3:]

        self._humidity_calib = [0] * 6
        self._humidity_calib[0] = self._read_byte(_BME280_REGISTER_DIG_H1)
        coeff = self._read_register(_BME280_REGISTER_DIG_H2, 7)
        coeff = list(struct.unpack("<hBbBbb", bytes(coeff)))
        self._humidity_calib[1] = float(coeff[0])
        self._humidity_calib[2] = float(coeff[1])
        self._humidity_calib[3] = float((coeff[2] << 4) | (coeff[3] & 0xF))
        self._humidity_calib[4] = float((coeff[4] << 4) | (coeff[3] >> 4))
        self._humidity_calib[5] = float(coeff[5])

    def _read_byte(self, register):
        """Read a byte register value and return it"""
        return self._read_register(register, 1)[0]

    def _read24(self, register):
        """Read an unsigned 24-bit value as a floating point and return it."""
        ret = 0.0
        for b in self._read_register(register, 3):
            ret *= 256.0
            ret += float(b & 0xFF)
        return ret

    def _read_register(self, register, length):
        raise NotImplementedError()

    def _write_register_byte(self, register, value):
        raise NotImplementedError()


class Adafruit_BME280_I2C(Adafruit_BME280):
    """Driver for BME280 connected over I2C"""

    def __init__(self, i2c, address=_BME280_ADDRESS):
        import adafruit_bus_device.i2c_device as i2c_device  # pylint: disable=import-outside-toplevel

        self._i2c = i2c_device.I2CDevice(i2c, address)
        super().__init__()

    def _read_register(self, register, length):
        with self._i2c as i2c:
            i2c.write(bytes([register & 0xFF]))
            result = bytearray(length)
            i2c.readinto(result)
            # print("$%02X => %s" % (register, [hex(i) for i in result]))
            return result

    def _write_register_byte(self, register, value):
        with self._i2c as i2c:
            i2c.write(bytes([register & 0xFF, value & 0xFF]))
            # print("$%02X <= 0x%02X" % (register, value))


class Adafruit_BME280_SPI(Adafruit_BME280):
    """Driver for BME280 connected over SPI"""

    def __init__(self, spi, cs, baudrate=100000):
        import adafruit_bus_device.spi_device as spi_device  # pylint: disable=import-outside-toplevel

        self._spi = spi_device.SPIDevice(spi, cs, baudrate=baudrate)
        super().__init__()

    def _read_register(self, register, length):
        register = (register | 0x80) & 0xFF  # Read single, bit 7 high.
        with self._spi as spi:
            spi.write(bytearray([register]))  # pylint: disable=no-member
            result = bytearray(length)
            spi.readinto(result)  # pylint: disable=no-member
            # print("$%02X => %s" % (register, [hex(i) for i in result]))
            return result

    def _write_register_byte(self, register, value):
        register &= 0x7F  # Write, bit 7 low.
        with self._spi as spi:
            spi.write(bytes([register, value & 0xFF]))  # pylint: disable=no-member
