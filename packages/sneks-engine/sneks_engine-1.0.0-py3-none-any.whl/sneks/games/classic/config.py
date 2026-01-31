from dataclasses import dataclass

from sneks.engine.config.base import Config


@dataclass(frozen=True)
class ClassicConfig(Config):
    pass
