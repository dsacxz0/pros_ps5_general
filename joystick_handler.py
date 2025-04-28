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

        self.reset_arm_angle = 0.0  # 初始化 reset_arm_angle 屬性

        #controller joystick axis
        self.left_stick_horizontal = 0
        self.left_stick_vertical = 1
        self.right_stick_horizontal = 2
        self.right_stick_vertical = 3

        self.clockwise_rotation = 4
        self.counterclockwise_rotation = 5

        #controller button mapping
        self.arm_up = 4
        self.arm_down = 5


        self.wheel_speed = [0, 0, 0, 0] #wheel speed for gui

        #minimal joystick value to prevent drifting
        self.min_joystick_value = 0.1


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
            if "reset_arm_angle" in global_params and global_params["reset_arm_angle"]:
                self.reset_arm_angle = float(global_params["reset_arm_angle"])
            else:
                self.reset_arm_angle = 0.0
            if "rear_wheel_range" in global_params:
                try:
                    parts = global_params["rear_wheel_range"].split("-")
                    self.rear_wheel_range = (int(parts[0]), int(parts[1]))
                except:
                    self.rear_wheel_range = (2, 4)
            if "left_stick_horizontal" in global_params:
                self.left_stick_horizontal = int (global_params["left_stick_horizontal"])
            if "left_stick_vertical" in global_params:
                self.left_stick_vertical = int (global_params["left_stick_vertical"])
            if "right_stick_horizontal" in global_params:
                self.right_stick_horizontal = int (global_params["right_stick_horizontal"])
            if "right_stick_vertical" in global_params:
                self.right_stick_vertical = int (global_params["right_stick_vertical"])
            if "clockwise_rotation" in global_params:
                self.clockwise_rotation = int (global_params["clockwise_rotation"])
            if "counterclockwise_rotation" in global_params:
                self.counterclockwise_rotation = int (global_params["counterclockwise_rotation"])
            if "arm_up" in global_params:
                self.arm_up = int (global_params["arm_up"])
            if "arm_down" in global_params:
                self.arm_down = int (global_params["arm_down"])
            if "min_joystick_value" in global_params:
                self.min_joystick_value = float (global_params["min_joystick_value"])
            
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
        elif button == 8:   # 重設所有手臂角度為 CSV 設定的值
            reset_val = math.radians(self.reset_arm_angle)
            self.arm_angles = [reset_val] * self.arm_joints_count
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

    def process_joystick_continuous(self, joysticks, wheel_publish_callback):
        for joystick in joysticks.values():

            axis_vertical = 0
            axis_horizontal = 0
            axis_rotational = 0

            #get left stick horizontal axis
            if abs(joystick.get_axis(self.left_stick_horizontal)) > self.min_joystick_value:
                axis_horizontal = joystick.get_axis(self.left_stick_horizontal)
            #get left stick vertical axis
            if abs(joystick.get_axis(self.left_stick_vertical)) > self.min_joystick_value:
                axis_vertical = -joystick.get_axis(self.left_stick_vertical)
            #get clockwise rotation axis (trigger button starts at -1 and ends at 1)
            if abs((joystick.get_axis(self.clockwise_rotation) + 1) / 2) > self.min_joystick_value:
                axis_rotational += (joystick.get_axis(self.clockwise_rotation) + 1) / 2
            #get counterclockwise rotation axis (trigger button starts at -1 and ends at 1)
            if abs((joystick.get_axis(self.counterclockwise_rotation) + 1) / 2) > self.min_joystick_value:
                axis_rotational -= (joystick.get_axis(self.counterclockwise_rotation) + 1) / 2          
            
            #calculate mecanum wheel rotations
            frontLeft = axis_vertical + axis_horizontal + axis_rotational
            frontRight = axis_vertical - axis_horizontal - axis_rotational        
            rearLeft = axis_vertical - axis_horizontal + axis_rotational
            rearRight = axis_vertical + axis_horizontal - axis_rotational

            self.wheel_speed = [frontLeft * self.velocity, frontRight * self.velocity, rearLeft * self.velocity, rearRight * self.velocity]
            wheel_publish_callback(self.wheel_speed)

            # #get right stick horizontal axis
            # if abs(joystick.get_axis(self.right_stick_horizontal)) > self.min_joystick_value:
            #     x = joystick.get_axis(self.right_stick_horizontal)
            
           
            # z += joystick.get_button(self.arm_up)
            # z -= joystick.get_button(self.arm_down)

    def process_keypress_continuous(self, keys, wheel_publish_callback, arm_publish_callback, ik, joint_offset_degree):
        axis_vertical = 0
        axis_horizontal = 0
        axis_rotational = 0

        if keys[pygame.K_w]:
            axis_vertical += 1
        if keys[pygame.K_s]:
            axis_vertical -= 1
        if keys[pygame.K_d]:
            axis_horizontal += 1
        if keys[pygame.K_a]:
            axis_horizontal -= 1
        if keys[pygame.K_r]:
            axis_rotational += 1
        if keys[pygame.K_e]:
            axis_rotational -= 1

        frontLeft = axis_vertical + axis_horizontal + axis_rotational
        frontRight = axis_vertical - axis_horizontal - axis_rotational        
        rearLeft = axis_vertical - axis_horizontal + axis_rotational
        rearRight = axis_vertical + axis_horizontal - axis_rotational

        self.wheel_speed = [frontLeft * self.velocity, frontRight * self.velocity, rearLeft * self.velocity, rearRight * self.velocity]
        wheel_publish_callback(self.wheel_speed)

        dx = 0.00
        dy = 0.00
        dz = 0.00

        movespeed = 0.05

        if keys[pygame.K_UP]:
            dy += movespeed
        if keys[pygame.K_DOWN]:
            dy -= movespeed
        if keys[pygame.K_RIGHT]:
            dx += movespeed
        if keys[pygame.K_LEFT]:
            dx -= movespeed
        if keys[pygame.K_SPACE]:
            dz += movespeed
        if keys[pygame.K_LCTRL]:
            dz -= movespeed
        
        self.arm_angles = ik.solve(dx,dy,dz)
        # print(self.arm_angles)
        joint_offset_radian = [math.radians(deg) for deg in joint_offset_degree]
        arm_angle_adjusted = [i - j for i, j in zip(self.arm_angles, joint_offset_radian)]
        # print(arm_angle_adjusted)
        arm_publish_callback({"positions": arm_angle_adjusted})


    def get_joystick(self):
        return self.joystick