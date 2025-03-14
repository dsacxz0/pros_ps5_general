import pygame
import json
import websocket
from utils import map_trigger_value, vel_limit
import time

class PS5Controller:
    def __init__(self, rosbridge_port=9090):
        # 初始化 pygame 與介面
        pygame.init()
        pygame.joystick.init()
        self.rosbridge_ip = ""  # 一開始不設定 IP，由使用者輸入
        self.rosbridge_port = rosbridge_port
        self.velocity = 10.0
        self.direction = ""
        self.input_mode = True  # 啟動時強制進入 IP 輸入模式
        self.ip_input = ""       # 暫存使用者輸入的 IP 字串
        self.font = pygame.font.SysFont("Arial", 24)
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("PS5 Controller UI")

        # 初始化搖桿
        if pygame.joystick.get_count() == 0:
            print("No joystick detected.")
            self.joystick = None
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Detected Joystick: {self.joystick.get_name()}")

        # 初始不嘗試連線，等待使用者輸入 rosbridge_ip
        self.ws = None

    def connect_rosbridge(self, ip):
        self.rosbridge_ip = ip
        self.ws_url = f"ws://{ip}:{self.rosbridge_port}"
        try:
            self.ws = websocket.create_connection(self.ws_url)
            print(f"Connected to rosbridge via websocket at {self.ws_url}")
            # 連線成功後先 advertise topic
            self.advertise_topic("/car_C_rear_wheel", "std_msgs/Float32MultiArray")
            self.advertise_topic("/car_C_front_wheel", "std_msgs/Float32MultiArray")
        except Exception as e:
            print(f"Failed to connect to rosbridge at {self.ws_url}: {e}")
            self.ws = None

    def disconnect_rosbridge(self):
        if self.ws:
            try:
                self.ws.close()
                print("Disconnected from rosbridge.")
            except Exception as e:
                print(f"Error closing websocket: {e}")
        self.ws = None

    def update_rosbridge_ip(self, new_ip):
        # 斷開目前連線（若有）再以新 IP 建立連線
        self.disconnect_rosbridge()
        self.connect_rosbridge(new_ip)

    def advertise_topic(self, topic, msg_type):
        if not self.ws:
            return
        advertise_msg = {
            "op": "advertise",
            "topic": topic,
            "type": msg_type
        }
        try:
            self.ws.send(json.dumps(advertise_msg))
            print(f"Advertised topic {topic} with type {msg_type}")
        except Exception as e:
            print(f"Failed to advertise topic {topic}: {e}")

    def handle_button_press(self, button):
        if button == 11:  # 前進
            self.publish_wheel_command([self.velocity, self.velocity, self.velocity, self.velocity])
        elif button == 12:  # 後退
            self.publish_wheel_command([-self.velocity, -self.velocity, -self.velocity, -self.velocity])
        elif button == 13:  # 左轉
            self.publish_wheel_command([-self.velocity, self.velocity, -self.velocity, self.velocity])
        elif button == 14:  # 右轉
            self.publish_wheel_command([self.velocity, -self.velocity, self.velocity, -self.velocity])
        elif button == 7:   # 停止
            self.publish_wheel_command([0.0, 0.0, 0.0, 0.0])
        elif button == 9:   # L1：減速
            self.velocity -= 5.0
            self.velocity = vel_limit(self.velocity)
        elif button == 10:  # R1：加速
            self.velocity += 5.0
            self.velocity = vel_limit(self.velocity)
        time.sleep(0.01)

    def handle_button_release(self, button):
        pass

    def handle_axis_motion(self, axis, value):
        # 針對 R2 與 L2 觸發器
        if axis in [2, 5]:
            mapped_value = map_trigger_value(value)
            # 可根據需要更新 velocity，例如：
            # self.velocity = mapped_value
        else:
            pass

    def handle_hat_motion(self, hat, value):
        pass

    def publish_wheel_command(self, value):
        if not self.ws:
            print("Websocket connection not established.")
            return

        # 後輪訊息
        rear_wheel_msg = {
            "op": "publish",
            "topic": "/car_C_rear_wheel",
            "msg": {
                "layout": {
                    "dim": [
                        {
                            "label": "rear_wheels",
                            "size": 2,
                            "stride": 2
                        }
                    ],
                    "data_offset": 0
                },
                "data": [value[0], value[1], value[2], value[3]]
            }
        }
        # 前輪訊息
        front_wheel_msg = {
            "op": "publish",
            "topic": "/car_C_front_wheel",
            "msg": {
                "layout": {
                    "dim": [
                        {
                            "label": "front_wheels",
                            "size": 2,
                            "stride": 2
                        }
                    ],
                    "data_offset": 0
                },
                "data": [value[0], value[1]]
            }
        }
        try:
            self.ws.send(json.dumps(rear_wheel_msg))
            self.ws.send(json.dumps(front_wheel_msg))
            print("Published wheel commands")
        except Exception as e:
            print(f"Failed to publish wheel command: {e}")

    def run(self):
        if not self.joystick:
            return
        running = True
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                # 關閉程式
                if event.type == pygame.QUIT:
                    running = False

                # 處理鍵盤事件
                elif event.type == pygame.KEYDOWN:
                    if self.input_mode:
                        # 輸入模式中累積使用者輸入
                        if event.key == pygame.K_RETURN:
                            # 使用者按 Enter 確認輸入，若有輸入內容則更新 rosbridge 連線
                            if self.ip_input:
                                self.update_rosbridge_ip(self.ip_input)
                            self.input_mode = False
                            self.ip_input = ""
                        elif event.key == pygame.K_BACKSPACE:
                            self.ip_input = self.ip_input[:-1]
                        else:
                            self.ip_input += event.unicode
                    else:
                        # 非輸入模式下，按 I 可切換回輸入模式（重新連線）
                        if event.key == pygame.K_i:
                            self.input_mode = True
                            self.ip_input = ""

                # 處理搖桿事件（僅在非輸入模式時回應）
                if not self.input_mode:
                    if event.type == pygame.JOYBUTTONDOWN:
                        self.handle_button_press(event.button)
                    elif event.type == pygame.JOYBUTTONUP:
                        self.handle_button_release(event.button)
                    elif event.type == pygame.JOYAXISMOTION:
                        self.handle_axis_motion(event.axis, event.value)
                    elif event.type == pygame.JOYHATMOTION:
                        self.handle_hat_motion(event.hat, event.value)

            # 畫面繪製
            self.screen.fill((0, 0, 0))

            # 顯示當前速度
            velocity_text = self.font.render(f"Velocity: {self.velocity}", True, (255, 255, 255))
            self.screen.blit(velocity_text, (10, 10))

            # 顯示連線狀態與目前 IP
            connection_status = "Connected" if self.ws else "Disconnected"
            connection_text = self.font.render(f"ROSBridge ({self.rosbridge_ip}): {connection_status}", True, (255, 255, 255))
            self.screen.blit(connection_text, (10, 40))

            # 顯示提示訊息：若正在輸入則提示輸入新 IP，否則提示按 I 可重新輸入
            if self.input_mode:
                input_box = self.font.render(f"Enter new ROSBridge IP: {self.ip_input}", True, (0, 255, 0))
                self.screen.blit(input_box, (10, 70))
            else:
                instructions = self.font.render("Press 'I' to input new ROSBridge IP", True, (255, 255, 0))
                self.screen.blit(instructions, (10, 70))

            pygame.display.flip()
            clock.tick(30)

        # 離開前關閉連線與 pygame
        self.disconnect_rosbridge()
        pygame.quit()


if __name__ == "__main__":
    controller = PS5Controller(rosbridge_port=9090)
    controller.run()
