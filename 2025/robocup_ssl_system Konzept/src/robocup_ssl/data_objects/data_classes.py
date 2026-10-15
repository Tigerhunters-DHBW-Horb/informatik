from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional



# 0. SERIALISIERUNG (ZeroMQ-Transport)

class SerializableMixin:
    """Gemeinsame (De-)Serialisierung fuer alle systemweiten Dataclasses."""


# 1. RAW INPUTS (VON DEN PARSERN)

@dataclass
class VisionRobot(SerializableMixin): # Vision Daten
    robot_id: int
    x: float
    y: float
    orientation: float
    confidence: float = 1.0 

@dataclass
class RawVisionFrame(SerializableMixin):
    """Output von vision_parser.py -> Input für world_model.py"""
    t_capture: float
    camera_id: int
    balls: List[Dict[str, float]]
    blue_robots: List[VisionRobot]
    yellow_robots: List[VisionRobot]

@dataclass
class RawReferee(SerializableMixin):
    """Output von referee_parser.py -> Input für strategy_engine.py"""
    command: str
    stage: str
    time_remaining: float
    blue_score: int
    yellow_score: int
    designated_position: Optional[tuple[float, float]] = None

@dataclass
class RobotTelemetry(SerializableMixin):
    """Output von robots_parser.py -> Input für world_model.py"""
    robot_id: int
    timestamp: float = field(default_factory=time.time)
    has_ball: bool = False
    battery_level: float = 100.0
    v_x: Optional[float] = None
    v_y: Optional[float] = None
    omega: Optional[float] = None


# 2. STATE OBJECTS

@dataclass
class FilteredObject(SerializableMixin):
    """Sub-Klasse für WorldState"""
    x: float
    y: float
    v_x: float
    v_y: float
    angle: Optional[float] = None
    v_angle: Optional[float] = None
    confidence: float = 1.0

@dataclass
class WorldState(SerializableMixin):
    """Output von world_model.py -> Input für Strategy, Pathfinding, GUI"""
    timestamp: float
    ball: FilteredObject
    our_robots: Dict[int, FilteredObject] = field(default_factory=dict)
    opp_robots: Dict[int, FilteredObject] = field(default_factory=dict)
    
    
    field_length: Optional[float] = None  
    field_width: Optional[float] = None

@dataclass
class SystemState(SerializableMixin):
    """Output von system_manager.py -> Input für Strategy, Dispatcher, GUI"""
    mode: str = "AUTONOMOUS"     # "AUTONOMOUS", "MANUAL_JOYPAD", "EMERGENCY_STOP"
    vision_alive: bool = True
    referee_alive: bool = False
    active_joypad_robot: Optional[int] = None


# 3. STRATEGY & INTENTS

@dataclass
class RobotIntent(SerializableMixin):
    """Output von skills.py -> Input für path_planner.py"""
    robot_id: int
    priority: int
    skill_name: str
    
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    target_angle: Optional[float] = None
    
    target_v_x: float = 0.0
    target_v_y: float = 0.0
    
    kick_power: float = 0.0
    kick_type: str = "FLAT"
    dribbler_active: bool = False
    
    max_speed_override: Optional[float] = None 


# 4. HARDWARE COMMANDS

@dataclass
class HardwareCommand(SerializableMixin):
    """Output von path_planner.py -> Input für robot_dispatcher.py"""
    robot_id: int
    
    v_t: float                   # Translation (vor/zurück) in m/s
    v_o: float                   # Orthogonal (links/rechts) in m/s
    omega: float                 # Rotation (Drehung um eigene Achse) in rad/s

    kicker_power: float = 0.0
    kicker_type: str = "FLAT"
    dribbler_speed: float = 0.0