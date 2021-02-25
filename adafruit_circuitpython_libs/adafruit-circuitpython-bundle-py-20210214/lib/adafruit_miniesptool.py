# SPDX-FileCopyrightText: 2018 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_miniesptool`
====================================================

ROM loader for ESP chips, works with ESP8266 or ESP32.
This is a 'no-stub' loader, so you can't read MD5 or firmware back on ESP8266.

See this document for protocol we're implementing:
https://github.com/espressif/esptool/wiki/Serial-Protocol

See this for the 'original' code we're miniaturizing:
https://github.com/espressif/esptool/blob/master/esptool.py

There's a very basic Arduino ROM loader here for ESP32:
https://github.com/arduino-libraries/WiFiNINA/tree/master/examples/Tools/FirmwareUpdater

* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases


"""

import os
import time
import struct
from digitalio import Direction

__version__ = "0.2.8"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_miniesptool.git"

SYNC_PACKET = b"\x07\x07\x12 UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU"
ESP32_DATAREGVALUE = 0x15122500
ESP8266_DATAREGVALUE = 0x00062000

# Commands supported by ESP8266 ROM bootloader
ESP_FLASH_BEGIN = 0x02
ESP_FLASH_DATA = 0x03
ESP_FLASH_END = 0x04
ESP_MEM_BEGIN = 0x05
ESP_MEM_END = 0x06
ESP_MEM_DATA = 0x07
ESP_SYNC = 0x08
ESP_WRITE_REG = 0x09
ESP_READ_REG = 0x0A
ESP_SPI_SET_PARAMS = 0x0B
ESP_SPI_ATTACH = 0x0D
ESP_CHANGE_BAUDRATE = 0x0F
ESP_SPI_FLASH_MD5 = 0x13
ESP_CHECKSUM_MAGIC = 0xEF

ESP8266 = 0x8266
ESP32 = 0x32

FLASH_SIZES = {
    "512KB": 0x00,
    "256KB": 0x10,
    "1MB": 0x20,
    "2MB": 0x30,
    "4MB": 0x40,
    "2MB-c1": 0x50,
    "4MB-c1": 0x60,
    "8MB": 0x80,
    "16MB": 0x90,
}


class miniesptool:  # pylint: disable=invalid-name
    """A miniature version of esptool, a programming command line tool for
    ESP8266 and ESP32 chips. This version is minimized to work on CircuitPython
    boards, so you can burn ESP firmware direct from the CPy disk drive. Handy
    when you have an ESP module wired to a board and need to upload new AT
    firmware. Its slow! Expect a few minutes when programming 1 MB flash."""

    FLASH_WRITE_SIZE = 0x200
    FLASH_SECTOR_SIZE = 0x1000  # Flash sector size, minimum unit of erase.
    ESP_ROM_BAUD = 115200

    def __init__(
        self,
        uart,
        gpio0_pin,  # pylint: disable=too-many-arguments
        reset_pin,
        *,
        flashsize,
        baudrate=ESP_ROM_BAUD
    ):
        gpio0_pin.direction = Direction.OUTPUT
        reset_pin.direction = Direction.OUTPUT
        self._gpio0pin = gpio0_pin
        self._resetpin = reset_pin
        self._uart = uart
        self._uart.baudrate = baudrate
        self._debug = False
        self._efuses = [0] * 4
        self._chipfamily = None
        self._chipname = None
        self._flashsize = flashsize
        # self._debug_led = DigitalInOut(board.D13)
        # self._debug_led.direction = Direction.OUTPUT

    @property
    def debug(self):
        """Print out all sent/received UART data plus some debugging output"""
        return self._debug

    @debug.setter
    def debug(self, flag):
        self._debug = flag

    @property
    def baudrate(self):
        """The baudrate of the UART connection. On ESP8266 we cannot change
        this once we've started syncing. On ESP32 we must start at 115200 and
        then manually change to higher speeds if desired"""
        return self._uart.baudrate

    @baudrate.setter
    def baudrate(self, baud):
        if self._chipfamily == ESP8266:
            raise NotImplementedError("Baud rate can only change on ESP32")
        buffer = struct.pack("<II", baud, 0)
        self.check_command(ESP_CHANGE_BAUDRATE, buffer)
        self._uart.baudrate = baud
        time.sleep(0.05)
        self._uart.reset_input_buffer()
        self.check_command(ESP_CHANGE_BAUDRATE, buffer)

    def md5(self, offset, size):
        """On ESP32 we can ask the ROM bootloader to calculate an MD5 on the
        SPI flash memory, from a location over a size in bytes. Returns a
        string with the MD5 in lowercase"""
        if self._chipfamily == ESP8266:
            raise NotImplementedError("MD5 only supported on ESP32")
        self.check_command(ESP_SPI_ATTACH, bytes([0] * 8))
        buffer = struct.pack("<IIII", offset, size, 0, 0)
        md5 = self.check_command(ESP_SPI_FLASH_MD5, buffer, timeout=2)[1]
        return "".join([chr(i) for i in md5])

    @property
    def mac_addr(self):
        """The MAC address burned into the OTP memory of the ESP chip"""
        mac_addr = [0] * 6
        mac0, mac1, mac2, mac3 = self._efuses
        if self._chipfamily == ESP8266:
            if mac3 != 0:
                oui = ((mac3 >> 16) & 0xFF, (mac3 >> 8) & 0xFF, mac3 & 0xFF)
            elif ((mac1 >> 16) & 0xFF) == 0:
                oui = (0x18, 0xFE, 0x34)
            elif ((mac1 >> 16) & 0xFF) == 1:
                oui = (0xAC, 0xD0, 0x74)
            else:
                raise RuntimeError("Couldnt determine OUI")

            mac_addr[0] = oui[0]
            mac_addr[1] = oui[1]
            mac_addr[2] = oui[2]
            mac_addr[3] = (mac1 >> 8) & 0xFF
            mac_addr[4] = mac1 & 0xFF
            mac_addr[5] = (mac0 >> 24) & 0xFF
        if self._chipfamily == ESP32:
            mac_addr[0] = mac2 >> 8 & 0xFF
            mac_addr[1] = mac2 & 0xFF
            mac_addr[2] = mac1 >> 24 & 0xFF
            mac_addr[3] = mac1 >> 16 & 0xFF
            mac_addr[4] = mac1 >> 8 & 0xFF
            mac_addr[5] = mac1 & 0xFF
        return mac_addr

    @property
    def chip_type(self):
        """ESP32 or ESP8266 based on which chip type we're talking to"""
        if not self._chipfamily:
            datareg = self.read_register(0x60000078)
            if datareg == ESP32_DATAREGVALUE:
                self._chipfamily = ESP32
            elif datareg == ESP8266_DATAREGVALUE:
                self._chipfamily = ESP8266
            else:
                raise RuntimeError("Unknown Chip")
        return self._chipfamily

    @property
    def chip_name(self):
        """The specific name of the chip, e.g. ESP8266EX, to the best
        of our ability to determine without a stub bootloader."""
        self.chip_type  # pylint: disable=pointless-statement
        self._read_efuses()

        if self.chip_type == ESP32:
            return "ESP32"
        if self.chip_type == ESP8266:
            if self._efuses[0] & (1 << 4) or self._efuses[2] & (1 << 16):
                return "ESP8285"
            return "ESP8266EX"
        return None

    def _read_efuses(self):
        """Read the OTP data for this chip and store into _efuses array"""
        if self._chipfamily == ESP8266:
            base_addr = 0x3FF00050
        elif self._chipfamily == ESP32:
            base_addr = 0x6001A000
        else:
            raise RuntimeError("Don't know what chip this is")
        for i in range(4):
            self._efuses[i] = self.read_register(base_addr + 4 * i)

    def get_erase_size(self, offset, size):
        """Calculate an erase size given a specific size in bytes.
        Provides a workaround for the bootloader erase bug on ESP8266."""

        sectors_per_block = 16
        sector_size = self.FLASH_SECTOR_SIZE
        num_sectors = (size + sector_size - 1) // sector_size
        start_sector = offset // sector_size

        head_sectors = sectors_per_block - (start_sector % sectors_per_block)
        if num_sectors < head_sectors:
            head_sectors = num_sectors

        if num_sectors < 2 * head_sectors:
            return (num_sectors + 1) // 2 * sector_size
        return (num_sectors - head_sectors) * sector_size

    def flash_begin(self, *, size=0, offset=0):
        """Prepare for flashing by attaching SPI chip and erasing the
        number of blocks requred."""
        if self._chipfamily == ESP32:
            self.check_command(ESP_SPI_ATTACH, bytes([0] * 8))
            # We are hardcoded for 4MB flash on ESP32
            buffer = struct.pack(
                "<IIIIII", 0, self._flashsize, 0x10000, 4096, 256, 0xFFFF
            )
            self.check_command(ESP_SPI_SET_PARAMS, buffer)

        num_blocks = (size + self.FLASH_WRITE_SIZE - 1) // self.FLASH_WRITE_SIZE
        if self._chipfamily == ESP8266:
            erase_size = self.get_erase_size(offset, size)
        else:
            erase_size = size
        timeout = 13
        stamp = time.monotonic()
        buffer = struct.pack(
            "<IIII", erase_size, num_blocks, self.FLASH_WRITE_SIZE, offset
        )
        print(
            "Erase size %d, num_blocks %d, size %d, offset 0x%04x"
            % (erase_size, num_blocks, self.FLASH_WRITE_SIZE, offset)
        )

        self.check_command(ESP_FLASH_BEGIN, buffer, timeout=timeout)
        if size != 0:
            print(
                "Took %.2fs to erase %d flash blocks"
                % (time.monotonic() - stamp, num_blocks)
            )
        return num_blocks

    def check_command(
        self, opcode, buffer, checksum=0, timeout=0.1
    ):  # pylint: disable=unused-argument
        """Send a command packet, check that the command succeeded and
        return a tuple with the value and data.
        See the ESP Serial Protocol for more details on what value/data are"""
        self.send_command(opcode, buffer)
        value, data = self.get_response(opcode, timeout)
        if self._chipfamily == ESP8266:
            status_len = 2
        elif self._chipfamily == ESP32:
            status_len = 4
        else:
            if len(data) in (2, 4):
                status_len = len(data)
        if data is None or len(data) < status_len:
            raise RuntimeError("Didn't get enough status bytes")
        status = data[-status_len:]
        data = data[:-status_len]
        # print("status", status)
        # print("value", value)
        # print("data", data)
        if status[0] != 0:
            raise RuntimeError("Command failure error code 0x%02x" % status[1])
        return (value, data)

    def send_command(self, opcode, buffer):
        """Send a slip-encoded, checksummed command over the UART,
        does not check response"""
        self._uart.reset_input_buffer()

        # self._debug_led.value = True
        checksum = 0
        if opcode == 0x03:
            checksum = self.checksum(buffer[16:])
        # self._debug_led.value = False

        packet = [0xC0, 0x00]  # direction
        packet.append(opcode)
        packet.extend(struct.pack("H", len(buffer)))
        packet.extend(self.slip_encode(struct.pack("I", checksum)))
        packet.extend(self.slip_encode(buffer))
        packet += [0xC0]
        if self._debug:
            print([hex(x) for x in packet])
            print("Writing:", bytearray(packet))
        self._uart.write(bytearray(packet))

    def get_response(self, opcode, timeout=0.1):  # pylint: disable=too-many-branches
        """Read response data and decodes the slip packet, then parses
        out the value/data and returns as a tuple of (value, data) where
        each is a list of bytes"""
        reply = []

        stamp = time.monotonic()
        packet_length = 0
        escaped_byte = False
        while (time.monotonic() - stamp) < timeout:
            if self._uart.in_waiting > 0:
                c = self._uart.read(1)  # pylint: disable=invalid-name
                if c == b"\xDB":
                    escaped_byte = True
                elif escaped_byte:
                    if c == b"\xDD":
                        reply += b"\xDB"
                    elif c == b"\xDC":
                        reply += b"\xC0"
                    else:
                        reply += [0xDB, c]
                    escaped_byte = False
                else:
                    reply += c
            if reply and reply[0] != 0xC0:
                # packets must start with 0xC0
                del reply[0]
            if len(reply) > 1 and reply[1] != 0x01:
                del reply[0]
            if len(reply) > 2 and reply[2] != opcode:
                del reply[0]
            if len(reply) > 4:
                # get the length
                packet_length = reply[3] + (reply[4] << 8)
            if len(reply) == packet_length + 10:
                break
        # Check to see if we have a complete packet. If not, we timed out.
        if len(reply) != packet_length + 10:
            if self._debug:
                print("Timed out after {} seconds".format(timeout))
            return (None, None)
        if self._debug:
            print("Packet:", [hex(i) for i in reply])
            print("Reading:", bytearray(reply))
        value = reply[5:9]
        data = reply[9:-1]
        if self._debug:
            print("value:", [hex(i) for i in value], "data:", [hex(i) for i in data])
        return (value, data)

    def read_register(self, reg):
        """Read a register within the ESP chip RAM, returns a 4-element list"""
        if self._debug:
            print("Reading register 0x%08x" % reg)
        packet = struct.pack("I", reg)
        register = self.check_command(ESP_READ_REG, packet)[0]
        return struct.unpack("I", bytearray(register))[0]

    def reset(self, program_mode=False):
        """Perform a hard-reset into ROM bootloader using gpio0 and reset"""
        print("Resetting")
        self._gpio0pin.value = not program_mode
        self._resetpin.value = False
        time.sleep(0.1)
        self._resetpin.value = True
        time.sleep(1.0)

    def flash_block(self, data, seq, timeout=0.1):
        """Send one block of data to program into SPI Flash memory"""
        self.check_command(
            ESP_FLASH_DATA,
            struct.pack("<IIII", len(data), seq, 0, 0) + data,
            self.checksum(data),
            timeout=timeout,
        )

    def flash_file(self, filename, offset=0, md5=None):
        """Program a full, uncompressed binary file into SPI Flash at
        a given offset. If an ESP32 and md5 string is passed in, will also
        verify memory. ESP8266 does not have checksum memory verification in
        ROM"""
        filesize = os.stat(filename)[6]
        with open(filename, "rb") as file:
            print("\nWriting", filename, "w/filesize:", filesize)
            blocks = self.flash_begin(size=filesize, offset=offset)
            seq = 0
            written = 0
            address = offset
            stamp = time.monotonic()
            while filesize - file.tell() > 0:
                print(
                    "\rWriting at 0x%08x... (%d %%)"
                    % (
                        address + seq * self.FLASH_WRITE_SIZE,
                        100 * (seq + 1) // blocks,
                    ),
                    end="",
                )
                block = file.read(self.FLASH_WRITE_SIZE)
                # Pad the last block
                block = block + b"\xff" * (self.FLASH_WRITE_SIZE - len(block))
                # print(block)
                self.flash_block(block, seq, timeout=2)
                seq += 1
                written += len(block)
            print("Took %.2fs to write %d bytes" % (time.monotonic() - stamp, filesize))
            if md5:
                print("Verifying MD5sum ", md5)
                calcd = self.md5(offset, filesize)
                if md5 != calcd:
                    raise RuntimeError("MD5 mismatch, calculated:", calcd)

    def _sync(self):
        """Perform a soft-sync using AT sync packets, does not perform
        any hardware resetting"""
        self.send_command(0x08, SYNC_PACKET)
        for _ in range(8):
            reply, data = self.get_response(  # pylint: disable=unused-variable
                0x08, 0.1
            )
            if not data:
                continue
            if len(data) > 1 and data[0] == 0 and data[1] == 0:
                return True
        return False

    def sync(self):
        """Put into ROM bootload mode & attempt to synchronize with the
        ESP ROM bootloader, we will retry a few times"""
        self.reset(True)

        for _ in range(5):
            if self._sync():
                time.sleep(0.1)
                return True
            time.sleep(0.1)

        raise RuntimeError("Couldn't sync to ESP")

    @staticmethod
    def checksum(data, state=ESP_CHECKSUM_MAGIC):
        """ Calculate checksum of a blob, as it is defined by the ROM """
        for b in data:
            state ^= b
        return state

    @staticmethod
    def slip_encode(buffer):
        """Take a bytearray buffer and return back a new bytearray where
        0xdb is replaced with 0xdb 0xdd and 0xc0 is replaced with 0xdb 0xdc"""
        encoded = []
        for b in buffer:
            if b == 0xDB:
                encoded += [0xDB, 0xDD]
            elif b == 0xC0:
                encoded += [0xDB, 0xDC]
            else:
                encoded += [b]
        return bytearray(encoded)
