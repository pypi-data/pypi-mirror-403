from typing import List, Optional
from reportlab.platypus import Table, TableStyle
from .base import Block, BaseTableBlock
from gen_pdf_abc_xyz_will_change_later.styles.context import RenderContext

class ColumnsBlock(BaseTableBlock):
    def __init__(self, children: List[Block], col_widths=None, style=None):
        super().__init__(style=style)
        self.children = children
        self.col_widths = col_widths
        
        self.margin = getattr(style, 'margin', 0) or 0 if style else 0
        self.padding = getattr(style, 'padding', 0) or 0 if style else 0

    def render(self, context: Optional['RenderContext'] = None):
        row_data = []
        for child in self.children:
             r = child.render(context)
             if isinstance(r, list):
                 row_data.append(r)
             else:
                 row_data.append([r])
        
        data = [row_data]
        t = Table(data, colWidths=self.col_widths)
        
        style_cmds = self._get_base_style(context)
        t.setStyle(TableStyle(style_cmds))
        t.spaceBefore = self.margin
        t.spaceAfter = self.margin
        return t
