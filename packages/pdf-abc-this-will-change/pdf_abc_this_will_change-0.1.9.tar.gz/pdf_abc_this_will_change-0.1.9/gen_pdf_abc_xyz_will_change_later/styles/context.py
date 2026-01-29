from dataclasses import dataclass, field
from typing import List, Optional, Deque
from collections import deque

from .base import Style
from .box import ContainerStyle
from .text import TextStyle
from .icon import IconStyle

class RenderContext:
    def __init__(self):
        self.style_stack: Deque[Style] = deque()
        self._root_style = ContainerStyle()

    def push_style(self, style: Style):
        self.style_stack.append(style)

    def pop_style(self):
        if self.style_stack:
            self.style_stack.pop()

    def resolve_style(self, base_style: Optional[Style] = None) -> Style:
        final = type(base_style)() if base_style else ContainerStyle()
        
        target_type = type(final)
        
        for s in self.style_stack:
            if isinstance(s, target_type):
                final = final.merge(s)
            
        if base_style:
            final = final.merge(base_style)
            
        return final

    def get_color(self, name_or_hex: str) -> str:
        # No theme lookup anymore, just return the value as-is
        return name_or_hex
