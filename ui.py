# ui.py
import pygame
import math

class UI:
    def __init__(self):
        pygame.font.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("PS5 Controller UI")
        self.font = pygame.font.SysFont("Arial", 24)

    def draw(self, velocity, rosbridge_ip, connection_status, connection_error, input_mode, ip_input, arm_index, arm_angles):
        self.screen.fill((0, 0, 0))

        # 顯示速度
        velocity_text = self.font.render(f"Velocity: {velocity}", True, (255, 255, 255))
        self.screen.blit(velocity_text, (10, 10))

        # 顯示連線資訊
        connection_text = self.font.render(f"ROSBridge ({rosbridge_ip}): {connection_status}", True, (255, 255, 255))
        self.screen.blit(connection_text, (10, 40))

        # 顯示錯誤訊息（若有）
        if connection_error:
            error_text = self.font.render(f"Error: {connection_error}", True, (255, 0, 0))
            self.screen.blit(error_text, (10, 70))

        # 輸入模式提示
        if input_mode:
            ip_input_text = self.font.render(f"Enter IP: {ip_input}", True, (255, 255, 255))
            self.screen.blit(ip_input_text, (10, 100))
        else:
            mode_text = self.font.render("Press 'I' to change IP, 'Q' to quit", True, (255, 255, 255))
            self.screen.blit(mode_text, (10, 100))

        # 顯示當前手臂索引
        index_text = self.font.render(f"Current Arm Index: {arm_index}", True, (255, 255, 255))
        self.screen.blit(index_text, (10, 140))

        # 顯示各關節角度，並用顏色及符號指示當前索引
        start_y = 180
        for i, angle in enumerate(arm_angles):
            if i == arm_index:
                # 當前索引用紅色與 "> " 指示
                angle_text = self.font.render(
                    f"> Joint {i}: {math.degrees(angle):.2f}°",
                    True,
                    (255, 0, 0)
                )
            else:
                angle_text = self.font.render(
                    f"  Joint {i}: {math.degrees(angle):.2f}°",
                    True,
                    (255, 255, 255)
                )
            self.screen.blit(angle_text, (10, start_y + i * 30))

        pygame.display.flip()
