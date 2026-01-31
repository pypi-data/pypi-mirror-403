# type: ignore
import os
import pathlib
import subprocess
import uuid

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
try:
    import pygame.image
    from pygame import Surface
except ModuleNotFoundError:
    pygame = object

from sneks.engine.config.base import Config


class Recorder:
    def __init__(self) -> None:
        if not Config().graphics.record:
            return

        self.identifier = uuid.uuid4()
        self.i = 0
        self.prefix = pathlib.Path(Config().graphics.record_prefix)
        self.prefix.mkdir(exist_ok=True)
        (self.prefix / "pics").mkdir(exist_ok=True)
        (self.prefix / "movies").mkdir(exist_ok=True)

    def reset(self) -> None:
        self.identifier = uuid.uuid4()
        self.i = 0

    def record_frame(self, screen: Surface) -> None:
        if not Config().graphics.record:
            return

        pygame.image.save(
            screen,
            str(self.prefix / "pics" / f"pic_{self.identifier}_{self.i:04d}.png"),
        )
        self.i += 1

    def animate_game(self) -> None:
        if not Config().graphics.record:
            return

        import imageio_ffmpeg

        args = [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-framerate",
            f"{Config().graphics.record_fps}",
            "-i",
            str(self.prefix / "pics" / f"pic_{self.identifier}_%04d.png"),
            "-vcodec",
            "libx264",
            "-preset",
            "veryslow",
            "-crf",
            "17",
            "-tune",
            "animation",
            "-vf",
            f"fps={Config().graphics.record_fps},format=yuv420p",
            str(self.prefix / "movies" / f"game_{self.identifier}.mp4"),
        ]

        subprocess.run(args)

        for image in self.prefix.glob(f"pics/pic_{self.identifier}_*.png"):
            os.remove(str(image))
