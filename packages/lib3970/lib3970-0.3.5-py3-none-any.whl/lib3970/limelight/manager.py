import ntcore

import wpimath.geometry as geom

from ntcore import NetworkTableInstance
from lib3970.limelight.camera import Camera
from typing import ClassVar

class Manager():
    nt_instance:NetworkTableInstance = ntcore.NetworkTableInstance.getDefault()

    def __init__(self, name_camera_pair:list[tuple[str, Camera]]):
        self.camera_list:dict[str, Camera] = dict(name_camera_pair)

    def set_all_imu_modes(self, mode:float) -> None:
        """
        Sets the imu mode for all cameras.  Flush should generally be called
        after this method. During disabled this should normally be mode 1. 
        While enabled, mode 2 should be used.
        IMU Modes:
            0 - use external imu 
            1 - use external imu, seed internal imu 
            2 - use internal 
            3 - use internal with MT1 assisted convergence
            4 - use internal IMU with external IMU assisted convergence
        """
        cam:Camera
        for cam in self.camera_list.values():
            cam.set_imu_mode(mode)

    def set_all_orientations(self, yaw:float) -> None:
        """
        Sends the current robot orientation (yaw, in degrees) to all limelights.
        Flush should generally be called after this method.  Update all should
        be called after the flush where relevant.
        """
        cam:Camera
        for cam in self.camera_list.values():
            cam.set_robot_orientation(yaw)

    def update_all(self) -> None:
        """
        Updates camera properties.
        tx, ty, ta, tv
        target_to_cam: the position of the camera realtive to the target
        field_pose: The robots pose on the field as estimated by the camera
        """
        cam:Camera
        for cam in self.camera_list.values():
            cam.update_vals()

    def get_valid_poses(self, rot_rate:float=0, rot_rate_limit:float = 360) -> list[tuple[geom.Pose2d, float]] | None:
        """
        Returns a list of (pose2d, timestamp) tuples if any are availaible.  Optionally 
        takes in the current rotational rate of the robot, and a rot rate limit (ie. if 
        the robot is turning faster then the limit, it returns none).
        """
        if rot_rate > rot_rate_limit:
            return None

        valid_list: list[tuple[geom.Pose2d, float]] = []
        cam:Camera
        for cam in self.camera_list.values():
            if cam.field_pos != None:
                if not cam.field_pos.tag_count == 0:
                    valid_list.append((cam.field_pos.pose, cam.field_pos.timestamp_seconds))

        return valid_list if (valid_list) else None # Returns the list if it is not empty

    def flush(self):
        """
        Immediately sends any Network table entries that are currently staged.
        This should be called after important setting changes and Localization
        settings.
        """
        self.nt_instance.flush()


    _instance:ClassVar["Manager|None"] = None 

    @classmethod
    def get_instance(cls, name_camera_pair:list[tuple[str,Camera]]|None = None) -> "Manager":
        """
        Gets an instance of the manager class.  The first time this method is run in 
        your code a list of (name, Camera) tuples should be passed in.  Every subsequent
        time you may call this function with no arguments (if any are passed it will be ignored).
        """
        if cls._instance is None:
            assert name_camera_pair != None
            cls._instance = Manager(name_camera_pair)

        return cls._instance


