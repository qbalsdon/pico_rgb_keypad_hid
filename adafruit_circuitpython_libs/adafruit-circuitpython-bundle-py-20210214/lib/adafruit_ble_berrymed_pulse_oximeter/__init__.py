# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_berrymed_pulse_oximeter`
================================================================================

BLE Support for Berrymed Pulse Oximeters


* Author(s): Adafruit Industries

Implementation Notes
--------------------

**Hardware:**

* BM1000, made by Shanghai Berry Electronic Tech Co.,Ltd.
  Device labeling is not consistent.
  May be identified on device label, box, or in BLE advertisement as
  BM1000, BM1000B, BM1000C, or BM1000E.

  Protocol defined here:

    * https://github.com/zh2x/BCI_Protocol.

  Thanks as well to:

    * https://github.com/ehborisov/BerryMed-Pulse-Oximeter-tool
    * https://github.com/ScheindorfHyenetics/berrymedBluetoothOxymeter

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

# imports

from collections import namedtuple
import struct

from .adafruit_ble_transparent_uart import TransparentUARTService

__version__ = "2.0.5"
__repo__ = (
    "https://github.com/adafruit/Adafruit_CircuitPython_BLE_BerryMed_Pulse_Oximeter.git"
)


PulseOximeterValues = namedtuple(
    "PulseOximeterValues",
    ("valid", "spo2", "pulse_rate", "pleth", "finger_present"),
)
"""Namedtuple for measurement values.

* `PulseOximeterValues.valid`

        ``True`` if sensor readings are not valid right now

* `PulseOximeterValues.finger_present`

        ``True`` if finger present.

* `PulseOximeterValues.spo2`

        SpO2 value (int): 0-100%: blood oxygen saturation level.

* `PulseOximeterValues.pulse_rate`

        Pulse rate, in beats per minute (int).

* `PulseOximeterValues.pleth`

        Plethysmograph value, 0-100 (int).

For example::

    bpm = svc.values.pulse_rate
"""


class BerryMedPulseOximeterService(TransparentUARTService):
    """Service for reading from a BerryMed BM1000C or BM100E Pulse oximeter."""

    @property
    def values(self):
        """All the pulse oximeter values, returned as a PulseOximeterValues
        namedtuple.

        Return ``None`` if no data available.
        """
        # Discard stale data.
        self.reset_input_buffer()
        # Data packets are five bytes long. The first byte has its high bit set;
        # the rest do not. Read up to five bytes to get back in sync.
        have_header = False
        for _ in range(5):
            first_byte = self.read(1)
            if not first_byte:
                # Nothing read, even after stream timeout.
                return None
            header = first_byte[0]
            if header & 0x80:
                have_header = True
                break

        if not have_header:
            # Failed to synchronize.
            return None

        data = self.read(4)
        if not data or len(data) != 4:
            return None

        # Ignoring these values, which aren't that interesting.
        #
        # pulse_beep = bool(header & 0x40)
        # probe_unplugged = bool(header & 0x20)
        #
        # Bar graph height: not sure what this is measuring
        # bar_graph = data[1] & 0x0F
        #
        # This is the device sensor signal, not the BLE signal.
        # has_sensor_signal = bool(header & 0x010)
        # sensor_signal_strength = header & 0x0F
        #
        # Acquiring pulse value
        # pulse_search = bool(data[1] & 0x20)

        # Plethysmograph value, 0-100.
        pleth = data[0]

        # Finger detected
        finger_present = not bool(data[1] & 0x10)

        # Pulse rate: 255 if invalid.
        # The high bit of the pulse rate is sent in a different byte.
        pulse_rate = data[2] | (data[1] & 0x40) << 1

        # SpO2: 0-100, or 127 if invalid
        spo2 = data[3]

        valid = spo2 != 127

        return PulseOximeterValues(
            valid=valid,
            finger_present=finger_present,
            spo2=spo2,
            pulse_rate=pulse_rate,
            pleth=pleth,
        )
