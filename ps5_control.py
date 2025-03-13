import pygame

def handle_button_press(button):
    print(f"Button {button} pressed")

def handle_button_release(button):
    print(f"Button {button} released")

def handle_axis_motion(axis, value):
    pass
    # print(f"Axis {axis} moved to {value}")

def handle_hat_motion(hat, value):
    print(f"D-pad {hat} moved to {value}")

def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No joystick detected.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Detected Joystick: {joystick.get_name()}")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.JOYBUTTONDOWN:
                handle_button_press(event.button)
            elif event.type == pygame.JOYBUTTONUP:
                handle_button_release(event.button)
            elif event.type == pygame.JOYAXISMOTION:
                handle_axis_motion(event.axis, event.value)
            elif event.type == pygame.JOYHATMOTION:
                handle_hat_motion(event.hat, event.value)

    pygame.quit()

if __name__ == "__main__":
    main()