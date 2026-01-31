"""Image class"""

import struct
from os import stat_result
from pathlib import Path


class PortableNetworkGraphics:
    """Portable Network Graphics (PNG)"""

    path: Path
    stat: stat_result

    def __init__(self, path: Path):
        self.path = path

    def check_size(self, max_size: int) -> None:
        """Check file size against the limit.

        - max_size: int - Maximum file size in bytes
        """
        self.stat = self.path.stat()
        if self.stat.st_size > max_size:
            raise ValueError(
                f"Size of image {self.path} exceeds limit of {max_size / 1024 / 1024} MiB."
            )

    def check_dimensions(self, width: int, height: int) -> None:
        """Check dimensions of image."""
        with self.path.open("rb") as file_object:
            data = file_object.read()
        if not (data[:8] == b"\211PNG\r\n\032\n" and data[12:16] == b"IHDR"):
            raise ValueError(f"Path {self.path} is not a PNG image.")
        w, h = struct.unpack(">LL", data[16:24])
        image_width = int(w)
        image_height = int(h)
        if image_width != width:
            raise ValueError(
                f"Width of image {self.path} must be equal to {width} but is {image_width}."
            )
        if image_height != height:
            raise ValueError(
                f"Height of image {self.path} must be equal to {height} but is {image_height}."
            )
