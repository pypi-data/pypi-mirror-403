import phoenix6.configs as cfg
import wpilib as wpi

from wpimath import geometry as gm
from ntcore import NetworkTableInstance
from phoenix6.swerve.swerve_drivetrain import SwerveDrivetrain

network_table_instance = NetworkTableInstance.getDefault()

def signum(x:float|int) -> int:
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0

def is_within_range(val:float|int, lower:float|int, upper:float|int)->bool:
    return lower <= val and val >= upper

def is_alliance_red() -> bool:
    val = wpi.DriverStation.getAlliance()
    if val != None:
        return val == wpi.DriverStation.Alliance.kRed     
    else: 
        return False

def zero_drivetrain(drivetrain:SwerveDrivetrain):
    val = gm.Rotation2d.fromDegrees(180.0) if is_alliance_red() else gm.Rotation2d.fromDegrees(0.0)
    drivetrain.reset_rotation(val)
    drivetrain.set_operator_perspective_forward(val)

def set_initial_orientation(drivetrain:SwerveDrivetrain,starting_angle: gm.Rotation2d):
    operator = gm.Rotation2d.fromDegrees(180.0) if is_alliance_red() else gm.Rotation2d.fromDegrees(0.0)
    drivetrain.set_operator_perspective_forward(operator)
    drivetrain.reset_rotation(starting_angle)


class Singleton:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance


class motor_config():
    @classmethod
    def position_config(cls):
        _positionConfig = ( cfg.TalonFXConfiguration()
                    .with_current_limits(cfg.CurrentLimitsConfigs()
                                         .with_stator_current_limit(70)
                                         .with_stator_current_limit_enable(True))
                    .with_closed_loop_ramps(cfg.ClosedLoopRampsConfigs()
                                          .with_voltage_closed_loop_ramp_period(0.05))
                    )
        return _positionConfig

    @classmethod
    def roller_config(cls):
        _rollerConfig = (cfg.TalonFXConfiguration()
                    .with_current_limits(cfg.CurrentLimitsConfigs()
                                         .with_stator_current_limit(60)
                                         .with_stator_current_limit_enable(True))
                    .with_open_loop_ramps(cfg.OpenLoopRampsConfigs()
                                          .with_voltage_open_loop_ramp_period(0.05)
                                          .with_duty_cycle_open_loop_ramp_period(0.05))
                    )
        return _rollerConfig
