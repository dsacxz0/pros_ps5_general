# main.py
import pygame
from ui import UI
from ws_client import RosbridgeClient
from joystick_handler import JoystickHandler

def publish_wheel(ws_client, cmd):
    # 建立後輪與前輪的完整訊息（std_msgs/Float32MultiArray）
    rear_msg = {
        "layout": {
            "dim": [{
                "label": "rear_wheels",
                "size": 2,
                "stride": 2
            }],
            "data_offset": 0
        },
        "data": cmd  # 此範例直接傳送 4 個數值，依實際需求調整
    }
    front_msg = {
        "layout": {
            "dim": [{
                "label": "front_wheels",
                "size": 2,
                "stride": 2
            }],
            "data_offset": 0
        },
        "data": cmd[:2]  # 前輪只用前兩個值
    }
    ws_client.publish("/car_C_rear_wheel", rear_msg)
    ws_client.publish("/car_C_front_wheel", front_msg)

def main():
    pygame.init()
    clock = pygame.time.Clock()
    ui = UI()
    ws_client = RosbridgeClient(rosbridge_port=9090)
    joystick_handler = JoystickHandler()

    # 初始狀態：輸入 IP 模式
    input_mode = True
    ip_input = ""
    connection_error = ""
    rosbridge_ip = ""

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # 當處於 IP 輸入模式時，累積使用者輸入
                if input_mode:
                    if event.key == pygame.K_RETURN:
                        if ip_input:
                            rosbridge_ip = ip_input
                            if ws_client.connect(rosbridge_ip):
                                connection_error = ""
                                # 連線成功後 advertise topic
                                ws_client.advertise_topic("/car_C_rear_wheel", "std_msgs/Float32MultiArray")
                                ws_client.advertise_topic("/car_C_front_wheel", "std_msgs/Float32MultiArray")
                            else:
                                connection_error = "Connection failed"
                        input_mode = False
                        ip_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        ip_input = ip_input[:-1]
                    else:
                        ip_input += event.unicode
                else:
                    # 非輸入模式下，可按 I 進入 IP 輸入模式
                    if event.key == pygame.K_i:
                        input_mode = True
                        ip_input = ""
                    # 按 Q 斷線並結束程式
                    elif event.key == pygame.K_q:
                        ws_client.disconnect()
                        running = False

            # 非輸入模式下處理搖桿事件
            if not input_mode:
                if event.type == pygame.JOYBUTTONDOWN:
                    joystick_handler.process_button_press(
                        event.button,
                        wheel_publish_callback=lambda cmd: publish_wheel(ws_client, cmd),
                        arm_publish_callback=lambda arm_msg: ws_client.publish("/robot_arm", arm_msg)
                    )
                elif event.type == pygame.JOYAXISMOTION:
                    joystick_handler.process_axis_motion(event.axis, event.value)
                # 可根據需求擴充 JOYBUTTONUP、JOYHATMOTION 等事件

        # 根據連線狀態決定顯示文字
        connection_status = "Connected" if ws_client.ws else "Disconnected"
        ui.draw(
            joystick_handler.velocity,
            rosbridge_ip,
            connection_status,
            connection_error,
            input_mode,
            ip_input,
            joystick_handler.arm_index,
            joystick_handler.arm_angles
        )
        clock.tick(30)

    ws_client.disconnect()
    pygame.quit()

if __name__ == "__main__":
    main()
