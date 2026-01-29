from typing import List, Any
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from .base import BaseTableBlock

class TableBlock(BaseTableBlock):
    def __init__(self, data: List[List[Any]], col_widths=None, row_heights=None, style=None):
        super().__init__()
        self.data = data
        self.col_widths = col_widths
        self.row_heights = row_heights
        self.style = style or [
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

    def render(self, context=None):
        t = Table(self.data, colWidths=self.col_widths, rowHeights=self.row_heights)
        t.setStyle(TableStyle(self.style))
        return t
