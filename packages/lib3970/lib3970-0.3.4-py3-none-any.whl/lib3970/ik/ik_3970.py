from typing import Sequence, Union, Tuple
import numpy as np
from wpimath.geometry import (
    Pose2d,
    Pose3d,
    Rotation2d,
    Rotation3d,
    Transform3d,
    Translation2d,
    Translation3d,
)

"""
ik_3970 union of data types to allow for changes between each type.
"""
WorldPose3dLike = Union[
    Pose3d,
    Transform3d,
    np.ndarray,
    Tuple[float, float, float],
    Tuple[float, float, float, float, float, float],
]


"""
ik_3970 helper functions
"""

def _to_pose3d(x: WorldPose3dLike) -> Pose3d:
    """
    A helper function to generate a pose3d from all types listed:
    Translation3d
    Pose3d
    Transform3d
    """
    if isinstance(x, Translation3d):
        return Pose3d(x, Rotation3d())

    if isinstance(x, Pose3d):
        return x

    if isinstance(x, Transform3d):
        return Pose3d().transformBy(x)

    raise TypeError(f"Unsupported world pose type: {type(x)}")

"""
ik_3970 classes
"""

class Link:
    """
    A rigid linkage in a kinematic chain.

    Attributes:
        name (str): Name of the link/frame
        transform (Transform3d): Transform from parent frame to this link's frame
    """

    def __init__(self, name: str, transform: Transform3d):
        self.name = name
        self.transform = transform

    def __repr__(self) -> str:
        return f"Link(name={self.name}, transform={self.transform})"

class IKLinkChain:
    """
    Forward-kinematic chain with named links.

    Frame convention:
      World → Base → Link1 → Link2 → ... → End Effector
    """

    def __init__(
        self,
        links: Sequence[Link],
        base_pose_world: Pose3d = Pose3d(),
    ):
        self.links = list(links)
        self.base_pose_world = base_pose_world
        

    # ---------- Base / Root ----------

    def set_base_pose_world(self, new_base_pose: Pose3d):
        """
        Set the robot root (base) pose in world coordinates.
        """
        self.base_pose_world = new_base_pose

    def get_base_pose_world(self) -> Pose3d:
        """
        Get the robot root (base) pose in world coordinates.
        """
        return self.base_pose_world

    # ---------- Forward Kinematics ----------

    def pose_of(self, link_name: str) -> Pose3d:
        """
        Return the world pose of the specified link.
        """
        pose = self.base_pose_world

        for link in self.links:
            pose = pose.transformBy(link.transform)
            if link.name == link_name:
                return pose

        raise KeyError(f"Link '{link_name}' not found")

    def get_world_pose(self, link_name: str) -> Pose3d:
        """
        Return the world pose of the specified link.
        """
        pose = self.base_pose_world

        for link in self.links:
            pose = pose.transformBy(link.transform)
            if link.name == link_name:
                return pose

        raise KeyError(f"Link '{link_name}' not found")

    # ---------- Relative Transform ----------

    def get_relative_transform(
        self,
        world_target: WorldPose3dLike,
        relative_to: str,
    ) -> Transform3d:
        """
        Express `world_target` in the frame of `relative_to`.

        If relative_to is None, uses the end effector frame.
        """
        target_pose_w = _to_pose3d(world_target)

        reference_pose_w = self.pose_of(relative_to)

        return Transform3d(reference_pose_w, target_pose_w)

    # ---------- Relative Rotation to Look at Target ----------

    def get_relative_rotation_tolookAt_target_yaw_only(
        self,
        world_target: WorldPose3dLike,
        relative_to: str,
    ) -> Rotation2d:
        """
        Returns a Rotation2d in the reference frame (end effector by default)
        that would rotate the reference frame to "look at" the target.

        - Forward axis assumed +X
        - Up axis assumed +Z
        - world_up defaults to +Z
        """
        target_pose_w = _to_pose3d(world_target)
        reference_pose_w = self.pose_of(relative_to)

        # Target in reference frame: ^Ref T_Target
        rel_tf = Transform3d(reference_pose_w, target_pose_w)

        target_relative_pose: Pose2d = Pose2d(Translation2d(rel_tf.translation().x, rel_tf.translation().y), Rotation2d(rel_tf.rotation().Z))

        rotation = target_relative_pose.degrees(np.arctan2(target_relative_pose.y, target_relative_pose.x))

        return Rotation2d.fromDegrees(float(np.clip(rotation, self.min_limit, self.max_limit)))