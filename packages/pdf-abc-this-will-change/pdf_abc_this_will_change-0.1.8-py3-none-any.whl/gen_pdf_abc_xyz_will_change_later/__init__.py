from .document import Document, DocumentBuilder
from .page import Page

from .styles import ContainerStyle, TextStyle, IconStyle, RenderContext
import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def load_fonts():
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    if not os.path.exists(font_dir):
        print(f"Warning: Font directory not found: {font_dir}")
        return

    for f in os.listdir(font_dir):
        if f.lower().endswith('.ttf'):
            font_name = os.path.splitext(f)[0]
            font_path = os.path.join(font_dir, f)
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
            except Exception as e:
                print(f"Failed to register font {font_name}: {e}")

load_fonts()
