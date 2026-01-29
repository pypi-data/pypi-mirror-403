from dataclasses import dataclass
from typing import Optional
from .base import Style

@dataclass
class TextStyle(Style):
    font_name: Optional[str] = None
    font_size: Optional[int] = None
    color: Optional[str] = None
    leading: Optional[int] = None
    alignment: Optional[int] = None
    space_after: Optional[int] = None
