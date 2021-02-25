# SPDX-FileCopyrightText: 2019 Dave Astels for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_rplidar`
====================================================

Provide an interface to the Slamtech RPLidar that works in plain Python3
as well as CircuitPython/Blinka.

* Author(s): Dave Astels
* Based on https://github.com/SkoltechRobotics/rplidar by Artyom Pavlov

Implementation Notes
--------------------

**Hardware:**


**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

Version 0.0.1 does NOT support CircuitPython. Future versions will.
"""

import struct
import sys
import time
import warnings

# pylint:disable=invalid-name,undefined-variable,global-variable-not-assigned
# pylint:disable=too-many-arguments,raise-missing-from

__version__ = "1.1.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RPLIDAR.git"

SYNC_BYTE = b"\xA5"
SYNC_BYTE2 = b"\x5A"

GET_INFO_BYTE = b"\x50"
GET_HEALTH_BYTE = b"\x52"

STOP_BYTE = b"\x25"
RESET_BYTE = b"\x40"

SCAN_BYTE = b"\x20"
FORCE_SCAN_BYTE = b"\x21"

DESCRIPTOR_LEN = 7
INFO_LEN = 20
HEALTH_LEN = 3

INFO_TYPE = 4
HEALTH_TYPE = 6
SCAN_TYPE = 129

# Constants & Command to start A2 motor
MAX_MOTOR_PWM = 1023
DEFAULT_MOTOR_PWM = 660
SET_PWM_BYTE = b"\xF0"

_HEALTH_STATUSES = {
    0: "Good",
    1: "Warning",
    2: "Error",
}


class RPLidarException(Exception):
    """Basic exception class for RPLidar"""


def _process_scan(raw):
    """Processes input raw data and returns measurement data"""
    new_scan = bool(raw[0] & 0b1)
    inversed_new_scan = bool((raw[0] >> 1) & 0b1)
    quality = raw[0] >> 2
    if new_scan == inversed_new_scan:
        raise RPLidarException("New scan flags mismatch")
    check_bit = raw[1] & 0b1
    if check_bit != 1:
        raise RPLidarException("Check bit not equal to 1")
    angle = ((raw[1] >> 1) + (raw[2] << 7)) / 64.0
    distance = (raw[3] + (raw[4] << 8)) / 4.0
    return new_scan, quality, angle, distance


class RPLidar:
    """Class for communicating with RPLidar rangefinder scanners"""

    motor_pin = None  #: DigitalInOut instance controlling the motor
    _serial_port = None  #: Serial port (or UART) instance
    port = None  #: Serial port name, e.g. /dev/ttyUSB0
    timeout = 1  #: Serial port timeout
    motor = False  #: Is motor running?
    baudrate = 115200  #: Baudrate for serial port

    def __init__(self, motor_pin, port, baudrate=115200, timeout=1, logging=False):
        """Initialize RPLidar object for communicating with the sensor.

        Parameters

        port : busio.UART or str
            Serial port instance or name of the port to which the sensor is connected
        baudrate : int, optional
            Baudrate for serial connection (the default is 115200)
        timeout : float, optional
            Serial port connection timeout in seconds (the default is 1)
        logging : whether to output logging information
        """
        self.motor_pin = motor_pin
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.motor_running = False
        self.logging = logging

        self.is_CP = not isinstance(port, str)

        if self.is_CP:
            _serial_port = port
        else:
            global serial  # pylint: disable=global-statement
            import serial  # pylint: disable=import-outside-toplevel

        self.connect()
        self.start_motor()

    def log(self, level, msg):
        """Output the level and a message if logging is enabled."""
        if self.logging:
            sys.stdout.write("{0}: {1}\n".format(level, msg))

    def log_bytes(self, level, msg, ba):
        """Log and output a byte array in a readable way."""
        bs = ["%02x" % b for b in ba]
        self.log(level, msg + " ".join(bs))

    def connect(self):
        """Connects to the serial port named by the port instance var. If it was
        connected to another serial port disconnects from it first."""
        if not self.is_CP:
            if self._serial_port is not None:
                self.disconnect()
            try:
                self._serial_port = serial.Serial(
                    self.port,
                    self.baudrate,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=self.timeout,
                    dsrdtr=True,
                )
            except serial.SerialException as err:
                raise RPLidarException(
                    "Failed to connect to the sensor " "due to: %s" % err
                )

    def disconnect(self):
        """Disconnects from the serial port"""
        if self._serial_port is None:
            return
        self._serial_port.close()

    def set_pwm(self, pwm):
        """Set the motor PWM"""
        assert 0 <= pwm <= MAX_MOTOR_PWM
        payload = struct.pack("<H", pwm)
        self._send_payload_cmd(SET_PWM_BYTE, payload)

    def _control_motor(self, val):
        """Manipulate the motor"""
        if self.is_CP:
            self.motor_pin.value = val
        else:
            self._serial_port.dtr = not val

    def start_motor(self):
        """Starts sensor motor"""
        self.log("info", "Starting motor")
        # For A1
        self._control_motor(True)

        # For A2
        self.set_pwm(DEFAULT_MOTOR_PWM)
        self.motor_running = True

    def stop_motor(self):
        """Stops sensor motor"""
        self.log("info", "Stopping motor")
        # For A2
        self.set_pwm(0)
        time.sleep(0.001)
        # For A1
        self._control_motor(False)
        self.motor_running = False

    def _send_payload_cmd(self, cmd, payload):
        """Sends `cmd` command with `payload` to the sensor"""
        size = struct.pack("B", len(payload))
        req = SYNC_BYTE + cmd + size + payload
        checksum = 0
        for v in struct.unpack("B" * len(req), req):
            checksum ^= v
        req += struct.pack("B", checksum)
        self._serial_port.write(req)
        self.log_bytes("debug", "Command sent: ", req)

    def _send_cmd(self, cmd):
        """Sends `cmd` command to the sensor"""
        req = SYNC_BYTE + cmd
        self._serial_port.write(req)
        self.log_bytes("debug", "Command sent: ", req)

    def _read_descriptor(self):
        """Reads descriptor packet"""
        descriptor = self._serial_port.read(DESCRIPTOR_LEN)
        self.log_bytes("debug", "Received descriptor:", descriptor)
        if len(descriptor) != DESCRIPTOR_LEN:
            raise RPLidarException("Descriptor length mismatch")
        if not descriptor.startswith(SYNC_BYTE + SYNC_BYTE2):
            raise RPLidarException("Incorrect descriptor starting bytes")
        is_single = descriptor[-2] == 0
        return descriptor[2], is_single, descriptor[-1]

    def _read_response(self, dsize):
        """Reads response packet with length of `dsize` bytes"""
        self.log("debug", "Trying to read response: %d bytes" % dsize)
        data = self._serial_port.read(dsize)
        self.log_bytes("debug", "Received data:", data)
        if len(data) != dsize:
            raise RPLidarException("Wrong body size")
        return data

    @property
    def info(self):
        """Get device information

        Returns

        dict
            Dictionary with the sensor information
        """
        self._send_cmd(GET_INFO_BYTE)
        dsize, is_single, dtype = self._read_descriptor()
        if dsize != INFO_LEN:
            raise RPLidarException("Wrong info reply length")
        if not is_single:
            raise RPLidarException("Not a single response mode")
        if dtype != INFO_TYPE:
            raise RPLidarException("Wrong response data type")
        raw = self._read_response(dsize)
        serialnumber_bytes = struct.unpack("BBBBBBBBBBBBBBBB", raw[4:])
        serialnumber = "".join(reversed(["%02x" % b for b in serialnumber_bytes]))
        data = {
            "model": raw[0],
            "firmware": (raw[2], raw[1]),
            "hardware": raw[3],
            "serialnumber": serialnumber,
        }
        return data

    @property
    def health(self):
        """Get device health state. When the core system detects some
        potential risk that may cause hardware failure in the future,
        the returned status value will be 'Warning'. But sensor can still work
        as normal. When sensor is in the Protection Stop state, the returned
        status value will be 'Error'. In case of warning or error statuses
        non-zero error code will be returned.

        Returns

        status : str
            'Good', 'Warning' or 'Error' statuses
        error_code : int
            The related error code that caused a warning/error.
        """
        self._send_cmd(GET_HEALTH_BYTE)
        dsize, is_single, dtype = self._read_descriptor()
        if dsize != HEALTH_LEN:
            raise RPLidarException("Wrong info reply length")
        if not is_single:
            raise RPLidarException("Not a single response mode")
        if dtype != HEALTH_TYPE:
            raise RPLidarException("Wrong response data type")
        raw = self._read_response(dsize)
        status = _HEALTH_STATUSES[raw[0]]
        error_code = (raw[1] << 8) + raw[2]
        return (status, error_code)

    def clear_input(self):
        """Clears input buffer by reading all available data"""

    def stop(self):
        """Stops scanning process, disables laser diode and the measurement
        system, moves sensor to the idle state."""
        self.log("info", "Stopping scanning")
        self._send_cmd(STOP_BYTE)
        time.sleep(0.001)
        self.clear_input()

    def reset(self):
        """Resets sensor core, reverting it to a similar state as it has
        just been powered up."""
        self.log("info", "Resetting the sensor")
        self._send_cmd(RESET_BYTE)
        time.sleep(0.002)

    def iter_measurements(self, max_buf_meas=500):
        """Iterate over measurements. Note that consumer must be fast enough,
        otherwise data will be accumulated inside buffer and consumer will get
        data with increasing lag.

        Parameters

        max_buf_meas : int
            Maximum number of measurements to be stored inside the buffer. Once
            number exceeds this limit buffer will be emptied out.

        Yields

        new_scan : bool
            True if measurement belongs to a new scan
        quality : int
            Reflected laser pulse strength
        angle : float
            The measurement heading angle in degree unit [0, 360)
        distance : float
            Measured object distance related to the sensor's rotation center.
            In millimeter unit. Set to 0 when measurement is invalid.
        """
        self.start_motor()
        status, error_code = self.health
        self.log("debug", "Health status: %s [%d]" % (status, error_code))
        if status == _HEALTH_STATUSES[2]:
            self.log(
                "warning",
                "Trying to reset sensor due to the error. "
                "Error code: %d" % (error_code),
            )
            self.reset()
            status, error_code = self.health
            if status == _HEALTH_STATUSES[2]:
                raise RPLidarException(
                    "RPLidar hardware failure. " "Error code: %d" % error_code
                )
        elif status == _HEALTH_STATUSES[1]:
            self.log(
                "warning",
                "Warning sensor status detected! " "Error code: %d" % (error_code),
            )
        cmd = SCAN_BYTE
        self._send_cmd(cmd)
        dsize, is_single, dtype = self._read_descriptor()
        if dsize != 5:
            raise RPLidarException("Wrong info reply length")
        if is_single:
            raise RPLidarException("Not a multiple response mode")
        if dtype != SCAN_TYPE:
            raise RPLidarException("Wrong response data type")
        while True:
            raw = self._read_response(dsize)
            self.log_bytes("debug", "Received scan response: ", raw)
            if max_buf_meas:
                data_in_buf = self._serial_port.in_waiting
                if data_in_buf > max_buf_meas * dsize:
                    self.log(
                        "warning",
                        "Too many measurements in the input buffer: %d/%d. "
                        "Clearing buffer..." % (data_in_buf // dsize, max_buf_meas),
                    )
                    self._serial_port.read(data_in_buf // dsize * dsize)
            yield _process_scan(raw)

    def iter_measurments(self, max_buf_meas=500):
        """For compatibility, this method wraps `iter_measurements`"""
        warnings.warn(
            "The method `iter_measurments` has been renamed "
            "`iter_measurements` to correct spelling",
            PendingDeprecationWarning,
        )
        self.iter_measurements(max_buf_meas=max_buf_meas)

    def iter_scans(self, max_buf_meas=500, min_len=5):
        """Iterate over scans. Note that consumer must be fast enough,
        otherwise data will be accumulated inside buffer and consumer will get
        data with increasing lag.

        Parameters

        max_buf_meas : int
            Maximum number of measurements to be stored inside the buffer. Once
            number exceeds this limit buffer will be emptied out.
        min_len : int
            Minimum number of measurements in the scan for it to be yielded.

        Yields

        scan : list
            List of the measurements. Each measurement is tuple with following
            format: (quality, angle, distance). For values description please
            refer to `iter_measurements` method's documentation.
        """
        scan = []
        iterator = self.iter_measurements(max_buf_meas)
        for new_scan, quality, angle, distance in iterator:
            if new_scan:
                if len(scan) > min_len:
                    yield scan
                scan = []
            if quality > 0 and distance > 0:
                scan.append((quality, angle, distance))
