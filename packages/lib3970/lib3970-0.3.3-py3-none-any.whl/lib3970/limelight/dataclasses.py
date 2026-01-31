import wpimath.geometry as geom

from dataclasses import dataclass, field

@dataclass
class RawFiducial:
    id: int = 0
    txnc: float = 0.0
    tync: float = 0.0
    ta: float = 0.0
    dist_to_camera: float = 0.0
    dist_to_robot: float = 0.0
    ambiguity: float = 0.0

    def __eq__(self, other):
        if self is other:
            return True
        if type(other) is not RawFiducial:
            return False

        return (
            self.id == other.id and
            self.txnc == other.txnc and
            self.tync == other.tync and
            self.ta == other.ta and
            self.dist_to_camera == other.dist_to_camera and
            self.dist_to_robot == other.dist_to_robot and
            self.ambiguity == other.ambiguity
        )

@dataclass
class PoseEstimate:
    pose: geom.Pose2d = field(default_factory=geom.Pose2d)
    timestamp_seconds: float = 0.0
    latency: float = 0.0
    tag_count: int = 0
    tag_span: float = 0.0
    avg_tag_dist: float = 0.0
    avg_tag_area: float = 0.0
    raw_fiducials: list[RawFiducial] = field(default_factory=list)
    is_mega_tag_2: bool = False

    def __eq__(self, other):
        if self is other:
            return True
        if type(other) is not PoseEstimate:
            return False

        # timestampSeconds intentionally excluded
        return (
            self.latency == other.latency and
            self.tag_count == other.tag_count and
            self.tag_span == other.tag_span and
            self.avg_tag_dist == other.avg_tag_dist and
            self.avg_tag_area == other.avg_tag_area and
            self.pose == other.pose and
            self.raw_fiducials == other.raw_fiducials
        )

