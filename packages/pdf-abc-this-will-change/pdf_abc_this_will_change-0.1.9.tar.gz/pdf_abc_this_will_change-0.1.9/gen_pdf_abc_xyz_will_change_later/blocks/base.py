from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Union, Any
from reportlab.lib.colors import HexColor

from gen_pdf_abc_xyz_will_change_later.styles.context import RenderContext

class Block(ABC):
    def __init__(self, style: Optional[Any] = None):
        self.style = style

    @abstractmethod
    def render(self, context: Optional[RenderContext] = None) -> Any:
        pass

class BaseTableBlock(Block):
    def __init__(self, style: Optional[Any] = None):
        super().__init__(style=style)

    def _get_base_style(self, context: Optional['RenderContext'] = None) -> List[Tuple]:
        style_cmds = [
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]
        
        # Pull visual properties from the style object
        padding = 0
        bg_color = None
        
        if self.style:
            padding = getattr(self.style, 'padding', 0) or 0
            bg_color = getattr(self.style, 'bg_color', None)
        
        style_cmds.extend([
            ('LEFTPADDING', (0, 0), (-1, -1), padding),
            ('RIGHTPADDING', (0, 0), (-1, -1), padding),
            ('TOPPADDING', (0, 0), (-1, -1), padding),
            ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
        ])
        
        if bg_color:
            final_bg = bg_color
            try:
                c = HexColor(final_bg) if isinstance(final_bg, str) and final_bg.startswith('#') else final_bg
                style_cmds.append(('BACKGROUND', (0,0), (-1,-1), c))
            except Exception as e:
                print(f"Warning: Invalid bg color '{final_bg}': {e}")
            
        return style_cmds
