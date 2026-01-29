#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Textual TUI application for aiomadeavr
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
"""Main Textual application for AVR control."""

import asyncio
import logging
from typing import Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    RichLog,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from .. import avr_factory, start_discovery
from ..avr import MDAVR
from .widgets import (
    DeviceListWidget,
    DeviceStatusPanel,
    MainZoneControl,
    ZoneControl,
)


class AVRControlApp(App):
    """Main Textual application for controlling Marantz/Denon AVRs."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #main-container {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 3fr;
        height: 1fr;
    }

    #sidebar {
        width: 100%;
        height: 100%;
        border: solid $primary;
        padding: 0 1;
    }

    #main-content {
        width: 100%;
        height: 100%;
        padding: 0 1;
    }

    #device-list {
        height: auto;
    }

    #device-listview {
        height: auto;
        max-height: 10;
    }

    #log-panel {
        height: 1fr;
        border: solid $secondary;
        background: $surface;
    }

    .panel {
        border: solid $secondary;
        padding: 0 1;
        margin: 0;
        height: auto;
    }

    .panel Horizontal {
        height: 3;
    }

    .panel Label {
        height: 3;
        content-align: center middle;
    }

    .panel-title {
        text-style: bold;
        color: $text;
    }

    .zone-panel {
        padding: 1;
        height: auto;
    }

    .control-row {
        height: 3;
    }

    .control-row Label {
        height: 3;
        content-align: center middle;
    }

    DeviceStatusPanel {
        height: auto;
    }

    MainZoneControl {
        height: auto;
    }

    ZoneControl {
        height: auto;
    }

    #zone-tabs {
        height: 1fr;
    }

    Select {
        height: 3;
        width: 1fr;
    }

    #no-device {
        text-align: center;
        margin: 1;
        color: $text-muted;
    }

    Button {
        margin: 0;
        min-width: 4;
        height: 3;
    }

    #main-volume-display, #z2-volume-display, #z3-volume-display {
        width: 15;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "discover", "Discover"),
        Binding("m", "toggle_mute", "Mute"),
        Binding("+", "volume_up", "Vol+"),
        Binding("-", "volume_down", "Vol-"),
    ]

    def __init__(self, ip: Optional[str] = None, debug: bool = False):
        super().__init__()
        self.devices: dict[str, MDAVR] = {}
        self.current_device: Optional[MDAVR] = None
        self.initial_ip = ip
        self.debug_mode = debug

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="sidebar"):
                yield Label("Devices", classes="panel-title")
                yield DeviceListWidget(id="device-list")
                yield Button("Discover", id="btn-discover", variant="primary")
                if self.debug_mode:
                    yield Label("Log", classes="panel-title")
                    yield RichLog(id="log-panel", highlight=True, markup=True)
            with ScrollableContainer(id="main-content"):
                yield Static("No device selected", id="no-device")
                yield DeviceStatusPanel(id="device-status")
                with TabbedContent(id="zone-tabs"):
                    with TabPane("Main", id="main-tab"):
                        yield MainZoneControl(id="main-zone-control")
                    with TabPane("Zone 2", id="zone2-tab"):
                        yield ZoneControl(zone=2, id="zone2-control")
                    with TabPane("Zone 3", id="zone3-tab"):
                        yield ZoneControl(zone=3, id="zone3-control")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        # Hide controls until device is selected
        self._hide_controls()

        if self.initial_ip:
            self.connect_to_ip(self.initial_ip)
        else:
            self.start_discovery()

    def _hide_controls(self) -> None:
        """Hide all control panels."""
        self.query_one("#device-status").display = False
        self.query_one("#zone-tabs").display = False
        self.query_one("#no-device").display = True

    def _show_controls(self) -> None:
        """Show all control panels."""
        self.query_one("#device-status").display = True
        self.query_one("#zone-tabs").display = True
        self.query_one("#no-device").display = False

    @work(exclusive=True)
    async def start_discovery(self) -> None:
        """Start device discovery."""
        device_list = self.query_one("#device-list", DeviceListWidget)
        device_list.clear()

        # Queue to receive discovered devices
        queue: asyncio.Queue = asyncio.Queue()

        def on_discovered(info: dict) -> None:
            queue.put_nowait(info)

        await start_discovery(callb=on_discovered)

        # Process discovered devices as they come in
        async def process_queue():
            while True:
                try:
                    info = await asyncio.wait_for(queue.get(), timeout=0.5)
                    self._add_discovered_device(info)
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break

        process_task = asyncio.create_task(process_queue())
        await asyncio.sleep(6)  # Wait for discovery timeout
        process_task.cancel()
        try:
            await process_task
        except asyncio.CancelledError:
            pass

        # Process any remaining items in queue
        while not queue.empty():
            info = queue.get_nowait()
            self._add_discovered_device(info)

    def _add_discovered_device(self, info: dict) -> None:
        """Add a discovered device to the list."""
        serial = info.get("serial", "").lower()
        if serial and serial not in self.devices:
            self.connect_device(info)

    @work(exclusive=False)
    async def connect_device(self, info: dict) -> None:
        """Connect to a discovered device."""
        try:
            device = await avr_factory(info["name"], info["ip"])
            if device:
                serial = info.get("serial", info["ip"]).lower()
                self.devices[serial] = device
                device.notifyme(self._on_device_notification)
                if self.debug_mode:
                    device.set_log_callback(
                        lambda msg: self.call_later(self._log_message, msg)
                    )

                # Now request initial status - notifications will work
                device.refresh()

                # Wait for responses to arrive
                await asyncio.sleep(2.0)

                device_list = self.query_one("#device-list", DeviceListWidget)
                device_list.add_device(serial, info["name"])

                # Auto-select if first device - schedule on main thread
                if len(self.devices) == 1:
                    self.call_later(self._select_device, serial)
        except Exception as e:
            logging.error(f"Failed to connect to {info['ip']}: {e}")

    def connect_to_ip(self, ip: str) -> None:
        """Connect directly to an IP address."""
        info = {"name": f"AVR@{ip}", "ip": ip, "serial": ip.replace(".", "")}
        self.connect_device(info)

    def _log_message(self, msg: str) -> None:
        """Write a message to the log panel (only in debug mode)."""
        if not self.debug_mode:
            return
        try:
            log_panel = self.query_one("#log-panel", RichLog)
            log_panel.write(msg)
        except Exception:
            pass  # Panel might not exist yet

    def _on_device_notification(self, label: str, value) -> None:
        """Called when device state changes."""
        if self.debug_mode:
            self._log_message(f"[green]NOTIFY:[/] {label} = {value}")
        # Schedule UI update - use call_later since we're in the same event loop
        self.call_later(self._update_ui)

    def _update_ui(self) -> None:
        """Update UI with current device state."""
        if not self.current_device:
            return

        device_status = self.query_one("#device-status", DeviceStatusPanel)
        device_status.update_status(self.current_device)

        main_zone = self.query_one("#main-zone-control", MainZoneControl)
        main_zone.update_zone(self.current_device)

        zone2 = self.query_one("#zone2-control", ZoneControl)
        zone2.update_zone(self.current_device)

        zone3 = self.query_one("#zone3-control", ZoneControl)
        zone3.update_zone(self.current_device)

    def _select_device(self, serial: str) -> None:
        """Select a device for control."""
        self.log(
            f"_select_device called: serial={serial}, devices={list(self.devices.keys())}"
        )
        if serial in self.devices:
            self.log(f"Device found, selecting...")
            self.current_device = self.devices[serial]
            self._show_controls()
            self._update_ui()
            # Schedule additional UI updates to catch late-arriving responses
            self.set_timer(0.5, self._update_ui)
            self.set_timer(1.0, self._update_ui)
            self.set_timer(2.0, self._update_ui)
        else:
            self.log(f"Device NOT found in devices dict!")

    def on_device_list_widget_device_selected(
        self, event: DeviceListWidget.DeviceSelected
    ) -> None:
        """Handle device selection from list."""
        self.log(f"on_device_list_widget_device_selected: serial={event.serial}")
        self._select_device(event.serial)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-discover":
            self.start_discovery()
        # Device power button
        elif button_id == "power-btn" and self.current_device:
            if str(self.current_device.power) == "On":
                self.current_device.turn_off()
            else:
                self.current_device.turn_on()
        # Main zone buttons
        elif button_id == "main-power-btn" and self.current_device:
            if str(self.current_device.zmain) == "On":
                self.current_device.main_turn_off()
            else:
                self.current_device.main_turn_on()
        elif button_id == "btn-main-mute" and self.current_device:
            self.current_device.mute_volume(self.current_device.muted is not True)
        elif button_id == "btn-main-vol-up" and self.current_device:
            self.current_device.volume_up()
        elif button_id == "btn-main-vol-down" and self.current_device:
            self.current_device.volume_down()
        # Zone 2 buttons
        elif button_id == "btn-z2-power" and self.current_device:
            if str(self.current_device.z2) == "On":
                self.current_device.z2_turn_off()
            else:
                self.current_device.z2_turn_on()
        elif button_id == "btn-z2-mute" and self.current_device:
            self.current_device.z2_mute_volume(self.current_device.z2_muted is not True)
        elif button_id == "btn-z2-vol-up" and self.current_device:
            self.current_device.z2_volume_up()
        elif button_id == "btn-z2-vol-down" and self.current_device:
            self.current_device.z2_volume_down()
        # Zone 3 buttons
        elif button_id == "btn-z3-power" and self.current_device:
            if str(self.current_device.z3) == "On":
                self.current_device.z3_turn_off()
            else:
                self.current_device.z3_turn_on()
        elif button_id == "btn-z3-mute" and self.current_device:
            self.current_device.z3_mute_volume(self.current_device.z3_muted is not True)
        elif button_id == "btn-z3-vol-up" and self.current_device:
            self.current_device.z3_volume_up()
        elif button_id == "btn-z3-vol-down" and self.current_device:
            self.current_device.z3_volume_down()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select widget changes."""
        if not self.current_device:
            return

        select_id = event.select.id
        value = str(event.value)

        if select_id == "main-source-select":
            self.current_device.select_source(value)
        elif select_id == "main-sound-mode-select":
            self.current_device.select_sound_mode(value)
        elif select_id == "z2-source-select":
            self.current_device.z2_select_source(value)
        elif select_id == "z3-source-select":
            self.current_device.z3_select_source(value)

    def action_quit(self) -> None:
        """Quit the application."""
        for device in self.devices.values():
            device.close()
        self.exit()

    def action_refresh(self) -> None:
        """Refresh current device state."""
        if self.current_device:
            self.current_device.refresh()
            # Schedule UI updates to catch responses
            self.set_timer(0.5, self._update_ui)
            self.set_timer(1.0, self._update_ui)

    def action_discover(self) -> None:
        """Start device discovery."""
        self.start_discovery()

    def action_toggle_mute(self) -> None:
        """Toggle mute on current device."""
        if self.current_device:
            self.current_device.mute_volume(not self.current_device.muted)

    def action_volume_up(self) -> None:
        """Increase volume on current device."""
        if self.current_device:
            self.current_device.volume_up()

    def action_volume_down(self) -> None:
        """Decrease volume on current device."""
        if self.current_device:
            self.current_device.volume_down()


def run_tui(ip: Optional[str] = None, debug: bool = False) -> None:
    """Run the Textual TUI.

    Args:
        ip: Optional IP address for direct connection
        debug: Enable debug logging and log panel
    """
    app = AVRControlApp(ip=ip, debug=debug)
    app.run()
