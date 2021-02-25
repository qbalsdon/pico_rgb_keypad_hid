# The MIT License (MIT)
#
# Copyright (c) 2020 Dan Halbert for Adafruit Industries LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_ble_cycling_speed_and_cadence`
================================================================================

BLE Cycling Speed and Cadence Service


* Author(s): Dan Halbert for Adafruit Industries

The Cycling Speed and Cadence Service is specified here:
https://www.bluetooth.com/wp-content/uploads/Sitecore-Media-Library/Gatt/Xml/Services/org.bluetooth.service.cycling_speed_and_cadence.xml

Implementation Notes
--------------------

**Hardware:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's BLE library: https://github.com/adafruit/Adafruit_CircuitPython_BLE
"""
import struct
from collections import namedtuple

import _bleio
from adafruit_ble.services import Service
from adafruit_ble.uuid import StandardUUID
from adafruit_ble.characteristics import Characteristic, ComplexCharacteristic
from adafruit_ble.characteristics.int import Uint8Characteristic

__version__ = "1.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Cycling_Speed_and_Cadence.git"

CSCMeasurementValues = namedtuple(
    "CSCMeasurementValues",
    (
        "cumulative_wheel_revolutions",
        "last_wheel_event_time",
        "cumulative_crank_revolutions",
        "last_crank_event_time",
    ),
)
"""Namedtuple for measurement values.

.. :attribute:: cumulative_wheel_revolutions:

        Cumulative wheel revolutions (int).

.. :attribute:: last_wheel_event_time:

        Time (int), units in 1024ths of a second, when last wheel event was measured.
        This is a monotonically increasing clock value, not an interval.

.. :attribute:: cumulative_crank_revolutions:

        Cumulative crank revolutions (int).

.. :attribute:: last_crank_event_time:

        Time (int), units in 1024ths of a second, when last crank event was measured.
        This is a monotonically increasing clock value, not an interval.

For example::

    wheel_revs = svc.csc_measurement_values.cumulative_wheel_revolutions
"""


class _CSCMeasurement(ComplexCharacteristic):
    """Notify-only characteristic of speed and cadence data."""

    uuid = StandardUUID(0x2A5B)

    def __init__(self):
        super().__init__(properties=Characteristic.NOTIFY)

    def bind(self, service):
        """Bind to a CyclingSpeedAndCadenceService."""
        bound_characteristic = super().bind(service)
        bound_characteristic.set_cccd(notify=True)
        # Use a PacketBuffer that can store one packet to receive the SCS data.
        return _bleio.PacketBuffer(bound_characteristic, buffer_size=1)


class CyclingSpeedAndCadenceService(Service):
    """Service for reading from a Cycling Speed and Cadence sensor."""

    # 0x180D is the standard HRM 16-bit, on top of standard base UUID
    uuid = StandardUUID(0x1816)

    # Mandatory.
    csc_measurement = _CSCMeasurement()

    csc_feature = Uint8Characteristic(
        uuid=StandardUUID(0x2A5C), properties=Characteristic.READ
    )
    sensor_location = Uint8Characteristic(
        uuid=StandardUUID(0x2A5D), properties=Characteristic.READ
    )

    sc_control_point = Characteristic(
        uuid=StandardUUID(0x2A39), properties=Characteristic.WRITE
    )

    _SENSOR_LOCATIONS = (
        "Other",
        "Top of shoe",
        "In shoe",
        "Hip",
        "Front Wheel",
        "Left Crank",
        "Right Crank",
        "Left Pedal",
        "Right Pedal",
        "Front Hub",
        "Rear Dropout",
        "Chainstay",
        "Rear Wheel",
        "Rear Hub",
        "Chest",
        "Spider",
        "Chain Ring",
    )

    def __init__(self, service=None):
        super().__init__(service=service)
        # Defer creating buffer until we're definitely connected.
        self._measurement_buf = None

    @property
    def measurement_values(self):
        """All the measurement values, returned as a CSCMeasurementValues
        namedtuple.

        Return ``None`` if no packet has been read yet.
        """
        # uint8: flags
        #  bit 0 = 1: Wheel Revolution Data is present
        #  bit 1 = 1: Crank Revolution Data is present
        #
        # The next two fields are present only if bit 0 above is 1:
        #   uint32: Cumulative Wheel Revolutions
        #   uint16: Last Wheel Event Time, in 1024ths of a second
        #
        # The next two fields are present only if bit 10 above is 1:
        #   uint16: Cumulative Crank Revolutions
        #   uint16: Last Crank Event Time, in 1024ths of a second
        #

        if self._measurement_buf is None:
            self._measurement_buf = bytearray(
                self.csc_measurement.incoming_packet_length  # pylint: disable=no-member
            )
        buf = self._measurement_buf
        packet_length = self.csc_measurement.readinto(buf)  # pylint: disable=no-member
        if packet_length == 0:
            return None
        flags = buf[0]
        next_byte = 1

        if flags & 0x1:
            wheel_revs = struct.unpack_from("<L", buf, next_byte)[0]
            wheel_time = struct.unpack_from("<H", buf, next_byte + 4)[0]
            next_byte += 6
        else:
            wheel_revs = wheel_time = None

        if flags & 0x2:
            # Note that wheel revs is uint32 and and crank revs is uint16.
            crank_revs = struct.unpack_from("<H", buf, next_byte)[0]
            crank_time = struct.unpack_from("<H", buf, next_byte + 2)[0]
        else:
            crank_revs = crank_time = None

        return CSCMeasurementValues(wheel_revs, wheel_time, crank_revs, crank_time)

    @property
    def location(self):
        """The location of the sensor on the cycle, as a string.

        Possible values are:
        "Other", "Top of shoe", "In shoe", "Hip",
        "Front Wheel", "Left Crank", "Right Crank",
        "Left Pedal", "Right Pedal", "Front Hub",
        "Rear Dropout", "Chainstay", "Rear Wheel",
        "Rear Hub", "Chest", "Spider", "Chain Ring")
        "Other", "Chest", "Wrist", "Finger", "Hand", "Ear Lobe", "Foot",
        and "InvalidLocation" (if value returned does not match the specification).
        """

        try:
            return self._SENSOR_LOCATIONS[self.sensor_location]
        except IndexError:
            return "InvalidLocation"


#    def set_cumulative_wheel_revolutions(self, value):
#        self._control_point_request(self.pack("<BLBB", 1, value, 0, )
