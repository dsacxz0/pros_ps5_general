import pybullet as p
import pybullet_data
import xml.etree.ElementTree as ET
import math
import time


class IKSolver:
    def __init__(self, urdf_path, initial_joint_angles_deg, end_effector_index=3):
        self.urdf_path = urdf_path
        self.end_effector_index = end_effector_index

        self.physics_client = p.connect(p.GUI)  # use DIRECT for headless
        p.setAdditionalSearchPath(pybullet_data.getDataPath())

        self.base_offset = self._get_inertial_offset(urdf_path)

        self.robot_id = p.loadURDF(
            urdf_path,
            basePosition=self.base_offset,
            baseOrientation=p.getQuaternionFromEuler([0, 0, 0]),
            useFixedBase=True
        )

        self.num_joints = p.getNumJoints(self.robot_id)

        self.joint_lower_limits = []
        self.joint_upper_limits = []
        self.joint_ranges = []
        self.prev_joint_angles = []

        for i in range(self.num_joints):
            info = p.getJointInfo(self.robot_id, i)
            joint_type = info[2]

            if joint_type in [p.JOINT_REVOLUTE, p.JOINT_PRISMATIC]:
                self.joint_lower_limits.append(info[8])
                self.joint_upper_limits.append(info[9])
                self.joint_ranges.append(info[9] - info[8])
            else:
                self.joint_lower_limits.append(0)
                self.joint_upper_limits.append(0)
                self.joint_ranges.append(0)

        # Set initial joint positions
        initial_angles_rad = [math.radians(deg) for deg in initial_joint_angles_deg]
        for i, angle in enumerate(initial_angles_rad):
            p.resetJointState(self.robot_id, i, angle)
            self.prev_joint_angles.append(angle)

        # Get starting pose for offset reference
        state = p.getLinkState(self.robot_id, self.end_effector_index, computeForwardKinematics=True)
        self.initial_pos = list(state[4])
        self.initial_orn = state[5]  # orientation quaternion

    def _get_inertial_offset(self, urdf_path):
        tree = ET.parse(urdf_path)
        root = tree.getroot()
        for link in root.findall("link"):
            if link.attrib["name"] == "base_link":
                inertial = link.find("inertial")
                if inertial is not None:
                    origin = inertial.find("origin")
                    if origin is not None and "xyz" in origin.attrib:
                        return [-float(x) for x in origin.attrib["xyz"].split()]
        return [0, 0, 0]

    def solve(self, dx, dy, dz):
        # Get the current end effector pose
        state = p.getLinkState(self.robot_id, self.end_effector_index, computeForwardKinematics=True)
        current_pos = list(state[4])
        print(f"End effector position: x={current_pos[0]:.3f}, y={current_pos[1]:.3f}, z={current_pos[2]:.3f}")

        # Apply offsets to current position
        target_pos = [
            current_pos[0] + dx,
            current_pos[1] + dy,
            current_pos[2] + dz
        ]

        # print(f"Target position: {target_pos}")


        # Solve IK from current pose toward new target
        joint_angles = p.calculateInverseKinematics(
            self.robot_id,
            self.end_effector_index,
            targetPosition=target_pos,
            lowerLimits=self.joint_lower_limits,
            upperLimits=self.joint_upper_limits,
            jointRanges=self.joint_ranges,
            restPoses=self.prev_joint_angles,
            residualThreshold=1e-4,
            maxNumIterations=200
        )

        for i, angle in enumerate(joint_angles):
            p.setJointMotorControl2(self.robot_id, i, p.POSITION_CONTROL, targetPosition=angle)

        p.stepSimulation()


        # print("\n=== Joint Information ===")
        # for i in range(self.num_joints):
        #     info = p.getJointInfo(self.robot_id, i)
        #     joint_name = info[1].decode("utf-8")
        #     joint_type = info[2]
        #     lower = info[8]
        #     upper = info[9]
        #     joint_type_name = {p.JOINT_REVOLUTE: "Revolute", p.JOINT_PRISMATIC: "Prismatic"}.get(joint_type, "Fixed/Other")

        #     state = p.getJointState(self.robot_id, i)
        #     current_position = state[0]

        #     if i <= self.end_effector_index:
        #         print(f"Joint {i} ({joint_name}):")
        #         print(f"  Type         : {joint_type_name}")
        #         if joint_type in [p.JOINT_REVOLUTE, p.JOINT_PRISMATIC]:
        #             print(f"  Lower Limit  : {lower:.3f}")
        #             print(f"  Upper Limit  : {upper:.3f}")
        #         else:
        #             print("  Limits       : N/A")
        #         print(f"  Current Pos  : {current_position:.3f}")

        self.prev_joint_angles = joint_angles
        return joint_angles

