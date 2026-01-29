from reportlab.lib.pagesizes import letter
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, NextPageTemplate, PageBreak
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from typing import List, Optional
from .page import Page


from .styles.context import RenderContext

class Document:
    def __init__(self, pagesize=letter, pages: List[Page] = None):
        self.pages = pages or []
        self.pagesize = pagesize
        self.context = RenderContext()

    def add_page(self, page: Page):
        if not isinstance(page, Page):
            raise TypeError("Expected a Page object")
        self.pages.append(page)
    
    def append(self, pages: list):
        if not isinstance(pages, list):
             raise TypeError("Expected a list of Page objects")
        for p in pages:
            self.add_page(p)

    def _make_bg_drawer(self, color, context=None):
        def draw(canvas, doc):
            if color:
                canvas.saveState()
                final_color = color
                c = HexColor(final_color) if isinstance(final_color, str) and final_color.startswith('#') else final_color
                canvas.setFillColor(c)
                w, h = self.pagesize
                canvas.rect(0, 0, w, h, fill=True, stroke=False)
                canvas.restoreState()
        return draw

    def generate(self, filename: str):
        doc = BaseDocTemplate(filename, pagesize=self.pagesize)
        
        context = self.context
            
        margin = 72
        
        frame = Frame(
            margin, margin, 
            doc.width, doc.height, 
            id='normal'
        )
        
        templates = []
        story = []
        
        for i, page in enumerate(self.pages):
            template_id = f'PageTemplate_{i}'
            
            pt = PageTemplate(
                id=template_id, 
                frames=[frame], 
                onPage=self._make_bg_drawer(page.bg_color, context)
            )
            templates.append(pt)
            
            if i == 0:
                story.extend(page.get_renderables(context))
            else:
                story.append(NextPageTemplate(template_id))
                story.append(PageBreak())
                story.extend(page.get_renderables(context))
        
        doc.addPageTemplates(templates)
        doc.build(story)

class DocumentBuilder:
    def __init__(self, pagesize=letter):
        self.pages = []
        self.pagesize = pagesize

    def add_page(self, page: Page) -> 'DocumentBuilder':
        self.pages.append(page)
        return self

    def build(self) -> Document:
        return Document(pagesize=self.pagesize, pages=self.pages)

    def generate(self, filename: str):
        self.build().generate(filename)
