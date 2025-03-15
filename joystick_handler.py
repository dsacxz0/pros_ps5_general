# joystick_handler.py
import pygame
import time
from utils import map_trigger_value, vel_limit

class JoystickHandler:
    def __init__(self):
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            print("No joystick detected.")
            self.joystick = None
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Detected Joystick: {self.joystick.get_name()}")
        self.velocity = 10.0

    def process_button_press(self, button, publish_callback):
        if button == 11:  # 前進
            publish_callback([self.velocity, self.velocity, self.velocity, self.velocity])
        elif button == 12:  # 後退
            publish_callback([-self.velocity, -self.velocity, -self.velocity, -self.velocity])
        elif button == 13:  # 左轉
            publish_callback([-self.velocity, self.velocity, -self.velocity, self.velocity])
        elif button == 14:  # 右轉
            publish_callback([self.velocity, -self.velocity, self.velocity, -self.velocity])
        elif button == 7:   # 停止
            publish_callback([0.0, 0.0, 0.0, 0.0])
        elif button == 9:   # L1：減速
            self.velocity -= 5.0
            self.velocity = vel_limit(self.velocity)
        elif button == 10:  # R1：加速
            self.velocity += 5.0
            self.velocity = vel_limit(self.velocity)
        time.sleep(0.01)

    def process_axis_motion(self, axis, value):
        if axis in [2, 5]:
            mapped_value = map_trigger_value(value)
            # 如需要可用 mapped_value 更新速度，例如：
            # self.velocity = mapped_value

    def get_joystick(self):
        return self.joystick
