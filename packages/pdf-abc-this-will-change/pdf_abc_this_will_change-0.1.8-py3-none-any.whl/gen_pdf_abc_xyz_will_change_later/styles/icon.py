from dataclasses import dataclass
from typing import Optional
from .base import Style

@dataclass
class IconStyle(Style):
    size: Optional[float] = None
    color: Optional[str] = None
