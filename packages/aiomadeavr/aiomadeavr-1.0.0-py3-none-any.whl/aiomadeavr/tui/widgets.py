#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Textual widgets for aiomadeavr TUI
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
"""Custom widgets for AVR TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import (
    Button,
    Label,
    ListItem,
    ListView,
    Select,
    Static,
)

from ..avr import MDAVR


class DeviceListWidget(Static):
    """Widget for displaying discovered devices."""

    class DeviceSelected(Message):
        """Message sent when a device is selected."""

        def __init__(self, serial: str) -> None:
            self.serial = serial
            super().__init__()

    def compose(self) -> ComposeResult:
        yield ListView(id="device-listview")

    def clear(self) -> None:
        """Clear all devices from the list."""
        listview = self.query_one("#device-listview", ListView)
        listview.clear()

    def add_device(self, serial: str, name: str) -> None:
        """Add a device to the list."""
        listview = self.query_one("#device-listview", ListView)
        item = ListItem(Label(name), id=f"device-{serial}")
        listview.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle device selection."""
        item_id = event.item.id
        self.log(f"ListView selected: item_id={item_id}")
        if item_id and item_id.startswith("device-"):
            serial = item_id[7:]  # Remove "device-" prefix
            self.log(f"Posting DeviceSelected for serial={serial}")
            self.post_message(self.DeviceSelected(serial))


class DeviceStatusPanel(Static):
    """Widget for displaying device-level status (power + eco)."""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="panel"):
            yield Button("⏻", id="power-btn", variant="default")
            yield Label(" Device Power ", id="device-power-status")
            yield Label(" | Eco: ")
            yield Label("-", id="status-eco")

    def update_status(self, device: MDAVR) -> None:
        """Update status display from device."""
        power_on = str(device.power) == "On"

        power_btn = self.query_one("#power-btn", Button)
        power_btn.variant = "primary" if power_on else "warning"

        self.query_one("#device-power-status", Label).update(
            " On " if power_on else " Off "
        )
        self.query_one("#status-eco", Label).update(str(device.eco_mode))


class MainZoneControl(Static):
    """Widget for main zone control (power, volume, source, sound mode)."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="zone-panel"):
            # Power row
            with Horizontal(classes="control-row"):
                yield Button("⏻", id="main-power-btn", variant="default")
                yield Label(" Main Zone ", id="main-power-status")

            # Volume row
            with Horizontal(classes="control-row"):
                yield Label("🔊 Vol: ")
                yield Label("--", id="main-volume-display")
                yield Button("−", id="btn-main-vol-down", variant="default")
                yield Button("🔇", id="btn-main-mute", variant="warning")
                yield Button("+", id="btn-main-vol-up", variant="default")

            # Source row
            with Horizontal(classes="control-row"):
                yield Label("Source: ")
                yield Select([], id="main-source-select", prompt="Select source...")

            # Sound mode row (main zone only)
            with Horizontal(classes="control-row"):
                yield Label("Mode: ")
                yield Select([], id="main-sound-mode-select", prompt="Select mode...")

    def update_zone(self, device: MDAVR) -> None:
        """Update main zone display from device."""
        # Power
        power_on = str(device.zmain) == "On"
        power_btn = self.query_one("#main-power-btn", Button)
        power_btn.variant = "primary" if power_on else "warning"
        self.query_one("#main-power-status", Label).update(
            " On " if power_on else " Off "
        )

        # Volume
        volume = device.volume
        muted = device.muted is True

        vol_display = self.query_one("#main-volume-display", Label)

        if isinstance(volume, (int, float)):
            display = f"{volume:.1f} dB"
            if muted:
                display += " 🔇"
            vol_display.update(display)
        else:
            vol_display.update(str(volume))

        # Mute button style
        mute_btn = self.query_one("#btn-main-mute", Button)
        mute_btn.variant = "error" if muted else "warning"

        # Source
        source_list = device.source_list
        current_source = device.source
        source_select = self.query_one("#main-source-select", Select)

        if source_list:
            options = [(src, src) for src in sorted(source_list)]
            source_select.set_options(options)
            if (
                current_source
                and current_source != "-"
                and current_source in source_list
            ):
                source_select.value = current_source

        # Sound mode
        mode_list = device.sound_mode_list
        current_mode = device.sound_mode
        mode_select = self.query_one("#main-sound-mode-select", Select)

        if mode_list:
            options = [(mode, mode) for mode in sorted(mode_list)]
            mode_select.set_options(options)
            if current_mode and current_mode != "-" and current_mode in mode_list:
                mode_select.value = current_mode


class ZoneControl(Static):
    """Widget for zone control (Zone 2 or Zone 3)."""

    def __init__(self, zone: int = 2, **kwargs):
        super().__init__(**kwargs)
        self.zone = zone
        self.prefix = f"z{zone}"

    def compose(self) -> ComposeResult:
        with Vertical(classes="zone-panel"):
            # Power row
            with Horizontal(classes="control-row"):
                yield Button("⏻", id=f"btn-{self.prefix}-power", variant="default")
                yield Label(f" Zone {self.zone} ", id=f"{self.prefix}-power-status")

            # Volume row
            with Horizontal(classes="control-row"):
                yield Label("🔊 Vol: ")
                yield Label("--", id=f"{self.prefix}-volume-display")
                yield Button("−", id=f"btn-{self.prefix}-vol-down", variant="default")
                yield Button("🔇", id=f"btn-{self.prefix}-mute", variant="default")
                yield Button("+", id=f"btn-{self.prefix}-vol-up", variant="default")

            # Source row
            with Horizontal(classes="control-row"):
                yield Label("Source: ")
                yield Select([], id=f"{self.prefix}-source-select", prompt="Select...")

    def update_zone(self, device: MDAVR) -> None:
        """Update zone display from device."""
        if self.zone == 2:
            power = device.z2
            volume = device.z2_volume
            muted = device.z2_muted is True
            source = device.z2_source
        else:
            power = device.z3
            volume = device.z3_volume
            muted = device.z3_muted is True
            source = device.z3_source

        # Power
        power_on = str(power) == "On"
        power_btn = self.query_one(f"#btn-{self.prefix}-power", Button)
        power_btn.variant = "primary" if power_on else "warning"
        self.query_one(f"#{self.prefix}-power-status", Label).update(
            " On " if power_on else " Off "
        )

        # Volume
        vol_display = self.query_one(f"#{self.prefix}-volume-display", Label)
        if isinstance(volume, (int, float)):
            display = f"{volume:.1f}"
            if muted:
                display += " 🔇"
            vol_display.update(display)
        else:
            vol_display.update(str(volume))

        # Mute button style
        mute_btn = self.query_one(f"#btn-{self.prefix}-mute", Button)
        mute_btn.variant = "error" if muted else "default"

        # Source
        source_list = device.source_list
        select = self.query_one(f"#{self.prefix}-source-select", Select)

        if source_list:
            options = [(src, src) for src in sorted(source_list)]
            select.set_options(options)
            if source and source != "-" and source in source_list:
                select.value = source
