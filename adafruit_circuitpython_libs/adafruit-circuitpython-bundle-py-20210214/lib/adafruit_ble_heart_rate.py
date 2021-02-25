# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_heart_rate`
================================================================================

BLE Heart Rate Service


* Author(s): Dan Halbert for Adafruit Industries

The Heart Rate Service is specified here:
https://www.bluetooth.com/wp-content/uploads/Sitecore-Media-Library/Gatt/Xml/Services/org.bluetooth.service.heart_rate.xml

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

__version__ = "1.1.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Heart_Rate.git"

HeartRateMeasurementValues = namedtuple(
    "HeartRateMeasurementValues",
    ("heart_rate", "contact", "energy_expended", "rr_intervals"),
)
"""Namedtuple for measurement values.

* `HeartRateMeasurementValues.heart_rate`

        Heart rate (int), in beats per minute.

* `HeartRateMeasurementValues.contact`

        ``True`` if device is contacting the body, ``False`` if not,
        ``None`` if device does not support contact detection.

* `HeartRateMeasurementValues.energy_expended`

        Energy expended (int), in kilo joules, or ``None`` if no value.

* `HeartRateMeasurementValues.rr_intervals`

        Sequence of RR intervals, measuring the time between
        beats. Oldest first, in ints that are units of 1024ths of a second.
        This sequence will be empty if the device does not report the intervals.
        *Caution:* inexpensive heart rate monitors may not measure this
        accurately. Do not use for diagnosis.

For example::

    bpm = svc.measurement_values.heart_rate
"""


class _HeartRateMeasurement(ComplexCharacteristic):
    """Notify-only characteristic of streaming heart rate data."""

    uuid = StandardUUID(0x2A37)

    def __init__(self):
        super().__init__(properties=Characteristic.NOTIFY)

    def bind(self, service):
        """Bind to a HeartRateService."""
        bound_characteristic = super().bind(service)
        bound_characteristic.set_cccd(notify=True)
        # Use a PacketBuffer that can store one packet to receive the HRM data.
        return _bleio.PacketBuffer(bound_characteristic, buffer_size=1)


class HeartRateService(Service):
    """Service for reading from a Heart Rate sensor."""

    # 0x180D is the standard HRM 16-bit, on top of standard base UUID
    uuid = StandardUUID(0x180D)

    # uint8: flags
    #  bit 0 = 0: Heart Rate Value is uint8
    #  bit 0 = 1: Heart Rate Value is uint16
    #  bits 2:1 = 0 or 1: Sensor Contact Feature not supported
    #  bits 2:1 = 2: Sensor Contact Feature supported, contact is not detected
    #  bits 2:1 = 3: Sensor Contact Feature supported, contacted is detected
    #  bit 3 = 0: Energy Expended field is not present
    #  bit 3 = 1: Energy Expended field is present. Units: kilo Joules
    #  bit 4 = 0: RR-Interval values are not present
    #  bit 4 = 1: One or more RR-Interval values are present
    #
    # next uint8 or uint16: Heart Rate Value
    # next uint16: Energy Expended, if present
    # next uint16 (multiple): RR-Interval values, resolution of 1/1024 second
    #   in order of oldest to newest
    #
    # Mandatory for Heart Rate Service
    heart_rate_measurement = _HeartRateMeasurement()
    # Optional for Heart Rate Service.
    body_sensor_location = Uint8Characteristic(
        uuid=StandardUUID(0x2A38), properties=Characteristic.READ
    )

    # Mandatory only if Energy Expended features is supported.
    heart_rate_control_point = Uint8Characteristic(
        uuid=StandardUUID(0x2A39), properties=Characteristic.WRITE
    )

    _BODY_LOCATIONS = ("Other", "Chest", "Wrist", "Finger", "Hand", "Ear Lobe", "Foot")

    def __init__(self, service=None):
        super().__init__(service=service)
        # Defer creating buffer until needed.
        self._measurement_buf = None

    @property
    def measurement_values(self):
        """All the measurement values, returned as a HeartRateMeasurementValues
        namedtuple.

        Return ``None`` if no packet has been read yet.
        """
        # pylint: disable=no-member
        if self._measurement_buf is None:
            self._measurement_buf = bytearray(self.heart_rate_measurement.packet_size)
        buf = self._measurement_buf
        packet_length = self.heart_rate_measurement.readinto(buf)
        # pylint: enable=no-member
        if packet_length == 0:
            return None
        flags = buf[0]
        next_byte = 1

        if flags & 0x1:
            bpm = struct.unpack_from("<H", buf, next_byte)[0]
            next_byte += 2
        else:
            bpm = struct.unpack_from("<B", buf, next_byte)[0]
            next_byte += 1

        if flags & 0x4:
            # True or False if Sensor Contact Feature is supported.
            contact = bool(flags & 0x2)
        else:
            # None (meaning we don't know) if Sensor Contact Feature is not supported.
            contact = None

        if flags & 0x8:
            energy_expended = struct.unpack_from("<H", buf, next_byte)[0]
            next_byte += 2
        else:
            energy_expended = None

        rr_values = []
        if flags & 0x10:
            for offset in range(next_byte, packet_length, 2):
                rr_val = struct.unpack_from("<H", buf, offset)[0]
                rr_values.append(rr_val)

        return HeartRateMeasurementValues(bpm, contact, energy_expended, rr_values)

    @property
    def location(self):
        """The location of the sensor on the human body, as a string.

        Note that the specification describes a limited number of locations.
        But the sensor manufacturer may specify using a non-standard location.
        For instance, some armbands are meant to be worn just below the inner elbow,
        but that is not a prescribed location. So the sensor will report something
        else, such as "Wrist".

        Possible values are:
        "Other", "Chest", "Wrist", "Finger", "Hand", "Ear Lobe", "Foot", and
        "InvalidLocation" (if value returned does not match the specification).
        """

        try:
            return self._BODY_LOCATIONS[self.body_sensor_location]
        except IndexError:
            return "InvalidLocation"
