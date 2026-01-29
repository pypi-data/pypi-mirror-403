from typing import Optional, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from gen_pdf_abc_xyz_will_change_later.styles.context import RenderContext
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import ParagraphStyle
from .base import Block

class TextBlock(Block):
    def __init__(self, text: str, style: Optional[Any] = None, **kwargs):
        super().__init__(style=style)
        self.text = text
        self.kwargs = kwargs
        
        self._legacy_style = None
        if not style and not kwargs:
             self._legacy_style = ParagraphStyle('Normal')
        elif isinstance(style, ParagraphStyle):
             self._legacy_style = style

    def render(self, context: Optional['RenderContext'] = None):
        if context:
            theme_style = None
            resolved_style = self.style
            
            if resolved_style and not isinstance(resolved_style, ParagraphStyle):
                theme_style = resolved_style

            rl_style_name = f'Text_{id(self)}'
            
            base_rl = ParagraphStyle('Normal')
            
            kw = dict(base_rl.__dict__) 
            kw['name'] = rl_style_name
            
            if theme_style:
                if theme_style.font_name: kw['fontName'] = theme_style.font_name
                if theme_style.font_size: kw['fontSize'] = theme_style.font_size
                if theme_style.color: kw['textColor'] = theme_style.color
                if theme_style.leading: kw['leading'] = theme_style.leading
                if theme_style.alignment is not None: kw['alignment'] = theme_style.alignment
                if theme_style.space_after: kw['spaceAfter'] = theme_style.space_after
                
            if self.kwargs:
                for k, v in self.kwargs.items():
                    if k == 'textColor' and v: kw[k] = v
                    else: kw[k] = v
            
            return Paragraph(self.text, ParagraphStyle(**kw))
            
        else:
            if self._legacy_style:
                s = self._legacy_style
            else:
                s = ParagraphStyle('Normal')
                
            if self.kwargs:
                s = ParagraphStyle(f'AdHoc_{id(self)}', parent=s, **self.kwargs)
                
            return Paragraph(self.text, s)
