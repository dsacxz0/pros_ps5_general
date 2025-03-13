import pygame
import json
import websocket
from utils import map_trigger_value, vel_limit
import time

class PS5Controller:
    def __init__(self, rosbridge_ip='localhost', rosbridge_port=9090):
        pygame.init()
        pygame.joystick.init()
        self.velocity = 10.0
        self.direction = ""

        if pygame.joystick.get_count() == 0:
            print("No joystick detected.")
            self.joystick = None
            return

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        print(f"Detected Joystick: {self.joystick.get_name()}")

        # 建立 websocket 連線到 rosbridge
        self.ws_url = f"ws://{rosbridge_ip}:{rosbridge_port}"
        try:
            self.ws = websocket.create_connection(self.ws_url)
            print(f"Connected to rosbridge via websocket at {self.ws_url}")
        except Exception as e:
            print(f"Failed to connect to rosbridge at {self.ws_url}: {e}")
            self.ws = None

        if self.ws:
            # 先 advertise topic，讓 rosbridge 知道我們要發佈此 topic 的訊息
            self.advertise_topic("/car_C_rear_wheel", "std_msgs/Float32MultiArray")
            self.advertise_topic("/car_C_front_wheel", "std_msgs/Float32MultiArray")

    def advertise_topic(self, topic, msg_type):
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
        if button == 11:  # forward
            self.publish_wheel_command([self.velocity, self.velocity, self.velocity, self.velocity])
        elif button == 12:  # backward
            self.publish_wheel_command([-self.velocity, -self.velocity, -self.velocity, -self.velocity])
        elif button == 13:  # left
            self.publish_wheel_command([-self.velocity, self.velocity, -self.velocity, self.velocity])
        elif button == 14:  # right
            self.publish_wheel_command([self.velocity, -self.velocity, self.velocity, -self.velocity])
        elif button == 0:  # X
            pass
        elif button == 1:  # O
            pass
        elif button == 2:  # Square
            pass
        elif button == 3:  # Triangle
            pass
        elif button == 7:  # 停止
            self.publish_wheel_command([0.0, 0.0, 0.0, 0.0])
        elif button == 9:  # L1
            # self.velocity -= 10.0
            # self.velocity = vel_limit(self.velocity)
            pass
        elif button == 10:  # R1
            # self.velocity += 10.0
            # self.velocity = vel_limit(self.velocity)
            pass
        time.sleep(0.01)

        # print(f"Button {button} pressed")

    def handle_button_release(self, button):
        # print(f"Button {button} released")
        pass

    def handle_axis_motion(self, axis, value):
        # R2 and L2 triggers
        if axis in [2, 5]:
            mapped_value = map_trigger_value(value)
            # 根據需要更新 velocity，例如：
            # self.velocity = mapped_value
        else:
            pass

    def handle_hat_motion(self, hat, value):
        pass

    def publish_wheel_command(self, value):
        if not self.ws:
            print("Websocket connection not established.")
            return

        # 完整填寫 std_msgs/Float32MultiArray 的所有欄位:
        # 對後輪訊息 (topic: /car_C_rear_wheel)
        rear_wheel_msg = {
            "op": "publish",
            "topic": "/car_C_rear_wheel",
            "msg": {
                "layout": {
                    "dim": [
                        {
                            "label": "rear_wheels",
                            "size": 2,      # 資料數量
                            "stride": 2     # 從本維度到下一維度所需跨越的元素數量 (這裡僅有一維，stride 可與 size 相同)
                        }
                    ],
                    "data_offset": 0
                },
                "data": [value[2], value[3]]
            }
        }
        # 對前輪訊息 (topic: /car_C_front_wheel)
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
        if not self.ws:
            print("Websocket not available, exiting.")
            return

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.JOYBUTTONDOWN:
                    self.handle_button_press(event.button)
                elif event.type == pygame.JOYBUTTONUP:
                    self.handle_button_release(event.button)
                elif event.type == pygame.JOYAXISMOTION:
                    self.handle_axis_motion(event.axis, event.value)
                elif event.type == pygame.JOYHATMOTION:
                    self.handle_hat_motion(event.hat, event.value)

        # 關閉 websocket 連線與 pygame
        try:
            self.ws.close()
        except Exception as e:
            print(f"Error closing websocket: {e}")
        pygame.quit()


if __name__ == "__main__":
    controller = PS5Controller(rosbridge_ip='192.168.0.123', rosbridge_port=9090)
    controller.run()
