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
        # 顯示目前速度
        velocity_text = self.font.render(f"Velocity: {velocity}", True, (255, 255, 255))
        self.screen.blit(velocity_text, (10, 10))
        # 顯示 rosbridge 連線狀態與 IP
        connection_text = self.font.render(f"ROSBridge ({rosbridge_ip}): {connection_status}", True, (255, 255, 255))
        self.screen.blit(connection_text, (10, 40))
        # 顯示連線錯誤訊息（若有）
        if connection_error:
            error_text = self.font.render(f"Error: {connection_error}", True, (255, 0, 0))
            self.screen.blit(error_text, (10, 70))
        # 輸入模式下提示使用者輸入新 IP
        if input_mode:
            input_box = self.font.render(f"Enter new ROSBridge IP: {ip_input}", True, (0, 255, 0))
            self.screen.blit(input_box, (10, 100))
        else:
            instructions = self.font.render("Press 'I' to input new IP, 'Q' to disconnect", True, (255, 255, 0))
            self.screen.blit(instructions, (10, 100))

        # 顯示當前手臂索引
        index_text = self.font.render(f"Arm Index: {arm_index}", True, (255, 255, 255))
        self.screen.blit(index_text, (10, 130))

        # 顯示各關節角度（轉為度數）
        for i, angle in enumerate(arm_angles):
            angle_text = self.font.render(f"Joint {i} Angle: {math.degrees(angle):.2f}", True, (255, 255, 255))
            self.screen.blit(angle_text, (10, 160 + i * 30))

        pygame.display.flip()
