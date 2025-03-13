import pygame
import roslibpy
from utils import map_trigger_value, vel_limit


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

        # ROS setup 使用參數傳入的 IP 和 port 進行連線
        self.client = roslibpy.Ros(host=rosbridge_ip, port=rosbridge_port)
        self.client.run()
        # 修改兩個 topic 的 message type 為相同格式
        self.car_C_rear_wheel_pub = roslibpy.Topic(
            self.client, '/car_C_rear_wheel', 'std_msgs/Float32MultiArray')
        self.car_C_front_wheel_pub = roslibpy.Topic(
            self.client, '/car_C_front_wheel', 'std_msgs/Float32MultiArray')

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
        elif button == 7:
            self.publish_wheel_command([0.0, 0.0, 0.0, 0.0])
        elif button == 9:  # L1
            # self.velocity -= 10.0
            # self.velocity = vel_limit(self.velocity)
            pass
        elif button == 10:  # R1
            # self.velocity += 10.0
            # self.velocity = vel_limit(self.velocity)
            pass

        print(f"Button {button} pressed")

    def handle_button_release(self, button):
        print(f"Button {button} released")

    def handle_axis_motion(self, axis, value):
        # R2 and L2 triggers
        if axis in [2, 5]:
            mapped_value = map_trigger_value(value)
            # self.velocity = mapped_value
        else:
            pass

    def handle_hat_motion(self, hat, value):
        pass

    def publish_wheel_command(self, value):
        rear_wheel_msg = {'data': [value[2], value[3]]}  # 針對後輪
        front_wheel_msg = {'data': [value[0], value[1]]}  # 針對前輪

        self.car_C_rear_wheel_pub.publish(roslibpy.Message(rear_wheel_msg))
        self.car_C_front_wheel_pub.publish(roslibpy.Message(front_wheel_msg))
        print("Published wheel commands")

    def run(self):
        if not self.joystick:
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

        self.client.terminate()
        pygame.quit()


if __name__ == "__main__":
    controller = PS5Controller(rosbridge_ip='127.0.0.1', rosbridge_port=9090)
    controller.run()
