# SPDX-FileCopyrightText: 2018 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_crickit`
==========================

Convenience library for using the Adafruit Crickit robotics boards.

* Author(s): Dan Halbert

Implementation Notes
--------------------

**Hardware:**

   `Adafruit Crickit for Circuit Playground Express <https://www.adafruit.com/3093>`_
   `Adafruit Crickit FeatherWing <https://www.adafruit.com/3343>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

import sys

import board

from micropython import const

# pylint: disable=wrong-import-position
try:
    lib_index = sys.path.index("/lib")  # pylint: disable=invalid-name
    if lib_index < sys.path.index(".frozen"):
        # Prefer frozen modules over those in /lib.
        sys.path.insert(lib_index, ".frozen")
except ValueError:
    # Don't change sys.path if it doesn't contain "lib" or ".frozen".
    pass

from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.crickit import Crickit_Pinmap
from adafruit_seesaw.pwmout import PWMOut
from adafruit_motor.servo import Servo, ContinuousServo
from adafruit_motor.motor import DCMotor
from adafruit_motor.stepper import StepperMotor

__version__ = "2.3.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Crickit.git"


_SERVO1 = const(17)
_SERVO2 = const(16)
_SERVO3 = const(15)
_SERVO4 = const(14)

_MOTOR1 = (22, 23)
_MOTOR2 = (19, 18)
# Order as needed for steppers.
_MOTOR_STEPPER = _MOTOR1 + _MOTOR2

_DRIVE1 = const(13)
_DRIVE2 = const(12)
_DRIVE3 = const(43)
_DRIVE4 = const(42)

# Order as needed for steppers.
_DRIVE_STEPPER = (_DRIVE1, _DRIVE3, _DRIVE2, _DRIVE4)


_TOUCH1 = const(4)
_TOUCH2 = const(5)
_TOUCH3 = const(6)
_TOUCH4 = const(7)

_NEOPIXEL = const(20)
_SS_PIXEL = const(27)

# pylint: disable=too-few-public-methods
class CrickitTouchIn:
    """Imitate touchio.TouchIn."""

    def __init__(self, seesaw, pin):
        self._seesaw = seesaw
        self._pin = pin
        self.threshold = self.raw_value + 100

    @property
    def raw_value(self):
        """The raw touch measurement as an `int`. (read-only)"""
        return self._seesaw.touch_read(self._pin)

    @property
    def value(self):
        """Whether the touch pad is being touched or not. (read-only)"""
        return self.raw_value > self.threshold


# pylint: disable=too-many-public-methods
class Crickit:
    """Represents a Crickit board. Provides a number of devices available via properties, such as
    ``servo_1``. Devices are created on demand the first time they are referenced.

    It's fine to refer a device multiple times via its property, but it's faster and results
    in more compact code to assign a device to a variable.

    .. code-block:: python

      import time
      from adafruit_crickit import crickit

      # This is fine:
      crickit.servo_1.angle = 0
      time.sleep(1)
      crickit.servo_1.angle = 90
      time.sleep(1)

      # This is slightly faster and more compact:
      servo_1 = crickit.servo_1
      servo_1.angle = 0
      time.sleep(1)
      servo_1.angle = 90
      time.sleep(1)
    """

    SIGNAL1 = 2
    """Signal 1 terminal"""
    SIGNAL2 = 3
    """Signal 2 terminal"""
    SIGNAL3 = 40
    """Signal 3 terminal"""
    SIGNAL4 = 41
    """Signal 4 terminal"""
    SIGNAL5 = 11
    """Signal 5 terminal"""
    SIGNAL6 = 10
    """Signal 6 terminal"""
    SIGNAL7 = 9
    """Signal 7 terminal"""
    SIGNAL8 = 8
    """Signal 8 terminal"""

    def __init__(self, seesaw):
        self._seesaw = seesaw
        self._seesaw.pin_mapping = Crickit_Pinmap
        # Associate terminal(s) with certain devices.
        # Used to find existing devices.
        self._devices = dict()
        self._neopixel = None
        self._onboard_pixel = None

    @property
    def seesaw(self):
        """The Seesaw object that talks to the Crickit. Use this object to manipulate the
        signal pins that correspond to Crickit terminals.

        .. code-block:: python

          from adafruit_crickit import crickit

          ss = crickit.seesaw
          ss.pin_mode(crickit.SIGNAL4, ss.OUTPUT)
          ss.digital_write(crickit.SIGNAL4], True)
        """

        return self._seesaw

    @property
    def servo_1(self):
        """``adafruit_motor.servo.Servo`` object on Servo 1 terminal"""
        return self._servo(_SERVO1, Servo)

    @property
    def servo_2(self):
        """``adafruit_motor.servo.Servo`` object on Servo 2 terminal"""
        return self._servo(_SERVO2, Servo)

    @property
    def servo_3(self):
        """``adafruit_motor.servo.Servo`` object on Servo 3 terminal"""
        return self._servo(_SERVO3, Servo)

    @property
    def servo_4(self):
        """``adafruit_motor.servo.Servo`` object on Servo 4 terminal"""
        return self._servo(_SERVO4, Servo)

    @property
    def continuous_servo_1(self):
        """``adafruit_motor.servo.ContinuousServo`` object on Servo 1 terminal"""
        return self._servo(_SERVO1, ContinuousServo)

    @property
    def continuous_servo_2(self):
        """``adafruit_motor.servo.ContinuousServo`` object on Servo 2 terminal"""
        return self._servo(_SERVO2, ContinuousServo)

    @property
    def continuous_servo_3(self):
        """``adafruit_motor.servo.ContinuousServo`` object on Servo 3 terminal"""
        return self._servo(_SERVO3, ContinuousServo)

    @property
    def continuous_servo_4(self):
        """``adafruit_motor.servo.ContinuousServo`` object on Servo 4 terminal"""
        return self._servo(_SERVO4, ContinuousServo)

    def _servo(self, terminal, servo_class):
        device = self._devices.get(terminal, None)
        if not isinstance(device, servo_class):
            pwm = PWMOut(self._seesaw, terminal)
            pwm.frequency = 50
            device = servo_class(pwm)
            self._devices[terminal] = device
        return device

    @property
    def dc_motor_1(self):
        """``adafruit_motor.motor.DCMotor`` object on Motor 1 terminals"""
        return self._motor(_MOTOR1, DCMotor)

    @property
    def dc_motor_2(self):
        """``adafruit_motor.motor.DCMotor`` object on Motor 2 terminals"""
        return self._motor(_MOTOR2, DCMotor)

    @property
    def stepper_motor(self):
        """``adafruit_motor.motor.StepperMotor`` object on Motor 1 and Motor 2 terminals"""
        return self._motor(_MOTOR_STEPPER, StepperMotor)

    @property
    def drive_stepper_motor(self):
        """``adafruit_motor.motor.StepperMotor`` object on Drive terminals"""
        return self._motor(_DRIVE_STEPPER, StepperMotor)

    @property
    def feather_drive_stepper_motor(self):
        """``adafruit_motor.motor.StepperMotor`` object on Drive terminals on Crickit FeatherWing"""
        return self._motor(tuple(reversed(_DRIVE_STEPPER)), StepperMotor)

    def _motor(self, terminals, motor_class):
        device = self._devices.get(terminals, None)
        if not isinstance(device, motor_class):
            device = motor_class(
                *(PWMOut(self._seesaw, terminal) for terminal in terminals)
            )
            self._devices[terminals] = device
        return device

    @property
    def drive_1(self):
        """``adafruit_seesaw.pwmout.PWMOut`` object on Drive 1 terminal, with ``frequency=1000``"""
        return self._drive(_DRIVE1)

    @property
    def drive_2(self):
        """``adafruit_seesaw.pwmout.PWMOut`` object on Drive 2 terminal, with ``frequency=1000``"""
        return self._drive(_DRIVE2)

    @property
    def drive_3(self):
        """``adafruit_seesaw.pwmout.PWMOut`` object on Drive 3 terminal, with ``frequency=1000``"""
        return self._drive(_DRIVE3)

    @property
    def drive_4(self):
        """``adafruit_seesaw.pwmout.PWMOut`` object on Drive 4 terminal, with ``frequency=1000``"""
        return self._drive(_DRIVE4)

    feather_drive_1 = drive_4
    """``adafruit_seesaw.pwmout.PWMOut`` object on Crickit Featherwing Drive 1 terminal,
    with ``frequency=1000``
    """
    feather_drive_2 = drive_3
    """``adafruit_seesaw.pwmout.PWMOut`` object on Crickit Featherwing Drive 2 terminal,
    with ``frequency=1000``
    """
    feather_drive_3 = drive_2
    """``adafruit_seesaw.pwmout.PWMOut`` object on Crickit Featherwing Drive 3 terminal,
    with ``frequency=1000``
    """
    feather_drive_4 = drive_1
    """``adafruit_seesaw.pwmout.PWMOut`` object on Crickit Featherwing Drive 4 terminal,
    with ``frequency=1000``
    """

    def _drive(self, terminal):
        device = self._devices.get(terminal, None)
        if not isinstance(device, PWMOut):
            device = PWMOut(self._seesaw, terminal)
            device.frequency = 1000
            self._devices[terminal] = device
        return device

    @property
    def touch_1(self):
        """``adafruit_crickit.CrickitTouchIn`` object on Touch 1 terminal"""
        return self._touch(_TOUCH1)

    @property
    def touch_2(self):
        """``adafruit_crickit.CrickitTouchIn`` object on Touch 2 terminal"""
        return self._touch(_TOUCH2)

    @property
    def touch_3(self):
        """``adafruit_crickit.CrickitTouchIn`` object on Touch 3 terminal"""
        return self._touch(_TOUCH3)

    @property
    def touch_4(self):
        """``adafruit_crickit.CrickitTouchIn`` object on Touch 4 terminal"""
        return self._touch(_TOUCH4)

    def _touch(self, terminal):
        touch_in = self._devices.get(terminal, None)
        if not touch_in:
            touch_in = CrickitTouchIn(self._seesaw, terminal)
            self._devices[terminal] = touch_in
        return touch_in

    @property
    def neopixel(self):
        """```adafruit_seesaw.neopixel`` object on NeoPixel terminal.
        Raises ValueError if ``init_neopixel`` has not been called.
        """
        if not self._neopixel:
            raise ValueError("Call init_neopixel first")
        return self._neopixel

    def init_neopixel(
        self, n, *, bpp=3, brightness=1.0, auto_write=True, pixel_order=None
    ):
        """Set up a seesaw.NeoPixel object

        .. note:: On the CPX Crickit board, the NeoPixel terminal is by default
          controlled by CPX pin A1, and is not controlled by seesaw. So this object
          will not be usable. Instead, use the regular NeoPixel library
          and specify ``board.A1`` as the pin.

        You can change the jumper connection on the bottom of the CPX Crickit board
        to move control of the NeoPixel terminal to seesaw pin #20 (terminal.NEOPIXEL).
        In addition, the Crickit FeatherWing always uses seesaw pin #20.
        In either of those cases, this object will work.

        .. code-block:: python

          from adafruit_crickit.crickit import crickit

          crickit.init_neopixel(24)
          crickit.neopixel.fill((100, 0, 0))
        """
        from adafruit_seesaw.neopixel import (  # pylint: disable=import-outside-toplevel
            NeoPixel,
        )

        self._neopixel = NeoPixel(
            self._seesaw,
            _NEOPIXEL,
            n,
            bpp=bpp,
            brightness=brightness,
            auto_write=auto_write,
            pixel_order=pixel_order,
        )

    @property
    def onboard_pixel(self):
        """```adafruit_seesaw.neopixel`` object on the Seesaw on-board NeoPixel.
        Initialize on-board NeoPixel and clear upon first use.
        """
        if not self._onboard_pixel:
            from adafruit_seesaw.neopixel import (  # pylint: disable=import-outside-toplevel
                NeoPixel,
            )

            self._onboard_pixel = NeoPixel(
                self._seesaw,
                _SS_PIXEL,
                1,
                bpp=3,
                brightness=1.0,
                auto_write=True,
                pixel_order=None,
            )
            self._onboard_pixel.fill((0, 0, 0))
        return self._onboard_pixel

    def reset(self):
        """Reset the whole Crickit board."""
        self._seesaw.sw_reset()


crickit = None  # pylint: disable=invalid-name
"""A singleton instance to control a single Crickit board, controlled by the default I2C pins."""

# Sphinx's board is missing real pins so skip the constructor in that case.
if "I2C" in dir(board):
    crickit = Crickit(Seesaw(board.I2C()))  # pylint: disable=invalid-name
