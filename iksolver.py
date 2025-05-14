import pybullet as p
import pybullet_data
import xml.etree.ElementTree as ET
import math
import time

class IKSolver:
    def __init__(self, urdf_path, initial_joint_angles_deg,
                 end_effector_index, blend_factor=0.5,
                 max_step_deg=None, min_step_deg=None):
        """
        urdf_path: path to robot file
        initial_joint_angles_deg: list of start angles (degrees)
        blend_factor: fraction of full IK delta to move each update
        max_step_deg: maximum allowed joint change per update (degrees)
        min_step_deg: below this total delta, snap directly to target
        """
        self.urdf_path = urdf_path
        self.end_effector_index = end_effector_index
        self.blend = blend_factor
        self.max_step_deg = max_step_deg
        self.min_step_deg = min_step_deg

      
        self.goals = None

        # connect to physics
        self.physics_client = p.connect(p.GUI)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())

        # load robot with base offset
        self.base_offset = self._get_inertial_offset(urdf_path)
        self.robot_id = p.loadURDF(
            urdf_path,
            basePosition=self.base_offset,
            baseOrientation=p.getQuaternionFromEuler([0, 0, 0]),
            useFixedBase=True
        )

        # fetch joint limits
        self.num_joints = p.getNumJoints(self.robot_id)
        self.joint_lower_limits = []
        self.joint_upper_limits = []
        self.joint_ranges = []
        for i in range(self.num_joints):
            info = p.getJointInfo(self.robot_id, i)
            if info[2] in [p.JOINT_REVOLUTE, p.JOINT_PRISMATIC]:
                self.joint_lower_limits.append(info[8])
                self.joint_upper_limits.append(info[9])
                self.joint_ranges.append(info[9] - info[8])
            else:
                self.joint_lower_limits.append(0)
                self.joint_upper_limits.append(0)
                self.joint_ranges.append(0)

        # set initial state
        radians = [math.radians(d) for d in initial_joint_angles_deg]
        for i, ang in enumerate(radians):
            p.resetJointState(self.robot_id, i, ang)
        self.prev_joint_angles = list(radians)

        # initial target = current end-effector pose
        link_state = p.getLinkState(self.robot_id, self.end_effector_index,
                                    computeForwardKinematics=True)
        self.target_pos = list(link_state[4])

    def _get_inertial_offset(self, urdf_path):
        tree = ET.parse(urdf_path)
        root = tree.getroot()
        for link in root.findall("link"):
            if link.attrib.get("name") == "base_link":
                inertial = link.find("inertial")
                if inertial is not None:
                    origin = inertial.find("origin")
                    if origin is not None and origin.attrib.get("xyz"):
                        return [-float(x) for x in origin.attrib["xyz"].split()]
        return [0, 0, 0]

    def solve(self, dx, dy, dz):
        """
        Set a new absolute target offset from current end-effector pose.
        """
        state = p.getLinkState(self.robot_id, self.end_effector_index,
                               computeForwardKinematics=True)
        current = list(state[4])
        self.target_pos = [current[0] + dx,
                           current[1] + dy,
                           current[2] + dz]
        self.goals = p.calculateInverseKinematics(
                self.robot_id,
                self.end_effector_index,
                targetPosition=self.target_pos,
                lowerLimits=self.joint_lower_limits,
                upperLimits=self.joint_upper_limits,
                jointRanges=self.joint_ranges,
                restPoses=self.prev_joint_angles,
                residualThreshold=1e-4,
                maxNumIterations=200
            )
        
    def set_joint_targets(self, target_angles_deg):
        """
        Set direct joint-angle targets (degrees) and switch to joint mode.
        """
        # convert to radians and store
        self.goals = [math.radians(d) for d in target_angles_deg]

    def update(self):
        """
        Compute IK and move joints by a fraction of the full delta (blend_factor),
        but snap to target if total move less than min_step_deg, and cap per-step
        by max_step_deg if set.
        Call each simulation frame.
        """
        if self.goals is None:
            state = p.getLinkState(self.robot_id, self.end_effector_index,
                               computeForwardKinematics=True)
            current = list(state[4])
            return current

        # compute per-joint deltas (radians)
        deltas = [goal - prev for goal, prev in zip(self.goals, self.prev_joint_angles)]
        # convert to degrees for magnitude checks
        deg_deltas = [abs(d * 180.0 / math.pi) for d in deltas]
        max_deg = max(deg_deltas) if deg_deltas else 0

        # decide fraction
        # snap to target if small move requested
        if self.min_step_deg is not None and max_deg < self.min_step_deg:
            fraction = 1.0
        else:
            fraction = self.blend
            # enforce max step if set
            if self.max_step_deg is not None and max_deg > self.max_step_deg:
                max_frac = self.max_step_deg / max_deg
                fraction = min(fraction, max_frac)

        # apply motion
        new_angles = []
        for i, (prev, delta) in enumerate(zip(self.prev_joint_angles, deltas)):
            step = prev + delta * fraction
            new_angles.append(step)
            p.setJointMotorControl2(
                self.robot_id, i, p.POSITION_CONTROL,
                targetPosition=step
            )

        # advance simulation
        p.stepSimulation()
        self.prev_joint_angles = new_angles

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

        # return current position
        return new_angles

