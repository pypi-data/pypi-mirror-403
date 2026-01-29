from reportlab.platypus import Spacer
from .base import Block

class SpacerBlock(Block):
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def render(self, context=None):
        return Spacer(self.width, self.height)
