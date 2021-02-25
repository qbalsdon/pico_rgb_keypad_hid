# SPDX-FileCopyrightText: 2019 wallarug Robotics Masters
#
# SPDX-License-Identifier: MIT

# pylint: disable=missing-docstring,invalid-name,too-many-public-methods,too-few-public-methods

"""
`adafruit_seesaw.robohat` - Pin definition for RoboHAT
======================================================
"""

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


__version__ = "1.7.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_seesaw.git"

# Robo HAT MM1 Board: https://www.crowdsupply.com/robotics-masters/robo-hat-mm1

# The ordering here reflects the seesaw firmware (mm1_hat) pinmap for Robo HAT MM1,
# not logical ordering of the HAT terminals.

_MM1_D0 = const(55)  # (RX to RPI_TX)
_MM1_D1 = const(54)  # (TX to RPI_RX)
_MM1_D2 = const(34)  # ADC (GPS_TX)
_MM1_D3 = const(35)  # ADC (GPS_RX)
_MM1_D4 = const(0)  # (GPS_SDA)
_MM1_D5 = const(1)  # (GPS_SCL)
_MM1_D6 = const(28)  # (POWER_ENABLE)
_MM1_D7 = const(2)  # (BATTERY)
_MM1_D8 = const(20)  # (NEOPIXEL)
_MM1_D9 = const(43)  # PWM (SPI_SCK)
_MM1_D10 = const(41)  # PWM (SPI_SS)
_MM1_D11 = const(42)  # PWM (SPI_MOSI)
_MM1_D12 = const(40)  # PWM (SPI_MISO)
_MM1_D13 = const(21)  # LED
_MM1_D14 = const(3)  # (POWER_OFF)

_MM1_SERVO8 = const(8)
_MM1_SERVO7 = const(9)
_MM1_SERVO6 = const(10)
_MM1_SERVO5 = const(11)
_MM1_SERVO4 = const(19)
_MM1_SERVO3 = const(18)
_MM1_SERVO2 = const(17)
_MM1_SERVO1 = const(16)

_MM1_RCH1 = const(7)
_MM1_RCH2 = const(6)
_MM1_RCH3 = const(5)
_MM1_RCH4 = const(4)


# seesaw firmware has indexed lists of pins by function.
# These "pin" numbers map to real PAxx, PBxx pins on the board implementing seesaaw
# They may or may not match.
# See seesaw/include/SeesawConfig.h and seesaw/boards/robohatmm1/board_config.h for the pin choices.

# You must look at both files and combine the defaults in SeesawConfig.h with the
# overrides in robohatmm1/board_config.h.
# PA<nn> pins are nn
# PB<nn> pins are 32+nn


class MM1_Pinmap:
    """This class is automatically used by `adafruit_seesaw.seesaw.Seesaw` when
    a RoboHAT board is detected.

    It is also a reference for the capabilities of each pin."""

    # seesaw firmware (mm1_hat) analog pin map:
    # analog[0]:47    analog[1]:48    analog[2]:     analog[3]:
    # analog[4]:    analog[5]:    analog[6]:    analog[7]:
    #
    #: The pins capable of analog output
    analog_pins = (_MM1_D3, _MM1_D2)

    #: The effective bit resolution of the PWM pins
    pwm_width = 16

    # seesaw firmware (mm1_hat) pwm pin map:
    # pwm[0]:16   pwm[1]:17    pwm[2]:18    pwm[3]:19    pwm[4]:11    pwm[5]:10
    # pwm[6]:9    pwm[7]:8    pwm[8]:40    pwm[9]:41    pwm[10]:42   pwm[11]:43
    #
    #: The pins capable of PWM output
    pwm_pins = (
        _MM1_SERVO1,
        _MM1_SERVO2,
        _MM1_SERVO3,
        _MM1_SERVO4,
        _MM1_SERVO5,
        _MM1_SERVO6,
        _MM1_SERVO7,
        _MM1_SERVO8,
        _MM1_D12,
        _MM1_D10,
        _MM1_D11,
        _MM1_D9,
    )

    # seesaw firmware touch pin map:
    # touch[0]: 7    touch[1]: 6    touch[2]: 5    touch[3]: 4
    #: The pins capable of touch input
    touch_pins = (_MM1_RCH1, _MM1_RCH2, _MM1_RCH3, _MM1_RCH4)
