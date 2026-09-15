from typing import Optional
import json
import os

class Servo:
    """Represents individual servo"""
    def __init__(self, channel: int, name: str, intial_position: int = 1500, 
                 step: int = 50, min_val: int = 1000, max_val: int = 2000) -> None:
        self.channel = channel
        self.name = name
        self.position = intial_position
        self.step = step
        self.min_val = min_val
        self.max_val = max_val


class ServoManager:
    """Assigns channels and communicates with servos"""
    def __init__(self, hardware_interface, max_channels: int = 24) -> None:
        self.hw = hardware_interface
        self.max_channels = max_channels
        self.servos = {} 
        self.config_file = "servos_config.json"

        self._load_config()

    def _save_config(self) -> None:
        """Saves current servos state to a JSON file"""
        data = {}
        for ch, servo in self.servos.items():
            data[ch] = {
                "name": servo.name,
                "position": servo.position,
                "step": servo.step,
                "min_val": servo.min_val,
                "max_val": servo.max_val
            }

        with open(self.config_file, "w") as f:
            json.dump(data, f, indent=4)


    def _load_config(self) -> None:
        """Loads servos state from a JSON file if exists"""
        if not os.path.exists(self.config_file):
            return

        with open(self.config_file, "r") as f:
            try: 
                data = json.load(f)
                for ch_str, servo_data in data.items():
                    ch = int(ch_str)
                    name = servo_data.get("name", f"Servo {ch}")
                    pos = servo_data.get("position", 1500)
                    step = servo_data.get("step", 50)
                    min_val = servo_data.get("min_val", 1000)
                    max_val = servo_data.get("max_val", 2000)

                    new_servo = Servo(ch, name, pos, step, min_val, max_val)
                    self.servos[ch] = new_servo
                    self.hw.set_target(ch, pos)

            except:
                pass #ignore errors caused by damaged file

    def add_servo(self, name: str) -> Optional['Servo']:
        """finds first free channel and adds new servo. Returns None when no channel is free"""
        for ch in range(self.max_channels):
            if ch not in self.servos:
                new_servo = Servo(channel=ch, name=name)
                self.servos[ch] = new_servo

                #set strting position
                self.hw.set_target(ch, new_servo.position)
                self._save_config()
                return new_servo

        return None

    def remove_servo(self, channel: int) -> None:
        """removes servo from manager"""
        if channel in self.servos:
            self.hw.set_target(channel, 0)
            del self.servos[channel]
            self._save_config()

    def set_servo_position(self, channel: int, position: int) -> None:
        """Updates servo's position and sends it to device"""
        if channel in self.servos:
            self.servos[channel].position = position
            self.hw.set_target(channel, position)
            self._save_config()