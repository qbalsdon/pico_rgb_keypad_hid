# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint:disable=undefined-variable,wildcard-import,no-name-in-module
# pylint:disable=no-member

import adafruit_logging as logging

logger = logging.getLogger("test")

logger.setLevel(logging.ERROR)
logger.info("Info message")
logger.error("Error message")
