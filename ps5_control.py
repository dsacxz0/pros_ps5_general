import pygame

class PS5Controller:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("No joystick detected.")
            self.joystick = None
            return

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        print(f"Detected Joystick: {self.joystick.get_name()}")

    def handle_button_press(self, button):
        print(f"Button {button} pressed")

    def handle_button_release(self, button):
        print(f"Button {button} released")

    def handle_axis_motion(self, axis, value):
        # R2 and L2 triggers
        if axis in [2, 5]:
            print(f"Trigger {axis} moved to {value}")
        else:
            pass
            # print(f"Axis {axis} moved to {value}")

    def handle_hat_motion(self, hat, value):
        print(f"D-pad {hat} moved to {value}")

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

        pygame.quit()

if __name__ == "__main__":
    controller = PS5Controller()
    controller.run()