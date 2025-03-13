import pygame

# 初始化 Pygame 和 Joystick
pygame.init()
pygame.joystick.init()

# 檢查是否有連接的搖桿
if pygame.joystick.get_count() == 0:
    print("未偵測到 PS5 遙控器，請確保已連接。")
    exit()

# 取得第一個連接的搖桿
joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"偵測到搖桿：{joystick.get_name()}")

# 讀取按鍵、搖桿和扳機
running = True
while running:
    pygame.event.pump()  # 更新事件

    # 讀取左搖桿
    left_x = joystick.get_axis(0)  # 左搖桿 X 軸 (-1.0 ~ 1.0)
    left_y = joystick.get_axis(1)  # 左搖桿 Y 軸 (-1.0 ~ 1.0)

    # 讀取右搖桿
    right_x = joystick.get_axis(2)  # 右搖桿 X 軸 (-1.0 ~ 1.0)
    right_y = joystick.get_axis(5)  # 右搖桿 Y 軸 (-1.0 ~ 1.0)

    # 讀取 L2/R2 扳機（0.0 ~ 1.0）
    l2 = (joystick.get_axis(3) + 1) / 2
    r2 = (joystick.get_axis(4) + 1) / 2

    # 讀取按鍵（1 = 按下, 0 = 放開）
    cross = joystick.get_button(0)
    circle = joystick.get_button(1)
    square = joystick.get_button(2)
    triangle = joystick.get_button(3)
    l1 = joystick.get_button(4)
    r1 = joystick.get_button(5)
    ps_button = joystick.get_button(12)  # PS 按鈕

    # 顯示讀取的數據
    print(f"Left Stick -> X={left_x:.2f}, Y={left_y:.2f} | Right Stick -> X={right_x:.2f}, Y={right_y:.2f}")
    print(f"L2={l2:.2f}, R2={r2:.2f} | Cross={cross}, Circle={circle}, Square={square}, Triangle={triangle}")

    # 偵測 PS 按鈕退出
    if ps_button:
        print("PS 按鈕按下，結束程式。")
        running = False

# 退出 pygame
joystick.quit()
pygame.quit()
