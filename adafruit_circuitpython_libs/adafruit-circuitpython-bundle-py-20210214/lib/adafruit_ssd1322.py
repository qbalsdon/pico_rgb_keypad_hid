# SPDX-FileCopyrightText: 2019 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ssd1322`
================================================================================

DisplayIO driver for grayscale OLEDs driven by SSD1322


* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

* 3.12" Newhaven Display 256x64 Grayscale Blue OLED:
    https://www.newhavendisplay.com/nhd31225664ucb2-p-3622.html

**Software and Dependencies:**

* Adafruit CircuitPython 5+ firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import displayio

__version__ = "1.1.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SSD1322.git"

_INIT_SEQUENCE = (
    b"\xfd\x01\x12"  # Set_Command_Lock(0x12);// Unlock Basic Commands (0x12/0x16)
    b"\xae\x00"  # Set_Display_On_Off(0x00);// Display Off (0x00/0x01)
    b"\xb3\x01\x91"  # Set_Display_Clock(0x91);// Set Clock as 80 Frames/Sec
    b"\xca\x01\x3f"  # Set_Multiplex_Ratio(0x3F);// 1/64 Duty (0x0F~0x3F)
    b"\xa2\x01\x00"  # Set_Display_Offset(0x00);// Shift Mapping RAM Counter (0x00~0x3F)
    b"\xa1\x01\x00"  # Set_Start_Line(0x00);// Set Mapping RAM Display Start Line (0x00~0x7F)
    b"\xa0\x02\x14\x11"  # Set_Remap_Format(0x14);// Set Horizontal Address Increment
    # //     Column Address 0 Mapped to SEG0
    # //     Disable Nibble Remap
    # //     Scan from COM[N-1] to COM0
    # //     Disable COM Split Odd Even
    # //     Enable Dual COM Line Mode
    b"\xb5\x01\x00"  # Set_GPIO(0x00);// Disable GPIO Pins Input
    b"\xab\x01\x01"  # Set_Function_Selection(0x01);// Enable Internal VDD Regulator
    b"\xb4\x02\xa0\xfd"  # Set_Display_Enhancement_A(0xA0,0xFD);// Enable External VSL
    b"\xc1\x01\x9f"  # Set_Contrast_Current(0x9F); // Set Segment Output Current
    b"\xc7\x01\x0f"  # Set_Master_Current(0x0F);//Set Scale Factor of Segment Output Current Control
    b"\xb8\x0f\x00\x01\x02\x03\x04\x05\x06\x07\x08\x10\x40\x90\xa0\xb0\xb4"  # Set graytable
    # b"\xb9\x00" # Set_Linear_Gray_Scale_Table();//set default linear gray scale table
    b"\xb1\x01\xe2"  # Set_Phase_Length(0xE2);// Set Phase 1 as 5 Clocks & Phase 2 as 14 Clocks
    # Set_Display_Enhancement_B(0x20);// Enhance Driving Scheme Capability (0x00/0x20)
    b"\xd1\x02\xa2\x20"
    b"\xbb\x01\x1f"  # Set_Precharge_Voltage(0x1F);// Set Pre-Charge Voltage Level as 0.60*VCC
    b"\xb6\x01\x08"  # Set_Precharge_Period(0x08);// Set Second Pre-Charge Period as 8 Clocks
    b"\xbe\x01\x07"  # Set_VCOMH(0x07);// Set Common Pins Deselect Voltage Level as 0.86*VCC
    b"\xa6\x00"  # Set_Display_Mode(0x02);// Normal Display Mode (0x00/0x01/0x02/0x03)
    b"\xa9\x00"  # Set_Partial_Display(0x01,0x00,0x00);// Disable Partial Display
    b"\xaf\x00"  # Set_Display_On_Off(0x01);
)

# pylint: disable=too-few-public-methods
class SSD1322(displayio.Display):
    """SSD1322 driver"""

    def __init__(self, bus, **kwargs):
        # Patch the init sequence for 32 pixel high displays.
        init_sequence = bytearray(_INIT_SEQUENCE)
        height = kwargs["height"]
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 0:
            height = kwargs["width"]
        init_sequence[10] = height - 1  # patch mux ratio
        super().__init__(
            bus,
            _INIT_SEQUENCE,
            **kwargs,
            color_depth=4,
            grayscale=True,
            set_column_command=0x15,
            set_row_command=0x75,
            set_vertical_scroll=0xD3,
            write_ram_command=0x5C,
            single_byte_bounds=True,
            reverse_pixels_in_byte=True,
            bytes_per_cell=2,
        )
