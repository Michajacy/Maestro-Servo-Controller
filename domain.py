"""
Domain logic module for Servo management.
Contains models and managers for application state.
"""
from typing import Optional
import json
import os
import config


class Servo:
    """Represents an individual servo's state and configuration."""
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(self, channel: int, name: str, initial_position: int = config.SERVO_DEF_POS,
                 step: int = config.SERVO_DEF_STEP, min_val: int = config.SERVO_DEF_MIN,
                 max_val: int = config.SERVO_DEF_MAX) -> None:
        self.channel = channel
        self.name = name
        self.position = initial_position
        self.step = step
        self.min_val = min_val
        self.max_val = max_val

class ServoManager:
    """Assigns channels, stores configurations, and communicates with hardware."""
    def __init__(self, hardware_interface, max_channels: int = config.MAX_CHANNELS,
                 hw_mode: str = config.DEFAULT_HW_MODE) -> None:
        self.hw = hardware_interface
        self.max_channels = max_channels
        self.servos = {}
        self.config_file = "servos_config.json"
        self.hw_mode = hw_mode

        self._load_config()

    def set_hardware(self, hardware_interface, hw_mode: str) -> None:
        """Dynamically swaps the hardware interface (e.g. from Mock to Serial)."""
        if self.hw:
            self.hw.close()
        self.hw = hardware_interface
        self.hw_mode = hw_mode
        self._save_config()

    def _save_config(self) -> None:
        """Saves current servos state to a JSON file."""
        data = {
            "settings": {
                "hw_mode": self.hw_mode
            },
            "servos": {}
        }
        for ch_id, servo in self.servos.items():
            data["servos"][ch_id] = {
                "name": servo.name,
                "position": servo.position,
                "step": servo.step,
                "min_val": servo.min_val,
                "max_val": servo.max_val
            }

        with open(self.config_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def _load_config(self) -> None:
        """Loads servos state from a JSON file if it exists."""
        if not os.path.exists(self.config_file):
            return

        with open(self.config_file, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)

                if "servos" in data:
                    servos_data = data["servos"]
                    self.hw_mode = data.get("settings", {}).get("hw_mode", "Mock")
                else:
                    servos_data = data
                    self.hw_mode = "Mock"

                for ch_str, servo_data in servos_data.items():
                    ch_id = int(ch_str)
                    name = servo_data.get("name", f"{config.SERVO_DEF_NAME} {ch_id}")
                    pos = servo_data.get("position", config.SERVO_DEF_POS)
                    step = servo_data.get("step", config.SERVO_DEF_STEP)
                    min_val = servo_data.get("min_val", config.SERVO_DEF_MIN)
                    max_val = servo_data.get("max_val", config.SERVO_DEF_MAX)

                    new_servo = Servo(ch_id, name, pos, step, min_val, max_val)
                    self.servos[ch_id] = new_servo

            except (json.JSONDecodeError, ValueError):
                pass  # ignore errors caused by a damaged file

    def add_servo(self, name: str) -> Optional['Servo']:
        """
        Finds the first free channel and adds a new servo.
        Returns None when no channel is free.
        """
        existing_names = [servo.name for servo in self.servos.values()]

        core_name = name
        counter = 1
        parts = name.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            core_name = parts[0]
            counter = int(parts[1])

        unique_name = name
        while unique_name in existing_names:
            unique_name = f"{core_name} {counter}"
            counter += 1

        for ch_id in range(self.max_channels):
            if ch_id not in self.servos:
                new_servo = Servo(channel=ch_id, name=unique_name)
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
