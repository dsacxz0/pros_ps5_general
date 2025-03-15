# PS5 Controller Robot Arm Project

This project allows you to control a robot using a PS5 DualSense controller. It features both wheel and arm control with a real-time graphical UI built with Pygame, and publishes ROS messages (including `trajectory_msgs/msg/JointTrajectoryPoint` for arm joints) via WebSockets.

## Features

- **Joystick Control:**
  Control robot wheels and arm joints with a PS5 controller.
- **Arm Joint Control:**
  Modify joint angles (in radians) for the robot arm with dedicated buttons.
- **Real-time UI:**
  View velocity, connection status, current arm joint index (with a red ">" indicator), and joint angles.
- **ROSBridge Communication:**
  Publish and subscribe to ROS topics over a WebSocket connection.

## File Structure

- **main.py:** Main application file handling the event loop, controller events, and UI updates.
- **joystick_handler.py:** Processes controller input, updates robot wheel commands, and publishes arm joint messages.
- **ws_client.py:** Manages the WebSocket connection to the ROSBridge server.
- **ui.py:** Implements the Pygame-based UI for displaying application data.
- **utils.py:** Contains helper functions (e.g., trigger value mapping, velocity limits).
- **README.md:** This documentation file.

## Requirements

- Python 3.12+
- A PS5 DualSense Wireless Controller
- A running ROSBridge server

## Controller Layout

## Setup

1. **Install Dependencies:**
   Install Pygame via pip:
   ```bash
   pip install -r .\requirements.txt
   ```

2. **Run ROSBridge Server:**
   Launch the ROSBridge server (adjust the command as per your ROS setup):
   ```bash
   ros2 launch rosbridge_server rosbridge_websocket_launch.xml
   ```

## Usage

1. **Start the Application:**
   ```bash
   python main.py
   ```

2. **Controlling the Robot:**
   - **Wheel Control:**
     Use designated buttons to move the robot forward, backward, turn left/right, or stop.
   - **Arm Control:**
     - **Button 1:** Change to the next joint
     - **Button 2:** Change to the previous joint
     - **Button 3:** Increase the current joint's angle by 10°
     - **Button 0:** Decrease the current joint's angle by 10°
     The arm commands are published using the ROS message type `trajectory_msgs/msg/JointTrajectoryPoint`.

3. **IP Input Mode:**
   - Press `I` to enter IP input mode for setting the ROSBridge server IP.
   - Press `Q` to disconnect and quit the application.

## Customization

- **Adjusting Arm Joints:**
  Set the number of joints by modifying the initialization in `JoystickHandler` or via the `set_joint_count()` function.

- **UI Customization:**
  Modify text, colors, or layout in `ui.py` to suit your design needs.

## Troubleshooting

- **Missing UI Indicator:**
  Ensure that the `arm_index` and `arm_angles` values are correctly updated and passed into `ui.draw()`.
- **ROS Connection Errors:**
  Check your ROSBridge server status and confirm the IP and port settings.

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests for improvements or bug fixes.
