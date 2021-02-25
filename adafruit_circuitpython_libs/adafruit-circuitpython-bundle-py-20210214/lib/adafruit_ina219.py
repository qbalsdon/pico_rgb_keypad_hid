# SPDX-FileCopyrightText: 2017 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ina219`
====================================================

CircuitPython driver for the INA219 current sensor.

* Author(s): Dean Miller

Implementation Notes
--------------------

**Hardware:**

* `Adafruit INA219 High Side DC Current Sensor Breakout <https://www.adafruit.com/product/904>`_

* `Adafruit INA219 FeatherWing <https://www.adafruit.com/product/3650>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware (2.2.0+) for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice

from adafruit_register.i2c_struct import ROUnaryStruct, UnaryStruct
from adafruit_register.i2c_bits import ROBits, RWBits
from adafruit_register.i2c_bit import ROBit

__version__ = "3.4.8"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_INA219.git"

# Bits
# pylint: disable=too-few-public-methods

# Config Register (R/W)
_REG_CONFIG = const(0x00)


class BusVoltageRange:
    """Constants for ``bus_voltage_range``"""

    RANGE_16V = 0x00  # set bus voltage range to 16V
    RANGE_32V = 0x01  # set bus voltage range to 32V (default)


class Gain:
    """Constants for ``gain``"""

    DIV_1_40MV = 0x00  # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV = 0x01  # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV = 0x02  # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV = 0x03  # shunt prog. gain set to /8, 320 mV range


class ADCResolution:
    """Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``"""

    ADCRES_9BIT_1S = 0x00  #  9bit,   1 sample,     84us
    ADCRES_10BIT_1S = 0x01  # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S = 0x02  # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S = 0x03  # 12 bit,  1 sample,    532us
    ADCRES_12BIT_2S = 0x09  # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S = 0x0A  # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S = 0x0B  # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S = 0x0C  # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S = 0x0D  # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S = 0x0E  # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S = 0x0F  # 12bit, 128 samples, 68.10ms


class Mode:
    """Constants for ``mode``"""

    POWERDOWN = 0x00  # power down
    SVOLT_TRIGGERED = 0x01  # shunt voltage triggered
    BVOLT_TRIGGERED = 0x02  # bus voltage triggered
    SANDBVOLT_TRIGGERED = 0x03  # shunt and bus voltage triggered
    ADCOFF = 0x04  # ADC off
    SVOLT_CONTINUOUS = 0x05  # shunt voltage continuous
    BVOLT_CONTINUOUS = 0x06  # bus voltage continuous
    SANDBVOLT_CONTINUOUS = 0x07  # shunt and bus voltage continuous


# SHUNT VOLTAGE REGISTER (R)
_REG_SHUNTVOLTAGE = const(0x01)

# BUS VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE = const(0x02)

# POWER REGISTER (R)
_REG_POWER = const(0x03)

# CURRENT REGISTER (R)
_REG_CURRENT = const(0x04)

# CALIBRATION REGISTER (R/W)
_REG_CALIBRATION = const(0x05)
# pylint: enable=too-few-public-methods


def _to_signed(num):
    if num > 0x7FFF:
        num -= 0x10000
    return num


class INA219:
    """Driver for the INA219 current sensor"""

    # Basic API:

    # INA219( i2c_bus, addr)  Create instance of INA219 sensor
    #    :param i2c_bus          The I2C bus the INA219is connected to
    #    :param addr (0x40)      Address of the INA219 on the bus (default 0x40)

    # shunt_voltage               RO : shunt voltage scaled to Volts
    # bus_voltage                 RO : bus voltage (V- to GND) scaled to volts (==load voltage)
    # current                     RO : current through shunt, scaled to mA
    # power                       RO : power consumption of the load, scaled to Watt
    # set_calibration_32V_2A()    Initialize chip for 32V max and up to 2A (default)
    # set_calibration_32V_1A()    Initialize chip for 32V max and up to 1A
    # set_calibration_16V_400mA() Initialize chip for 16V max and up to 400mA

    # Advanced API:
    # config register break-up
    #   reset                     WO : Write Reset.RESET to reset the chip (must recalibrate)
    #   bus_voltage_range         RW : Bus Voltage Range field (use BusVoltageRange.XXX constants)
    #   gain                      RW : Programmable Gain field (use Gain.XXX constants)
    #   bus_adc_resolution        RW : Bus ADC resolution and averaging modes (ADCResolution.XXX)
    #   shunt_adc_resolution      RW : Shunt ADC resolution and averaging modes (ADCResolution.XXX)
    #   mode                      RW : operating modes in config register (use Mode.XXX constants)

    # raw_shunt_voltage           RO : Shunt Voltage register (not scaled)
    # raw_bus_voltage             RO : Bus Voltage field in Bus Voltage register (not scaled)
    # conversion_ready            RO : Conversion Ready bit in Bus Voltage register
    # overflow                    RO : Math Overflow bit in Bus Voltage register
    # raw_power                   RO : Power register (not scaled)
    # raw_current                 RO : Current register (not scaled)
    # calibration                 RW : calibration register (note: value is cached)

    def __init__(self, i2c_bus, addr=0x40):
        self.i2c_device = I2CDevice(i2c_bus, addr)
        self.i2c_addr = addr

        # Set chip to known config values to start
        self._cal_value = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_32V_2A()

    # config register break-up
    reset = RWBits(1, _REG_CONFIG, 15, 2, False)
    bus_voltage_range = RWBits(1, _REG_CONFIG, 13, 2, False)
    gain = RWBits(2, _REG_CONFIG, 11, 2, False)
    bus_adc_resolution = RWBits(4, _REG_CONFIG, 7, 2, False)
    shunt_adc_resolution = RWBits(4, _REG_CONFIG, 3, 2, False)
    mode = RWBits(3, _REG_CONFIG, 0, 2, False)

    # shunt voltage register
    raw_shunt_voltage = ROUnaryStruct(_REG_SHUNTVOLTAGE, ">h")

    # bus voltage register
    raw_bus_voltage = ROBits(13, _REG_BUSVOLTAGE, 3, 2, False)
    conversion_ready = ROBit(_REG_BUSVOLTAGE, 1, 2, False)
    overflow = ROBit(_REG_BUSVOLTAGE, 0, 2, False)

    # power and current registers
    raw_power = ROUnaryStruct(_REG_POWER, ">H")
    raw_current = ROUnaryStruct(_REG_CURRENT, ">h")

    # calibration register
    _raw_calibration = UnaryStruct(_REG_CALIBRATION, ">H")

    @property
    def calibration(self):
        """Calibration register (cached value)"""
        return self._cal_value  # return cached value

    @calibration.setter
    def calibration(self, cal_value):
        self._cal_value = (
            cal_value  # value is cached for ``current`` and ``power`` properties
        )
        self._raw_calibration = self._cal_value

    @property
    def shunt_voltage(self):
        """The shunt voltage (between V+ and V-) in Volts (so +-.327V)"""
        # The least signficant bit is 10uV which is 0.00001 volts
        return self.raw_shunt_voltage * 0.00001

    @property
    def bus_voltage(self):
        """The bus voltage (between V- and GND) in Volts"""
        # Shift to the right 3 to drop CNVR and OVF and multiply by LSB
        # Each least signficant bit is 4mV
        return self.raw_bus_voltage * 0.004

    @property
    def current(self):
        """The current through the shunt resistor in milliamps."""
        # Sometimes a sharp load will reset the INA219, which will
        # reset the cal register, meaning CURRENT and POWER will
        # not be available ... always setting a cal
        # value even if it's an unfortunate extra step
        self._raw_calibration = self._cal_value
        # Now we can safely read the CURRENT register!
        return self.raw_current * self._current_lsb

    @property
    def power(self):
        """The power through the load in Watt."""
        # Sometimes a sharp load will reset the INA219, which will
        # reset the cal register, meaning CURRENT and POWER will
        # not be available ... always setting a cal
        # value even if it's an unfortunate extra step
        self._raw_calibration = self._cal_value
        # Now we can safely read the CURRENT register!
        return self.raw_power * self._power_lsb

    def set_calibration_32V_2A(self):  # pylint: disable=invalid-name
        """Configures to INA219 to be able to measure up to 32V and 2A of current. Counter
        overflow occurs at 3.2A.

        ..note :: These calculations assume a 0.1 shunt ohm resistor is present
        """
        # By default we use a pretty huge range for the input voltage,
        # which probably isn't the most appropriate choice for system
        # that don't use a lot of power.  But all of the calculations
        # are shown below if you want to change the settings.  You will
        # also need to change any relevant register settings, such as
        # setting the VBUS_MAX to 16V instead of 32V, etc.

        # VBUS_MAX = 32V             (Assumes 32V, can also be set to 16V)
        # VSHUNT_MAX = 0.32          (Assumes Gain 8, 320mV, can also be 0.16, 0.08, 0.04)
        # RSHUNT = 0.1               (Resistor value in ohms)

        # 1. Determine max possible current
        # MaxPossible_I = VSHUNT_MAX / RSHUNT
        # MaxPossible_I = 3.2A

        # 2. Determine max expected current
        # MaxExpected_I = 2.0A

        # 3. Calculate possible range of LSBs (Min = 15-bit, Max = 12-bit)
        # MinimumLSB = MaxExpected_I/32767
        # MinimumLSB = 0.000061              (61uA per bit)
        # MaximumLSB = MaxExpected_I/4096
        # MaximumLSB = 0,000488              (488uA per bit)

        # 4. Choose an LSB between the min and max values
        #    (Preferrably a roundish number close to MinLSB)
        # CurrentLSB = 0.0001 (100uA per bit)
        self._current_lsb = 0.1  # Current LSB = 100uA per bit

        # 5. Compute the calibration register
        # Cal = trunc (0.04096 / (Current_LSB * RSHUNT))
        # Cal = 4096 (0x1000)

        self._cal_value = 4096

        # 6. Calculate the power LSB
        # PowerLSB = 20 * CurrentLSB
        # PowerLSB = 0.002 (2mW per bit)
        self._power_lsb = 0.002  # Power LSB = 2mW per bit

        # 7. Compute the maximum current and shunt voltage values before overflow
        #
        # Max_Current = Current_LSB * 32767
        # Max_Current = 3.2767A before overflow
        #
        # If Max_Current > Max_Possible_I then
        #    Max_Current_Before_Overflow = MaxPossible_I
        # Else
        #    Max_Current_Before_Overflow = Max_Current
        # End If
        #
        # Max_ShuntVoltage = Max_Current_Before_Overflow * RSHUNT
        # Max_ShuntVoltage = 0.32V
        #
        # If Max_ShuntVoltage >= VSHUNT_MAX
        #    Max_ShuntVoltage_Before_Overflow = VSHUNT_MAX
        # Else
        #    Max_ShuntVoltage_Before_Overflow = Max_ShuntVoltage
        # End If

        # 8. Compute the Maximum Power
        # MaximumPower = Max_Current_Before_Overflow * VBUS_MAX
        # MaximumPower = 3.2 * 32V
        # MaximumPower = 102.4W

        # Set Calibration register to 'Cal' calculated above
        self._raw_calibration = self._cal_value

        # Set Config register to take into account the settings above
        self.bus_voltage_range = BusVoltageRange.RANGE_32V
        self.gain = Gain.DIV_8_320MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.mode = Mode.SANDBVOLT_CONTINUOUS

    def set_calibration_32V_1A(self):  # pylint: disable=invalid-name
        """Configures to INA219 to be able to measure up to 32V and 1A of current. Counter overflow
        occurs at 1.3A.

        .. note:: These calculations assume a 0.1 ohm shunt resistor is present"""
        # By default we use a pretty huge range for the input voltage,
        # which probably isn't the most appropriate choice for system
        # that don't use a lot of power.  But all of the calculations
        # are shown below if you want to change the settings.  You will
        # also need to change any relevant register settings, such as
        # setting the VBUS_MAX to 16V instead of 32V, etc.

        # VBUS_MAX = 32V        (Assumes 32V, can also be set to 16V)
        # VSHUNT_MAX = 0.32    (Assumes Gain 8, 320mV, can also be 0.16, 0.08, 0.04)
        # RSHUNT = 0.1            (Resistor value in ohms)

        # 1. Determine max possible current
        # MaxPossible_I = VSHUNT_MAX / RSHUNT
        # MaxPossible_I = 3.2A

        # 2. Determine max expected current
        # MaxExpected_I = 1.0A

        # 3. Calculate possible range of LSBs (Min = 15-bit, Max = 12-bit)
        # MinimumLSB = MaxExpected_I/32767
        # MinimumLSB = 0.0000305             (30.5uA per bit)
        # MaximumLSB = MaxExpected_I/4096
        # MaximumLSB = 0.000244              (244uA per bit)

        # 4. Choose an LSB between the min and max values
        #    (Preferrably a roundish number close to MinLSB)
        # CurrentLSB = 0.0000400 (40uA per bit)
        self._current_lsb = 0.04  # In milliamps

        # 5. Compute the calibration register
        # Cal = trunc (0.04096 / (Current_LSB * RSHUNT))
        # Cal = 10240 (0x2800)

        self._cal_value = 10240

        # 6. Calculate the power LSB
        # PowerLSB = 20 * CurrentLSB
        # PowerLSB = 0.0008 (800uW per bit)
        self._power_lsb = 0.0008

        # 7. Compute the maximum current and shunt voltage values before overflow
        #
        # Max_Current = Current_LSB * 32767
        # Max_Current = 1.31068A before overflow
        #
        # If Max_Current > Max_Possible_I then
        #    Max_Current_Before_Overflow = MaxPossible_I
        # Else
        #    Max_Current_Before_Overflow = Max_Current
        # End If
        #
        # ... In this case, we're good though since Max_Current is less than MaxPossible_I
        #
        # Max_ShuntVoltage = Max_Current_Before_Overflow * RSHUNT
        # Max_ShuntVoltage = 0.131068V
        #
        # If Max_ShuntVoltage >= VSHUNT_MAX
        #    Max_ShuntVoltage_Before_Overflow = VSHUNT_MAX
        # Else
        #    Max_ShuntVoltage_Before_Overflow = Max_ShuntVoltage
        # End If

        # 8. Compute the Maximum Power
        # MaximumPower = Max_Current_Before_Overflow * VBUS_MAX
        # MaximumPower = 1.31068 * 32V
        # MaximumPower = 41.94176W

        # Set Calibration register to 'Cal' calculated above
        self._raw_calibration = self._cal_value

        # Set Config register to take into account the settings above
        self.bus_voltage_range = BusVoltageRange.RANGE_32V
        self.gain = Gain.DIV_8_320MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.mode = Mode.SANDBVOLT_CONTINUOUS

    def set_calibration_16V_400mA(self):  # pylint: disable=invalid-name
        """Configures to INA219 to be able to measure up to 16V and 400mA of current. Counter
        overflow occurs at 1.6A.

        .. note:: These calculations assume a 0.1 ohm shunt resistor is present"""
        # Calibration which uses the highest precision for
        # current measurement (0.1mA), at the expense of
        # only supporting 16V at 400mA max.

        # VBUS_MAX = 16V
        # VSHUNT_MAX = 0.04          (Assumes Gain 1, 40mV)
        # RSHUNT = 0.1               (Resistor value in ohms)

        # 1. Determine max possible current
        # MaxPossible_I = VSHUNT_MAX / RSHUNT
        # MaxPossible_I = 0.4A

        # 2. Determine max expected current
        # MaxExpected_I = 0.4A

        # 3. Calculate possible range of LSBs (Min = 15-bit, Max = 12-bit)
        # MinimumLSB = MaxExpected_I/32767
        # MinimumLSB = 0.0000122              (12uA per bit)
        # MaximumLSB = MaxExpected_I/4096
        # MaximumLSB = 0.0000977              (98uA per bit)

        # 4. Choose an LSB between the min and max values
        #    (Preferrably a roundish number close to MinLSB)
        # CurrentLSB = 0.00005 (50uA per bit)
        self._current_lsb = 0.05  # in milliamps

        # 5. Compute the calibration register
        # Cal = trunc (0.04096 / (Current_LSB * RSHUNT))
        # Cal = 8192 (0x2000)

        self._cal_value = 8192

        # 6. Calculate the power LSB
        # PowerLSB = 20 * CurrentLSB
        # PowerLSB = 0.001 (1mW per bit)
        self._power_lsb = 0.001

        # 7. Compute the maximum current and shunt voltage values before overflow
        #
        # Max_Current = Current_LSB * 32767
        # Max_Current = 1.63835A before overflow
        #
        # If Max_Current > Max_Possible_I then
        #    Max_Current_Before_Overflow = MaxPossible_I
        # Else
        #    Max_Current_Before_Overflow = Max_Current
        # End If
        #
        # Max_Current_Before_Overflow = MaxPossible_I
        # Max_Current_Before_Overflow = 0.4
        #
        # Max_ShuntVoltage = Max_Current_Before_Overflow * RSHUNT
        # Max_ShuntVoltage = 0.04V
        #
        # If Max_ShuntVoltage >= VSHUNT_MAX
        #    Max_ShuntVoltage_Before_Overflow = VSHUNT_MAX
        # Else
        #    Max_ShuntVoltage_Before_Overflow = Max_ShuntVoltage
        # End If
        #
        # Max_ShuntVoltage_Before_Overflow = VSHUNT_MAX
        # Max_ShuntVoltage_Before_Overflow = 0.04V

        # 8. Compute the Maximum Power
        # MaximumPower = Max_Current_Before_Overflow * VBUS_MAX
        # MaximumPower = 0.4 * 16V
        # MaximumPower = 6.4W

        # Set Calibration register to 'Cal' calculated above
        self._raw_calibration = self._cal_value

        # Set Config register to take into account the settings above
        self.bus_voltage_range = BusVoltageRange.RANGE_16V
        self.gain = Gain.DIV_1_40MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.mode = Mode.SANDBVOLT_CONTINUOUS

    def set_calibration_16V_5A(self):  # pylint: disable=invalid-name
        """Configures to INA219 to be able to measure up to 16V and 5000mA of current. Counter
        overflow occurs at 8.0A.

        .. note:: These calculations assume a 0.02 ohm shunt resistor is present"""
        # Calibration which uses the highest precision for
        # current measurement (0.1mA), at the expense of
        # only supporting 16V at 5000mA max.

        # VBUS_MAX = 16V
        # VSHUNT_MAX = 0.16          (Assumes Gain 3, 160mV)
        # RSHUNT = 0.02              (Resistor value in ohms)

        # 1. Determine max possible current
        # MaxPossible_I = VSHUNT_MAX / RSHUNT
        # MaxPossible_I = 8.0A

        # 2. Determine max expected current
        # MaxExpected_I = 5.0A

        # 3. Calculate possible range of LSBs (Min = 15-bit, Max = 12-bit)
        # MinimumLSB = MaxExpected_I/32767
        # MinimumLSB = 0.0001529              (uA per bit)
        # MaximumLSB = MaxExpected_I/4096
        # MaximumLSB = 0.0012207              (uA per bit)

        # 4. Choose an LSB between the min and max values
        #    (Preferrably a roundish number close to MinLSB)
        # CurrentLSB = 0.00016 (uA per bit)
        self._current_lsb = 0.1524  # in milliamps

        # 5. Compute the calibration register
        # Cal = trunc (0.04096 / (Current_LSB * RSHUNT))
        # Cal = 13434 (0x347a)

        self._cal_value = 13434

        # 6. Calculate the power LSB
        # PowerLSB = 20 * CurrentLSB
        # PowerLSB = 0.003 (3.048mW per bit)
        self._power_lsb = 0.003048

        # 7. Compute the maximum current and shunt voltage values before overflow
        #
        # 8. Compute the Maximum Power
        #

        # Set Calibration register to 'Cal' calcutated above
        self._raw_calibration = self._cal_value

        # Set Config register to take into account the settings above
        self.bus_voltage_range = BusVoltageRange.RANGE_16V
        self.gain = Gain.DIV_4_160MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.mode = Mode.SANDBVOLT_CONTINUOUS
