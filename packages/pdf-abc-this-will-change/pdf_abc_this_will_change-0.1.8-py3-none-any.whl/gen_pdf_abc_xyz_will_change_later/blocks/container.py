from typing import List, Union, Optional
from reportlab.platypus import Table, TableStyle
from reportlab.lib.colors import HexColor
from .base import Block, BaseTableBlock
from gen_pdf_abc_xyz_will_change_later.styles.context import RenderContext

class ContainerBlock(BaseTableBlock):
    def __init__(self, children: Union[Block, List[Block]], style=None):
        super().__init__(style=style)
        self.children = children if isinstance(children, list) else [children]
        
        self.width = getattr(style, 'width', None) if style else None
        self.height = getattr(style, 'height', None) if style else None
        self.margin = getattr(style, 'margin', 0) or 0 if style else 0
        self.padding = getattr(style, 'padding', 0) or 0 if style else 0

    def render(self, context: Optional['RenderContext'] = None):
        if self.style:
            if self.width is None: self.width = getattr(self.style, 'width', None)
            if self.height is None: self.height = getattr(self.style, 'height', None)

        rendered_children = []
        for child in self.children:
            r = child.render(context)
            if isinstance(r, list):
                rendered_children.extend(r)
            else:
                rendered_children.append(r)
        
        data = [[rendered_children]]
        
        col_widths = [self.width] if self.width else None
        row_heights = [self.height] if self.height else None
        
        final_radius = 0
        if self.style:
             final_radius = getattr(self.style, 'border_radius', 0) or 0
             
        if self.height and final_radius > self.height / 2.0:
            final_radius = self.height / 2.0
            
        corner_radii = [final_radius]*4 if final_radius > 0 else None
        
        t = Table(data, colWidths=col_widths, rowHeights=row_heights, cornerRadii=corner_radii)
        
        style_cmds = self._get_base_style(context)
            
        if self.style:
            border_width = getattr(self.style, 'border_width', 0) or 0
            border_color = getattr(self.style, 'border_color', None)
            
            if border_width > 0 and border_color:
                final_border_color = border_color
                c = HexColor(final_border_color) if isinstance(final_border_color, str) else final_border_color
                style_cmds.append(('BOX', (0,0), (-1,-1), border_width, c))

        if final_radius > 0:
             t.setStyle(TableStyle([('ROUNDEDCORNERS', [final_radius]*4)]))
        
        t.setStyle(TableStyle(style_cmds))
        t.spaceBefore = self.margin
        t.spaceAfter = self.margin
        return t
