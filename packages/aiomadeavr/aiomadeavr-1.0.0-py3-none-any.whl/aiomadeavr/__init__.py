#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Exposed API for aiomadeavr
#
# Copyright (c) 2020 François Wautier
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
# IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
"""
aiomadeavr - Async library to control Marantz/Denon AVR devices.

Example usage:
    import asyncio
    from aiomadeavr import avr_factory

    async def main():
        avr = await avr_factory("Living Room", "192.168.1.100")
        if avr:
            async with avr:
                avr.turn_on()
                await asyncio.sleep(2)
                avr.set_volume(35)

    asyncio.run(main())
"""

from .avr import MDAVR, avr_factory, AvrError, AvrTimeoutError
from .discovery import start_discovery

__version__ = "1.0.0"
__all__ = [
    "MDAVR",
    "avr_factory",
    "AvrError",
    "AvrTimeoutError",
    "start_discovery",
]
