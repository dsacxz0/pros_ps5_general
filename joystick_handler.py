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
        # Default configuration in case loading fails
        self.arm_joints_count = num_joints
        self.arm_angles = [0.0] * self.arm_joints_count
        # Each element is a tuple (lower_limit, upper_limit) in radians, default 0 ~ 180°
        self.joint_limits = [(0.0, math.radians(180)) for _ in range(self.arm_joints_count)]
        self.arm_index = 0

        # Try to load configuration from txt file
        self.load_joint_config("joint_config.txt")

    def load_joint_config(self, filename):
        """
        讀取 joint_config.txt 檔案：
        第一行為關節數量，
        接下來每一行包含該關節的下限和上限（單位：度），以空白分隔。
        例如：
            5
            0 180
            0 180
            0 180
            0 180
            0 180
        """
        try:
            with open(filename, "r") as f:
                lines = [line.strip() for line in f if line.strip()]
            if not lines:
                return
            count = int(lines[0])
            self.arm_joints_count = count
            self.arm_angles = [0.0] * count
            self.joint_limits = []
            for i in range(count):
                if i+1 < len(lines):
                    parts = lines[i+1].split()
                    if len(parts) >= 2:
                        lower = math.radians(float(parts[0]))
                        upper = math.radians(float(parts[1]))
                        self.joint_limits.append((lower, upper))
                    else:
                        self.joint_limits.append((0.0, math.radians(180)))
                else:
                    self.joint_limits.append((0.0, math.radians(180)))
            # Reset the selected joint index to 0
            self.arm_index = 0
            print(f"Loaded joint config: {self.arm_joints_count} joints")
        except Exception as e:
            print("Error loading joint config:", e)

    def set_joint_count(self, count):
        """指定有多少個關節 (不使用檔案時)"""
        self.arm_joints_count = count
        self.arm_angles = [0.0] * count
        self.joint_limits = [(0.0, math.radians(180)) for _ in range(count)]
        self.arm_index = 0

    def clip_arm_angles(self):
        """限制所有關節角度在各自上下限之間（以弧度表示）"""
        for i in range(self.arm_joints_count):
            lower, upper = self.joint_limits[i]
            self.arm_angles[i] = max(lower, min(self.arm_angles[i], upper))

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
        elif button == 8:   # 停止：重設所有手臂角度為0
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
            # 如需要，可根據 mapped_value 更新速度，例如：
            # self.velocity = mapped_value

    def get_joystick(self):
        return self.joystick
