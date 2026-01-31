from dataclasses import dataclass
from typing import BinaryIO

__all__ = ("XenforoFile",)


@dataclass
class XenforoFile:
    stream: BinaryIO
    name: str
