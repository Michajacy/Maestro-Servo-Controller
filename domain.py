"""
Domain logic module for Servo management.
Contains models and managers for application state.
"""
from typing import Optional
import json
import os


class Servo:
    """Represents an individual servo's state and configuration."""
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(self, channel: int, name: str, initial_position: int = 1500,
                 step: int = 50, min_val: int = 1000, max_val: int = 2000) -> None:
        self.channel = channel
        self.name = name
        self.position = initial_position
        self.step = step
        self.min_val = min_val
        self.max_val = max_val


class ServoManager:
    """Assigns channels, stores configurations, and communicates with hardware."""
    def __init__(self, hardware_interface, max_channels: int = 24) -> None:
        self.hw = hardware_interface
        self.max_channels = max_channels
        self.servos = {}
        self.config_file = "servos_config.json"

        self._load_config()

    def _save_config(self) -> None:
        """Saves current servos state to a JSON file."""
        data = {}
        for ch_id, servo in self.servos.items():
            data[ch_id] = {
                "name": servo.name,
                "position": servo.position,
                "step": servo.step,
                "min_val": servo.min_val,
                "max_val": servo.max_val
            }

        # Added encoding='utf-8' to satisfy Pylint W1514
        with open(self.config_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def _load_config(self) -> None:
        """Loads servos state from a JSON file if it exists."""
        if not os.path.exists(self.config_file):
            return

        # Added encoding='utf-8' to satisfy Pylint W1514
        with open(self.config_file, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                for ch_str, servo_data in data.items():
                    ch_id = int(ch_str)
                    name = servo_data.get("name", f"Servo {ch_id}")
                    pos = servo_data.get("position", 1500)
                    step = servo_data.get("step", 50)
                    min_val = servo_data.get("min_val", 1000)
                    max_val = servo_data.get("max_val", 2000)

                    new_servo = Servo(ch_id, name, pos, step, min_val, max_val)
                    self.servos[ch_id] = new_servo

            except (json.JSONDecodeError, ValueError):
                pass  # ignore errors caused by a damaged file

    def add_servo(self, name: str) -> Optional['Servo']:
        """
        Finds the first free channel and adds a new servo.
        Returns None when no channel is free.
        """
        for ch_id in range(self.max_channels):
            if ch_id not in self.servos:
                new_servo = Servo(channel=ch_id, name=name)
                self.servos[ch_id] = new_servo

                # Set starting position
                self.hw.set_target(ch_id, new_servo.position)
                self._save_config()
                return new_servo

        return None

    def remove_servo(self, channel: int) -> None:
        """Removes a servo from the manager and halts its pulses."""
        if channel in self.servos:
            self.hw.set_target(channel, 0)
            del self.servos[channel]
            self._save_config()

    def set_servo_position(self, channel: int, position: int) -> None:
        """Updates a servo's position and sends it to the device."""
        if channel in self.servos:
            self.servos[channel].position = position
            self.hw.set_target(channel, position)
            self._save_config()
