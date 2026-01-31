import wpilib as wpi
import wpimath as wmath
import wpimath.geometry as geom

import math
import numpy

def transform_to_pose(transform: geom.Transform2d):
    return geom.Pose2d(transform.translation(), transform.rotation())

class Targeting():
    def __init__(self, child_pose: geom.Pose2d = geom.Pose2d(), min_limit: float = -180.0, max_limit: float = 180.0):
        self.child_pose: geom.Pose2d = child_pose
        self.parent_pose: geom.Pose2d = geom.Pose2d()
        self.target_pose: geom.Pose2d = geom.Pose2d()

        self.min_limit: float = min_limit
        self.max_limit: float = max_limit

    def set_parent_pose(self, parent_pose):
        """
        This function should be called once every robot period to seed
        our position to the targeting class.
        """
        
        self.parent_pose = parent_pose

    def set_target_pose(self, target_pose):
        self.target_pose = target_pose

    def get_child_relative_pose(self) -> geom.Pose2d:
        # TODO implement child relative rotation
        return transform_to_pose(self.parent_pose - self.child_pose)

    def calculate_child_rotation(self):
        child_relative_pose: geom.Pose2d = self.get_child_relative_pose()

        child_to_target = transform_to_pose(self.target_pose - child_relative_pose)

        rotation = math.degrees(numpy.arctan2(child_to_target.y, child_to_target.x))

        return geom.Rotation2d.fromDegrees(float(numpy.clip(rotation, self.min_limit, self.max_limit)))