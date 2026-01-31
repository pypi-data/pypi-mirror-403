import bisect
import wpimath.geometry as gm

class InterpolatingFloatMap:
    def __init__(self, x_pts: list[float], y_pts: list[float]):
        x_pts = x_pts.copy()
        y_pts = y_pts.copy()

        if x_pts[0] > x_pts[-1]:
            x_pts.reverse()
            y_pts.reverse()

        self.x_pts: list[float] = x_pts
        self.y_pts: list[float] = y_pts

        self.x_max:float = self.x_pts[-1]
        self.x_min:float = self.x_pts[ 0]

    def interpolate(self, x:float, x_left:float, x_right:float, y_left:float, y_right:float) -> float:
        x_span = x_right - x_left
        y_span = y_right - y_left
        
        percent = (x-x_left)/x_span

        return y_left + y_span*percent

    def get(self, x:float)->float:
        i = bisect.bisect_left(self.x_pts, x)
        if x >= self.x_max:
            return self.y_pts[-1]

        if x <= self.x_min:
            return self.y_pts[0]

        return self.interpolate(x,self.x_pts[i-1], self.x_pts[i], self.y_pts[i-1], self.y_pts[i])

class InterpolatingRotation2dMap:
    def __init__(self, x_pts: list[float], y_pts: list[gm.Rotation2d]):
        x_pts = x_pts.copy()
        y_pts = y_pts.copy()

        if x_pts[0] > x_pts[-1]:
            x_pts.reverse()
            y_pts.reverse()

        self.x_pts: list[float] = x_pts
        self.y_pts: list[gm.Rotation2d] = y_pts

        self.x_max:float = self.x_pts[-1]
        self.x_min:float = self.x_pts[ 0]

    def interpolate(self, x:float, x_left:float, x_right:float, y_left:gm.Rotation2d, y_right:gm.Rotation2d) -> gm.Rotation2d:
        x_span = x_right - x_left 

        # Fraction along x-axis
        percent = (x - x_left) / x_span

        # Compute rotation from left to right
        delta = (y_right-y_left)

        # Rotate left by fraction of delta
        return y_left.rotateBy(gm.Rotation2d(delta.radians() * percent))

    def get(self, x:float)->gm.Rotation2d:
        i = bisect.bisect_left(self.x_pts, x)

        if x >= self.x_max:
            return self.y_pts[-1]

        if x <= self.x_min:
            return self.y_pts[0]

        return self.interpolate(x, self.x_pts[i-1], self.x_pts[i], self.y_pts[i-1], self.y_pts[i])
