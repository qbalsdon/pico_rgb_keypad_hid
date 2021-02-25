# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Verifies which board is being used and imports the appropriate module.
"""

import os

if "CLUE" in os.uname().machine:
    from .clue import clue as pybadger
elif "Pybadge" in os.uname().machine:
    from .pybadge import pybadge as pybadger
elif "PyGamer" in os.uname().machine:
    from .pygamer import pygamer as pybadger
elif "PewPew M4" in os.uname().machine:
    from .pewpewm4 import pewpewm4 as pybadger
elif "PyPortal" in os.uname().machine:
    from .pyportal import pyportal as pybadger
elif "Circuit Playground Bluefruit" in os.uname().machine:
    from .cpb_gizmo import cpb_gizmo as pybadger
elif "MagTag with ESP32S2" in os.uname().machine:
    from .mag_tag import mag_tag as pybadger
