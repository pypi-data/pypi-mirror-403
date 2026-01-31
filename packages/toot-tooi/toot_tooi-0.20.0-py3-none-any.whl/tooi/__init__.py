from enum import StrEnum, auto
from importlib import metadata
from uuid import UUID

try:
    __version__ = metadata.version("toot-tooi")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"


APP_NAME = "tooi"
APP_WEBSITE = "https://codeberg.org/ihabunek/tooi"
USER_AGENT = f"{APP_NAME}/{__version__}"

MessageId = UUID
"""Uniquely identifies a message in the status bar allowing it to be cleared."""


class ImageType(StrEnum):
    """Determines how to render images"""
    sixel = auto()
    """Force Sixel images"""
    tgp = auto()
    """Force TGP images"""
    halfcell = auto()
    """Force Halfcell images"""
    unicode = auto()
    """Force Unicode images"""
    none = auto()
    """Don't render images"""
    auto = auto()
    """Automatically choose best available method"""
