from dataclasses import dataclass


@dataclass(frozen=True)
class WorldConfig:
    rows: int = 60
    columns: int = 90
    food_count: int = 40
