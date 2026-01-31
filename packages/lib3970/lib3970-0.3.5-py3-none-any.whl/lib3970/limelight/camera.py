import wpimath.geometry as geom

from ntcore import NetworkTableInstance,  NetworkTableEntry, NetworkTable

from lib3970.limelight import RawFiducial, PoseEstimate

class Camera():
    nt_instance:NetworkTableInstance = NetworkTableInstance.getDefault()

    def __init__(self, name:str):
        """
        Creates a limelight with the given name.  Provides acess to a number
        of helper methods for accesing camera data and setting camera controls
        """
        self.name:str = name
        self.table:NetworkTable = self.nt_instance.getTable("limelight-" + self.name)

        self.entries:dict[str,NetworkTableEntry] = dict()

        self.make_entries()
        self.update_vals()

    def make_entries(self):
        """
        Makes a NetworkTableEntry for most commonly used camera properties.
        """
        #Simple Targeting Entries
        self.entries["tx"] = self.table.getEntry("tx")
        self.entries["ty"] = self.table.getEntry("ty")
        self.entries["ta"] = self.table.getEntry("ta")
        self.entries["tv"] = self.table.getEntry("tv")

        #AprilTag Info
        self.entries["target_to_cam"] = self.table.getEntry("camerapose_targetspace")
        self.entries["tid"] = self.table.getEntry("tid")
        self.entries["priority_id"] = self.table.getEntry("priorityid")
        self.entries["id_filter_localization"] = self.table.getEntry("fiducial_id_filters_set")

        #Megatag 2 Localization Entries
        self.entries["orientation"] = self.table.getEntry("robot_orientation_set")
        self.entries["field_pos"] =  self.table.getEntry("botpose_orb_wpiblue")
        self.entries["imu_mode"] = self.table.getEntry("imumode_set")

    def update_vals(self):
        """
        Gets the most commonly used values from the camera.  These are 
        tx, ty, ta, tv: double
        target_to_cam: the position of the camera relative to the tag.
        field_pos: a PoseEstimate
        """
        self.tx:float = self.entries["tx"].getDouble(0)
        self.ty:float = self.entries["tx"].getDouble(0)
        self.ta:float = self.entries["tx"].getDouble(0)
        self.tv:float = self.entries["tx"].getDouble(0)

        self.target_to_cam:list[float] = self.entries["target_to_cam"].getDoubleArray([0,0,0,0,0,0])
        self.field_pos:PoseEstimate|None = self.get_field_pos()

    def set_robot_orientation(self, yaw: float) -> None:
        orientation_values = [yaw, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.entries["orientation"].setDoubleArray(orientation_values) # type: ignore

    def set_imu_mode(self, mode:float):
        """
        Sets the imu mode for the camera.  Flush should generally be called
        after this method. During disabled this should normally be mode 1. 
        While enabled, mode 2 should be used (do this in the teleop and auto
        init functions).
        IMU Modes:
            0 - use external imu 
            1 - use external imu, seed internal imu 
            2 - use internal 
            3 - use internal with MT1 assisted convergence
            4 - use internal IMU with external IMU assisted convergence
        """
        _ = self.entries["imu_mode"].setDouble(mode)

    def get_field_pos(self) -> PoseEstimate | None:
        
        # ll_pose is in the below format:
        # 
        # X, Y, Z, Roll, Pitch, Yaw, total latency (cl+tl), tag count, tag span,
        # average tag distance from camera, average tag area
        
        ll_pose:list[float] = self.entries["field_pos"].getDoubleArray([]) 
        ts = self.entries["field_pos"].getLastChange()

        if not ll_pose: #return none if there is no available pose
            return None
        
        bot_pose = self.ll_to_bot(ll_pose)
        latency   = self.get_index_or_default( 6, ll_pose)
        tag_count = self.get_index_or_default( 7, ll_pose)
        tag_span  = self.get_index_or_default( 8, ll_pose)
        tag_dist  = self.get_index_or_default( 9, ll_pose)
        tag_area  = self.get_index_or_default(10, ll_pose)

        adjustedTimestamp = (ts / 1000000.0) - (latency / 1000.0)

        raw_fiducials = []
        vals_per_fiducial = 7
        expected_total_vals = 11 + tag_count * vals_per_fiducial

        if len(ll_pose) >= 11:
            for i in range(int(tag_count)):
                base = 11 + i * vals_per_fiducial
                fid = RawFiducial(
                    id=int(self.get_index_or_default(base, ll_pose)),
                    txnc=self.get_index_or_default(base + 1, ll_pose),
                    tync=self.get_index_or_default(base + 2, ll_pose),
                    ta=self.get_index_or_default(base + 3, ll_pose),
                    dist_to_camera=self.get_index_or_default(base + 4, ll_pose),
                    dist_to_robot=self.get_index_or_default(base + 5, ll_pose),
                    ambiguity=self.get_index_or_default(base + 6, ll_pose),
                )
                raw_fiducials.append(fid)

        return PoseEstimate(
            pose=bot_pose, 
            timestamp_seconds=adjustedTimestamp, 
            latency=latency, 
            tag_count=tag_count,
            tag_span=tag_span,
            avg_tag_dist=tag_dist,
            avg_tag_area=tag_area,
            raw_fiducials=raw_fiducials,
            is_mega_tag_2=True
        )
        

    def ll_to_bot(self, ll_pose)->geom.Pose2d:
        """
        Takes in the robot's pose from a limelight and returns it as a wpilib
        pose2d object.
        """
        translation_2d = geom.Translation2d(ll_pose[0], ll_pose[1])
        rotation_2d = geom.Rotation2d.fromDegrees(ll_pose[5])

        return geom.Pose2d(translation_2d, rotation_2d)

    def get_index_or_default(self, index:int, l:list, default = 0):
        if 0 <= index < len(l):
            return l[index]
        else:
            return default
 
