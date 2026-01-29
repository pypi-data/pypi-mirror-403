from typing import List, Optional
from reportlab.platypus import Table, TableStyle
from .base import Block, BaseTableBlock
from gen_pdf_abc_xyz_will_change_later.styles.context import RenderContext

class GridBlock(BaseTableBlock):
    def __init__(self, children: List[Block], cols=2, col_widths=None, style=None):
        super().__init__(style=style)
        self.children = children
        self.cols = cols
        self.col_widths = col_widths
        
        self.width = None
        self.margin = 0
        self.padding = 0
        if self.style:
             self.width = getattr(self.style, 'width', None)
             self.margin = getattr(self.style, 'margin', 0) or 0
             self.padding = getattr(self.style, 'padding', 0) or 0

    def render(self, context: Optional['RenderContext'] = None):
        if self.width is None and self.style:
             self.width = getattr(self.style, 'width', None)
             
        grid_data = []
        current_row = []
        
        for i, child in enumerate(self.children):
            r = child.render(context)
            cell = r if isinstance(r, list) else [r]
            current_row.append(cell)
            
            if len(current_row) == self.cols:
                grid_data.append(current_row)
                current_row = []
        
        if current_row:
            while len(current_row) < self.cols:
                current_row.append('')
            grid_data.append(current_row)

        widths = self.col_widths
        if self.width and not widths:
            widths = [self.width / float(self.cols)] * self.cols
        elif widths and not isinstance(widths, list):
            widths = [widths] * self.cols
            
        t = Table(grid_data, colWidths=widths)
         
        style_cmds = self._get_base_style(context)
        t.setStyle(TableStyle(style_cmds))
        t.spaceBefore = self.margin
        t.spaceAfter = self.margin
        return t
