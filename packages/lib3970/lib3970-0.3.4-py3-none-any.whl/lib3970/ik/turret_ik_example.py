from wpimath.geometry import Transform3d, Translation3d, Rotation3d, Pose3d
from ik_3970 import Link, IKLinkChain

# Define each rigid link
robot_root = Link(
    name="robot_root",
    transform=Transform3d(
        Translation3d(0.0, 0.0, 0.0),   # 0.5m forward
        Rotation3d(0.0, 0.0, 0.0),
    ),
)

turret_one_base = Link(
    name="turret_one_base",
    transform=Transform3d(
        Translation3d(0.0, 0.0, 0.2),   # 0.4m forward
        Rotation3d(0.0, 0.0, 0.0),      # 0.5 rad yaw
    ),
)

chain = IKLinkChain(
    links=[robot_root, turret_one_base]
)

# Target point in world coordinates
hubgoal_worldspace = Translation3d(1.3, 0.2, 0.0)
robot_new_root_translation = Translation3d(0.0, 0.1, 0.0)

chain.set_base_pose_world(robot_new_root_translation)
relative_translation = chain.get_relative_rotation_tolookAt_target(hubgoal_worldspace, "turret_one_base")
