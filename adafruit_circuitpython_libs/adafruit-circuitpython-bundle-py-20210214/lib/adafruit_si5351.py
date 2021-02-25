# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_si5351`
====================================================

CircuitPython module to control the SI5351 clock generator.  See
examples/simpletest.py for a demo of the usage.  This is based on the Arduino
library at: https://github.com/adafruit/Adafruit_Si5351_Library/

* Author(s): Tony DiCola
"""
import math

from micropython import const

import adafruit_bus_device.i2c_device as i2c_device


__version__ = "1.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SI5351.git"


# Internal constants:
_SI5351_ADDRESS = const(0x60)  # Assumes ADDR pin = low
_SI5351_READBIT = const(0x01)
_SI5351_CRYSTAL_FREQUENCY = 25000000.0  # Fixed 25mhz crystal on board.
_SI5351_REGISTER_0_DEVICE_STATUS = const(0)
_SI5351_REGISTER_1_INTERRUPT_STATUS_STICKY = const(1)
_SI5351_REGISTER_2_INTERRUPT_STATUS_MASK = const(2)
_SI5351_REGISTER_3_OUTPUT_ENABLE_CONTROL = const(3)
_SI5351_REGISTER_9_OEB_PIN_ENABLE_CONTROL = const(9)
_SI5351_REGISTER_15_PLL_INPUT_SOURCE = const(15)
_SI5351_REGISTER_16_CLK0_CONTROL = const(16)
_SI5351_REGISTER_17_CLK1_CONTROL = const(17)
_SI5351_REGISTER_18_CLK2_CONTROL = const(18)
_SI5351_REGISTER_19_CLK3_CONTROL = const(19)
_SI5351_REGISTER_20_CLK4_CONTROL = const(20)
_SI5351_REGISTER_21_CLK5_CONTROL = const(21)
_SI5351_REGISTER_22_CLK6_CONTROL = const(22)
_SI5351_REGISTER_23_CLK7_CONTROL = const(23)
_SI5351_REGISTER_24_CLK3_0_DISABLE_STATE = const(24)
_SI5351_REGISTER_25_CLK7_4_DISABLE_STATE = const(25)
_SI5351_REGISTER_42_MULTISYNTH0_PARAMETERS_1 = const(42)
_SI5351_REGISTER_43_MULTISYNTH0_PARAMETERS_2 = const(43)
_SI5351_REGISTER_44_MULTISYNTH0_PARAMETERS_3 = const(44)
_SI5351_REGISTER_45_MULTISYNTH0_PARAMETERS_4 = const(45)
_SI5351_REGISTER_46_MULTISYNTH0_PARAMETERS_5 = const(46)
_SI5351_REGISTER_47_MULTISYNTH0_PARAMETERS_6 = const(47)
_SI5351_REGISTER_48_MULTISYNTH0_PARAMETERS_7 = const(48)
_SI5351_REGISTER_49_MULTISYNTH0_PARAMETERS_8 = const(49)
_SI5351_REGISTER_50_MULTISYNTH1_PARAMETERS_1 = const(50)
_SI5351_REGISTER_51_MULTISYNTH1_PARAMETERS_2 = const(51)
_SI5351_REGISTER_52_MULTISYNTH1_PARAMETERS_3 = const(52)
_SI5351_REGISTER_53_MULTISYNTH1_PARAMETERS_4 = const(53)
_SI5351_REGISTER_54_MULTISYNTH1_PARAMETERS_5 = const(54)
_SI5351_REGISTER_55_MULTISYNTH1_PARAMETERS_6 = const(55)
_SI5351_REGISTER_56_MULTISYNTH1_PARAMETERS_7 = const(56)
_SI5351_REGISTER_57_MULTISYNTH1_PARAMETERS_8 = const(57)
_SI5351_REGISTER_58_MULTISYNTH2_PARAMETERS_1 = const(58)
_SI5351_REGISTER_59_MULTISYNTH2_PARAMETERS_2 = const(59)
_SI5351_REGISTER_60_MULTISYNTH2_PARAMETERS_3 = const(60)
_SI5351_REGISTER_61_MULTISYNTH2_PARAMETERS_4 = const(61)
_SI5351_REGISTER_62_MULTISYNTH2_PARAMETERS_5 = const(62)
_SI5351_REGISTER_63_MULTISYNTH2_PARAMETERS_6 = const(63)
_SI5351_REGISTER_64_MULTISYNTH2_PARAMETERS_7 = const(64)
_SI5351_REGISTER_65_MULTISYNTH2_PARAMETERS_8 = const(65)
_SI5351_REGISTER_66_MULTISYNTH3_PARAMETERS_1 = const(66)
_SI5351_REGISTER_67_MULTISYNTH3_PARAMETERS_2 = const(67)
_SI5351_REGISTER_68_MULTISYNTH3_PARAMETERS_3 = const(68)
_SI5351_REGISTER_69_MULTISYNTH3_PARAMETERS_4 = const(69)
_SI5351_REGISTER_70_MULTISYNTH3_PARAMETERS_5 = const(70)
_SI5351_REGISTER_71_MULTISYNTH3_PARAMETERS_6 = const(71)
_SI5351_REGISTER_72_MULTISYNTH3_PARAMETERS_7 = const(72)
_SI5351_REGISTER_73_MULTISYNTH3_PARAMETERS_8 = const(73)
_SI5351_REGISTER_74_MULTISYNTH4_PARAMETERS_1 = const(74)
_SI5351_REGISTER_75_MULTISYNTH4_PARAMETERS_2 = const(75)
_SI5351_REGISTER_76_MULTISYNTH4_PARAMETERS_3 = const(76)
_SI5351_REGISTER_77_MULTISYNTH4_PARAMETERS_4 = const(77)
_SI5351_REGISTER_78_MULTISYNTH4_PARAMETERS_5 = const(78)
_SI5351_REGISTER_79_MULTISYNTH4_PARAMETERS_6 = const(79)
_SI5351_REGISTER_80_MULTISYNTH4_PARAMETERS_7 = const(80)
_SI5351_REGISTER_81_MULTISYNTH4_PARAMETERS_8 = const(81)
_SI5351_REGISTER_82_MULTISYNTH5_PARAMETERS_1 = const(82)
_SI5351_REGISTER_83_MULTISYNTH5_PARAMETERS_2 = const(83)
_SI5351_REGISTER_84_MULTISYNTH5_PARAMETERS_3 = const(84)
_SI5351_REGISTER_85_MULTISYNTH5_PARAMETERS_4 = const(85)
_SI5351_REGISTER_86_MULTISYNTH5_PARAMETERS_5 = const(86)
_SI5351_REGISTER_87_MULTISYNTH5_PARAMETERS_6 = const(87)
_SI5351_REGISTER_88_MULTISYNTH5_PARAMETERS_7 = const(88)
_SI5351_REGISTER_89_MULTISYNTH5_PARAMETERS_8 = const(89)
_SI5351_REGISTER_90_MULTISYNTH6_PARAMETERS = const(90)
_SI5351_REGISTER_91_MULTISYNTH7_PARAMETERS = const(91)
_SI5351_REGISTER_092_CLOCK_6_7_OUTPUT_DIVIDER = const(92)
_SI5351_REGISTER_165_CLK0_INITIAL_PHASE_OFFSET = const(165)
_SI5351_REGISTER_166_CLK1_INITIAL_PHASE_OFFSET = const(166)
_SI5351_REGISTER_167_CLK2_INITIAL_PHASE_OFFSET = const(167)
_SI5351_REGISTER_168_CLK3_INITIAL_PHASE_OFFSET = const(168)
_SI5351_REGISTER_169_CLK4_INITIAL_PHASE_OFFSET = const(169)
_SI5351_REGISTER_170_CLK5_INITIAL_PHASE_OFFSET = const(170)
_SI5351_REGISTER_177_PLL_RESET = const(177)
_SI5351_REGISTER_183_CRYSTAL_INTERNAL_LOAD_CAPACITANCE = const(183)

# User-facing constants:
R_DIV_1 = 0
R_DIV_2 = 1
R_DIV_4 = 2
R_DIV_8 = 3
R_DIV_16 = 4
R_DIV_32 = 5
R_DIV_64 = 6
R_DIV_128 = 7


# Disable invalid name because p1, p2, p3 variables are false positives.
# These are legitimate register names and adding more characters obfuscates
# the intention of the code.
# pylint: disable=invalid-name

# Disable protected access warning because inner classes by design need and use
# access to protected members.
# pylint: disable=protected-access

# Another silly pylint check to disable, it has no context of the complexity
# of R divider values and explicit unrolling of them into multiple if cases
# and return statements.  Disable.
# pylint: disable=too-many-return-statements


class SI5351:
    """SI5351 clock generator.  Initialize this class by specifying:
     - i2c: The I2C bus connected to the chip.

    Optionally specify:
     - address: The I2C address of the device if it differs from the default.
    """

    # Internal class to represent a PLL on the SI5351.  There are two instances
    # of this, PLL A and PLL B.  Each can be the source for a clock output
    # (with further division performed per clock output).
    class _PLL:
        def __init__(self, si5351, base_address, clock_control_enabled):
            self._si5351 = si5351
            self._base = base_address
            self._frequency = None
            self.clock_control_enabled = clock_control_enabled

        @property
        def frequency(self):
            """Get the frequency of the PLL in hertz."""
            return self._frequency

        def _configure_registers(self, p1, p2, p3):
            # Update PLL registers.
            # The datasheet is a nightmare of typos and inconsistencies here!
            self._si5351._write_u8(self._base, (p3 & 0x0000FF00) >> 8)
            self._si5351._write_u8(self._base + 1, (p3 & 0x000000FF))
            self._si5351._write_u8(self._base + 2, (p1 & 0x00030000) >> 16)
            self._si5351._write_u8(self._base + 3, (p1 & 0x0000FF00) >> 8)
            self._si5351._write_u8(self._base + 4, (p1 & 0x000000FF))
            self._si5351._write_u8(
                self._base + 5, ((p3 & 0x000F0000) >> 12) | ((p2 & 0x000F0000) >> 16)
            )
            self._si5351._write_u8(self._base + 6, (p2 & 0x0000FF00) >> 8)
            self._si5351._write_u8(self._base + 7, (p2 & 0x000000FF))
            # Reset both PLLs.
            self._si5351._write_u8(_SI5351_REGISTER_177_PLL_RESET, (1 << 7) | (1 << 5))

        def configure_integer(self, multiplier):
            """Configure the PLL with a simple integer mulitplier for the most
            accurate (but more limited) PLL frequency generation.
            """
            assert 14 < multiplier < 91
            multiplier = int(multiplier)
            # Compute register values and configure them.
            p1 = 128 * multiplier - 512
            p2 = 0
            p3 = 1
            self._configure_registers(p1, p2, p3)
            # Calculate exact frequency and store it for reference.
            fvco = _SI5351_CRYSTAL_FREQUENCY * multiplier
            # This should actually take the floor to get the true value but
            # there's a limit on how big a value the floor can be and it's
            # easy to hit with high megahertz frequencies:
            #   https://github.com/adafruit/circuitpython/issues/572
            self._frequency = fvco

        def configure_fractional(self, multiplier, numerator, denominator):
            """Configure the PLL with a fractional multipler specified by
            multiplier and numerator/denominator.  This is less accurate and
            susceptible to jitter but allows a larger range of PLL frequencies.
            """
            assert 14 < multiplier < 91
            assert 0 < denominator <= 0xFFFFF  # Prevent divide by zero.
            assert 0 <= numerator < 0xFFFFF
            multiplier = int(multiplier)
            numerator = int(numerator)
            denominator = int(denominator)
            # Compute register values and configure them.
            p1 = int(
                128 * multiplier + math.floor(128 * ((numerator / denominator)) - 512)
            )
            p2 = int(
                128 * numerator
                - denominator * math.floor(128 * (numerator / denominator))
            )
            p3 = denominator
            self._configure_registers(p1, p2, p3)
            # Calculate exact frequency and store it for reference.
            fvco = _SI5351_CRYSTAL_FREQUENCY * (multiplier + (numerator / denominator))
            # This should actually take the floor to get the true value but
            # there's a limit on how big a value the floor can be and it's
            # easy to hit with high megahertz frequencies:
            #   https://github.com/adafruit/circuitpython/issues/572
            self._frequency = fvco

    # Another internal class to represent each clock output.  There are 3 of
    # these and they can each be independently configured to use a specific
    # PLL source and have their own divider on that PLL.
    class _Clock:
        def __init__(self, si5351, base_address, control_register, r_register):
            self._si5351 = si5351
            self._base = base_address
            self._control = control_register
            self._r = r_register
            self._pll = None
            self._divider = None

        @property
        def frequency(self):
            """Get the frequency of this clock output in hertz.  This is
            computed based on the configured PLL, clock divider, and R divider.
            """
            # Make sure a PLL and divider are present, i.e. this clock has
            # been configured, otherwise return nothing.
            if self._pll is None or self._divider is None:
                return None
            # Now calculate frequency as PLL freuqency divided by clock divider.
            base_frequency = self._pll.frequency / self._divider
            # And add a further division for the R divider if set.
            r_divider = self.r_divider
            # pylint: disable=no-else-return
            # Disable should be removed when refactor can be tested.
            if r_divider == R_DIV_1:
                return base_frequency
            elif r_divider == R_DIV_2:
                return base_frequency / 2
            elif r_divider == R_DIV_4:
                return base_frequency / 4
            elif r_divider == R_DIV_8:
                return base_frequency / 8
            elif r_divider == R_DIV_16:
                return base_frequency / 16
            elif r_divider == R_DIV_32:
                return base_frequency / 32
            elif r_divider == R_DIV_64:
                return base_frequency / 64
            elif r_divider == R_DIV_128:
                return base_frequency / 128
            else:
                raise RuntimeError("Unexpected R divider!")

        @property
        def r_divider(self):
            """Get and set the R divider value, must be one of:
            - R_DIV_1: divider of 1
            - R_DIV_2: divider of 2
            - R_DIV_4: divider of 4
            - R_DIV_8: divider of 8
            - R_DIV_16: divider of 16
            - R_DIV_32: divider of 32
            - R_DIV_64: divider of 64
            - R_DIV_128: divider of 128
            """
            reg_value = self._si5351._read_u8(self._r)
            return (reg_value >> 4) & 0x07

        @r_divider.setter
        def r_divider(self, divider):
            assert 0 <= divider <= 7
            reg_value = self._si5351._read_u8(self._r)
            reg_value &= 0x0F
            divider &= 0x07
            divider <<= 4
            reg_value |= divider
            self._si5351._write_u8(self._r, reg_value)

        def _configure_registers(self, p1, p2, p3):
            # Update MSx registers.
            self._si5351._write_u8(self._base, (p3 & 0x0000FF00) >> 8)
            self._si5351._write_u8(self._base + 1, (p3 & 0x000000FF))
            self._si5351._write_u8(self._base + 2, (p1 & 0x00030000) >> 16)
            self._si5351._write_u8(self._base + 3, (p1 & 0x0000FF00) >> 8)
            self._si5351._write_u8(self._base + 4, (p1 & 0x000000FF))
            self._si5351._write_u8(
                self._base + 5, ((p3 & 0x000F0000) >> 12) | ((p2 & 0x000F0000) >> 16)
            )
            self._si5351._write_u8(self._base + 6, (p2 & 0x0000FF00) >> 8)
            self._si5351._write_u8(self._base + 7, (p2 & 0x000000FF))

        def configure_integer(self, pll, divider):
            """Configure the clock output with the specified PLL source
            (should be a PLL instance on the SI5351 class) and specific integer
            divider.  This is the most accurate way to set the clock output
            frequency but supports less of a range of values.
            """
            assert 3 < divider < 901
            divider = int(divider)
            # Make sure the PLL is configured (has a frequency set).
            assert pll.frequency is not None
            # Compute MSx register values.
            p1 = 128 * divider - 512
            p2 = 0
            p3 = 1
            self._configure_registers(p1, p2, p3)
            # Configure the clock control register.
            control = 0x0F  # 8mA drive strength, MS0 as CLK0 source,
            # Clock not inverted, powered up
            control |= pll.clock_control_enabled
            control |= 1 << 6  # Enable integer mode.
            self._si5351._write_u8(self._control, control)
            # Store the PLL and divisor value so frequency can be calculated.
            self._pll = pll
            self._divider = divider

        def configure_fractional(self, pll, divider, numerator, denominator):
            """Configure the clock output with the specified PLL source
            (should be a PLL instance on the SI5351 class) and specifiec
            fractional divider with numerator/denominator.  Again this is less
            accurate but has a wider range of output frequencies.
            """
            assert 3 < divider < 901
            assert 0 < denominator <= 0xFFFFF  # Prevent divide by zero.
            assert 0 <= numerator < 0xFFFFF
            divider = int(divider)
            numerator = int(numerator)
            denominator = int(denominator)
            # Make sure the PLL is configured (has a frequency set).
            assert pll.frequency is not None
            # Compute MSx register values.
            p1 = int(128 * divider + math.floor(128 * (numerator / denominator)) - 512)
            p2 = int(
                128 * numerator
                - denominator * math.floor(128 * (numerator / denominator))
            )
            p3 = denominator
            self._configure_registers(p1, p2, p3)
            # Configure the clock control register.
            control = 0x0F  # 8mA drive strength, MS0 as CLK0 source,
            # Clock not inverted, powered up
            control |= pll.clock_control_enabled
            self._si5351._write_u8(self._control, control)
            # Store the PLL and divisor value so frequency can be calculated.
            self._pll = pll
            self._divider = divider + (numerator / denominator)

    # Class-level buffer to reduce allocations and heap fragmentation.
    # This is not thread-safe or re-entrant by design!
    _BUFFER = bytearray(2)

    def __init__(self, i2c, *, address=_SI5351_ADDRESS):
        self._device = i2c_device.I2CDevice(i2c, address)
        # Setup the SI5351.
        # Disable all outputs setting CLKx_DIS high.
        self._write_u8(_SI5351_REGISTER_3_OUTPUT_ENABLE_CONTROL, 0xFF)
        # Power down all output drivers
        self._write_u8(_SI5351_REGISTER_16_CLK0_CONTROL, 0x80)
        self._write_u8(_SI5351_REGISTER_17_CLK1_CONTROL, 0x80)
        self._write_u8(_SI5351_REGISTER_18_CLK2_CONTROL, 0x80)
        self._write_u8(_SI5351_REGISTER_19_CLK3_CONTROL, 0x80)
        self._write_u8(_SI5351_REGISTER_20_CLK4_CONTROL, 0x80)
        self._write_u8(_SI5351_REGISTER_21_CLK5_CONTROL, 0x80)
        self._write_u8(_SI5351_REGISTER_22_CLK6_CONTROL, 0x80)
        self._write_u8(_SI5351_REGISTER_23_CLK7_CONTROL, 0x80)
        # Initialize PLL A and B objects.
        self.pll_a = self._PLL(self, 26, 0)
        self.pll_b = self._PLL(self, 34, (1 << 5))
        # Initialize the 3 clock outputs.
        self.clock_0 = self._Clock(
            self,
            _SI5351_REGISTER_42_MULTISYNTH0_PARAMETERS_1,
            _SI5351_REGISTER_16_CLK0_CONTROL,
            _SI5351_REGISTER_44_MULTISYNTH0_PARAMETERS_3,
        )
        self.clock_1 = self._Clock(
            self,
            _SI5351_REGISTER_50_MULTISYNTH1_PARAMETERS_1,
            _SI5351_REGISTER_17_CLK1_CONTROL,
            _SI5351_REGISTER_52_MULTISYNTH1_PARAMETERS_3,
        )
        self.clock_2 = self._Clock(
            self,
            _SI5351_REGISTER_58_MULTISYNTH2_PARAMETERS_1,
            _SI5351_REGISTER_18_CLK2_CONTROL,
            _SI5351_REGISTER_60_MULTISYNTH2_PARAMETERS_3,
        )

    def _read_u8(self, address):
        # Read an 8-bit unsigned value from the specified 8-bit address.
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            i2c.write(self._BUFFER, end=1)
            i2c.readinto(self._BUFFER, end=1)
        return self._BUFFER[0]

    def _write_u8(self, address, val):
        # Write an 8-bit unsigned value to the specified 8-bit address.
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            self._BUFFER[1] = val & 0xFF
            i2c.write(self._BUFFER, end=2)

    @property
    def outputs_enabled(self):
        """Get and set the enabled state of all clock outputs as a boolean.
        If true then all clock outputs are enabled, and if false then they are
        all disabled.
        """
        return self._read_u8(_SI5351_REGISTER_3_OUTPUT_ENABLE_CONTROL) == 0xFF

    @outputs_enabled.setter
    def outputs_enabled(self, val):
        if not val:
            self._write_u8(_SI5351_REGISTER_3_OUTPUT_ENABLE_CONTROL, 0xFF)
        else:
            self._write_u8(_SI5351_REGISTER_3_OUTPUT_ENABLE_CONTROL, 0x00)
