from typing import Optional
from .base import Block
from reportlab.platypus import Spacer

class IconBlock(Block):
    def __init__(self, path_or_url: str, size=None, color=None, is_url=True, style=None):
        super().__init__(style=style)
        self.size = size
        self.width = size
        self.height = size

    def render(self, context=None):
        # SVG support removed. Returning Spacer.
        w = self.width if self.width else 0
        h = self.height if self.height else 0
        return Spacer(w, h)
