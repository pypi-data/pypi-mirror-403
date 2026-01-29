from dataclasses import dataclass
from typing import Optional
from .base import Style

@dataclass
class ContainerStyle(Style):
    bg_color: Optional[str] = None
    border_color: Optional[str] = None
    border_width: Optional[float] = None
    border_radius: Optional[int] = None
    padding: Optional[int] = None
    margin: Optional[int] = None
    width: Optional[float] = None
    height: Optional[float] = None
