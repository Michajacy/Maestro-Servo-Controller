from typing import Optional

class Servo:
    def __init__(self, channel: int, name: str, intial_position: int = 1500) -> None:
        self.channel = channel
        self.name = name
        self.position = intial_position


class ServoManager:
    def __init__(self, hardware_interface, max_channels: int = 24) -> None:
        self.hw = hardware_interface
        self.max_channels = max_channels
        self.servos = {} 

    def add_servo(self, name: str) -> Optional['Servo']:
        """finds first free channel and adds new servo"""
        for ch in range(self.max_channels):
            if ch not in self.servos:
                new_servo = Servo(channel=ch, name=name)
                self.servos[ch] = new_servo

                #set strting position
                self.hw.set_target(ch, new_servo.position)
                return new_servo

        return None

    def remove_servo(self, channel: int) -> None:
        if channel in self.servos:
            self.hw.set_target(channel, 0)
            del self.servos[channel]

    def set_servo_position(self, channel: int, position: int) -> None:
        if channel in self.servos:
            self.servos[channel].position = position
            self.hw.set_target(channel, position)