import pytest

from sneks.engine.config.base import Config


def main(test_path: str | None = None) -> int:
    if test_path is not None:
        Config(registrar_prefix=test_path)
    return pytest.main(["--pyargs", "sneks.engine.validator"])
