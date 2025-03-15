import pygame
import time
import math
import csv
from utils import map_trigger_value, vel_limit

class JoystickHandler:
    def __init__(self, num_joints=5):
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            print("No joystick detected.")
            self.joystick = None
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()  # 初始化搖桿
            print(f"Detected Joystick: {self.joystick.get_name()}")

        # 預設值
        self.velocity = 10.0
        self.arm_joints_count = num_joints
        self.arm_angles = [0.0] * self.arm_joints_count
        self.joint_limits = [(0.0, math.radians(180)) for _  in range(self.arm_joints_count)]
        self.arm_index = 0
        self.arm_topic = "/robot_arm"
        self.angle_step_deg = 10.0    # 每次增/減的角度 (預設 10 度)
        self.speed_incr = 5.0         # 每次加減的速度值 (預設 5)
        # 預設前後輪 topic 與 cmd 讀取範圍
        self.front_wheel_topic = "/car_C_front_wheel"
        self.rear_wheel_topic  = "/car_C_rear_wheel"
        self.front_wheel_range = (0, 2)   # 默認讀取 cmd[0:2]
        self.rear_wheel_range  = (2, 4)   # 默認讀取 cmd[2:4]

        # 從 CSV 載入設定
        self.load_config("config.csv")

    def load_config(self, filename="config.csv"):
        """
        讀取 CSV 檔案，格式範例如下（含表頭）：

        type,param,value1,value2
        global,joints_count,6,
        global,angle_step,15,
        global,arm_topic,/robot_arm,
        global,speed_step,5,
        global,front_wheel_topic,/car_C_front_wheel,
        global,rear_wheel_topic,/car_C_rear_wheel,
        global,front_wheel_range,0-2,
        global,rear_wheel_range,2-4,
        joint,1,0,180
        joint,2,0,180
        joint,3,0,180
        joint,4,0,180
        joint,5,0,180
        joint,6,0,180
        """
        try:
            with open(filename, "r", newline='') as f:
                reader = csv.DictReader(f)
                global_params = {}
                joint_rows = []
                for row in reader:
                    if row["type"] == "global":
                        global_params[row["param"]] = row["value1"]
                    elif row["type"] == "joint":
                        joint_rows.append(row)
            # 全域參數讀取
            if "joints_count" in global_params:
                self.arm_joints_count = int(global_params["joints_count"])
            if "angle_step" in global_params:
                self.angle_step_deg = float(global_params["angle_step"])
            if "arm_topic" in global_params and global_params["arm_topic"]:
                self.arm_topic = global_params["arm_topic"]
            if "speed_step" in global_params:
                self.speed_incr = float(global_params["speed_step"])
            if "front_wheel_topic" in global_params and global_params["front_wheel_topic"]:
                self.front_wheel_topic = global_params["front_wheel_topic"]
            if "rear_wheel_topic" in global_params and global_params["rear_wheel_topic"]:
                self.rear_wheel_topic = global_params["rear_wheel_topic"]
            if "front_wheel_range" in global_params:
                try:
                    parts = global_params["front_wheel_range"].split("-")
                    self.front_wheel_range = (int(parts[0]), int(parts[1]))
                except:
                    self.front_wheel_range = (0, 2)
            if "rear_wheel_range" in global_params:
                try:
                    parts = global_params["rear_wheel_range"].split("-")
                    self.rear_wheel_range = (int(parts[0]), int(parts[1]))
                except:
                    self.rear_wheel_range = (2, 4)
            # 讀取各關節上下限
            joint_rows.sort(key=lambda x: int(x["param"]))  # 根據 joint 編號排序
            self.joint_limits = []
            for i in range(self.arm_joints_count):
                if i < len(joint_rows):
                    lower_deg = float(joint_rows[i]["value1"])
                    upper_deg = float(joint_rows[i]["value2"])
                    self.joint_limits.append((math.radians(lower_deg), math.radians(upper_deg)))
                else:
                    self.joint_limits.append((0.0, math.radians(180)))
            self.arm_angles = [0.0] * self.arm_joints_count
            self.arm_index = 0
            print(f"Loaded config: {self.arm_joints_count} joints, angle step {self.angle_step_deg} deg, speed step {self.speed_incr},")
            print(f"arm topic: {self.arm_topic}, front wheel topic: {self.front_wheel_topic}, rear wheel topic: {self.rear_wheel_topic}")
            print(f"front wheel range: {self.front_wheel_range}, rear wheel range: {self.rear_wheel_range}")
        except FileNotFoundError:
            print(f"Config CSV '{filename}' not found, using defaults.")
        except Exception as e:
            print("Error loading config CSV:", e)

    def clip_arm_angles(self):
        """將各關節角度限制在上下限之間（弧度）"""
        for i in range(self.arm_joints_count):
            lower, upper = self.joint_limits[i]
            self.arm_angles[i] = max(lower, min(self.arm_angles[i], upper))

    def set_joint_count(self, count):
        """指定關節數量（不從檔案時使用）"""
        self.arm_joints_count = count
        self.arm_angles = [0.0] * count
        self.joint_limits = [(0.0, math.radians(180)) for _ in range(count)]
        self.arm_index = 0

    def process_button_press(self, button, wheel_publish_callback, arm_publish_callback):
        # 轉換步進角度為弧度
        step_radians = math.radians(self.angle_step_deg)

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
        elif button == 8:   # 重設所有手臂角度為 0
            self.arm_angles = [0.0] * self.arm_joints_count
            self.clip_arm_angles()
            arm_publish_callback({"positions": self.arm_angles})
        elif button == 9:   # L1：減速
            self.velocity -= self.speed_incr
            self.velocity = vel_limit(self.velocity)
        elif button == 10:  # R1：加速
            self.velocity += self.speed_incr
            self.velocity = vel_limit(self.velocity)
        elif button == 1:   # 增加當前關節角度
            self.arm_angles[self.arm_index] += step_radians
            self.clip_arm_angles()
            arm_publish_callback({"positions": self.arm_angles})
        elif button == 2:   # 減少當前關節角度
            self.arm_angles[self.arm_index] -= step_radians
            self.clip_arm_angles()
            arm_publish_callback({"positions": self.arm_angles})
        elif button == 3:   # 上一個關節
            self.arm_index = max(self.arm_index - 1, 0)
        elif button == 0:   # 下一個關節
            self.arm_index = min(self.arm_index + 1, self.arm_joints_count - 1)

        time.sleep(0.01)

    def process_axis_motion(self, axis, value):
        if axis in [2, 5]:
            mapped_value = map_trigger_value(value)
            # 如需要，可根據 mapped_value 更新 self.velocity
            # self.velocity = mapped_value

    def get_joystick(self):
        return self.joystick