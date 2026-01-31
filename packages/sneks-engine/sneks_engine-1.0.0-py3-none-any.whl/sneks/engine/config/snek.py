from dataclasses import dataclass

from sneks.engine.core.bearing import Bearing


@dataclass(frozen=True)
class SnekConfig:
    vision_range: int = 20
    directional_speed_limit: int = 1
    combined_speed_limit: int = 1
    idle_allowed: bool = False
    initial_bearing: Bearing = Bearing(0, 1)
    respawn: bool = False
