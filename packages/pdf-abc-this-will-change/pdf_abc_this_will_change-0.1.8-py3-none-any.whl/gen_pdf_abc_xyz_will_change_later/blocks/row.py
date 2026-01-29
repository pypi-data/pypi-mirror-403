from typing import List, Optional
from reportlab.platypus import Table, TableStyle
from .base import Block, BaseTableBlock
from gen_pdf_abc_xyz_will_change_later.styles.context import RenderContext

class RowBlock(BaseTableBlock):
    def __init__(self, children: List[Block], col_widths=None, style=None):
        super().__init__(style=style)
        self.children = children
        self.col_widths = col_widths
        
        self.height = None
        self.margin = 0
        self.padding = 0
        if self.style:
             self.height = getattr(self.style, 'height', None)
             self.margin = getattr(self.style, 'margin', 0) or 0
             self.padding = getattr(self.style, 'padding', 0) or 0

    def render(self, context: Optional['RenderContext'] = None):
        if self.height is None and self.style:
             self.height = getattr(self.style, 'height', None)
        
        row_data = []
        for child in self.children:
            r = child.render(context)
            if isinstance(r, list):
                row_data.append(r)
            else:
                row_data.append([r])
        
        data = [row_data]
        row_heights = [self.height] if self.height else None
        
        t = Table(data, colWidths=self.col_widths, rowHeights=row_heights)
        
        style_cmds = self._get_base_style(context)
        t.setStyle(TableStyle(style_cmds))
        t.spaceBefore = self.margin
        t.spaceAfter = self.margin
        return t
