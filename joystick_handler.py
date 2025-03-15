# joystick_handler.py
import pygame
import time
import math
from utils import map_trigger_value, vel_limit

class JoystickHandler:
    def __init__(self, num_joints=5):
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            print("No joystick detected.")
            self.joystick = None
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Detected Joystick: {self.joystick.get_name()}")
        self.velocity = 10.0
        self.arm_joints_count = num_joints
        self.arm_angles = [0.0] * self.arm_joints_count
        self.arm_index = 0

    def set_joint_count(self, count):
        """指定有多少個關節"""
        self.arm_joints_count = count
        self.arm_angles = [0.0] * count
        self.arm_index = 0

    def clip_arm_angles(self):
        """限制所有關節角度在 0 ~ 180 度（以弧度表示）"""
        for i in range(self.arm_joints_count):
            self.arm_angles[i] = max(0.0, min(self.arm_angles[i], math.radians(180)))

    def process_button_press(self, button, wheel_publish_callback, arm_publish_callback):
        if button == 11:  # 前進
            wheel_publish_callback([self.velocity, self.velocity, self.velocity, self.velocity])
        elif button == 12:  # 後退
            wheel_publish_callback([-self.velocity, -self.velocity, -self.velocity, -self.velocity])
        elif button == 13:  # 左轉
            wheel_publish_callback([-self.velocity, self.velocity, -self.velocity, self.velocity])
        elif button == 14:  # 右轉
            wheel_publish_callback([self.velocity, -self.velocity, self.velocity, -self.velocity])
        elif button == 7:   # 停止
            wheel_publish_callback([0.0, 0.0, 0.0, 0.0])
        elif button == 8:   # 停止
            self.arm_angles = [0.0] * self.arm_joints_count
            self.clip_arm_angles()
            arm_publish_callback({"positions": self.arm_angles})
        elif button == 9:   # L1：減速
            self.velocity -= 5.0
            self.velocity = vel_limit(self.velocity)
        elif button == 10:  # R1：加速
            self.velocity += 5.0
            self.velocity = vel_limit(self.velocity)
        elif button == 1: # 加10度
            self.arm_angles[self.arm_index] += math.radians(10)
            self.clip_arm_angles()
            arm_publish_callback({"positions": self.arm_angles})
        elif button == 2: # 減10度
            self.arm_angles[self.arm_index] -= math.radians(10)
            self.clip_arm_angles()
            arm_publish_callback({"positions": self.arm_angles})
        elif button == 3:  # 上個關節
            self.arm_index = max(self.arm_index - 1, 0)
        elif button == 0:  # 下個關節
            self.arm_index = min(self.arm_index + 1, self.arm_joints_count - 1)




        time.sleep(0.01)

    def process_axis_motion(self, axis, value):
        if axis in [2, 5]:
            mapped_value = map_trigger_value(value)
            # 如需要可用 mapped_value 更新速度，例如：
            # self.velocity = mapped_value

    def get_joystick(self):
        return self.joystick
