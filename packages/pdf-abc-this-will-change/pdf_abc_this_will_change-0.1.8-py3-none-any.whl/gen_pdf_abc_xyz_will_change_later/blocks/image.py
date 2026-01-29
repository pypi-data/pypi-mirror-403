from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from gen_pdf_abc_xyz_will_change_later.styles.context import RenderContext
import os
import tempfile
import urllib.request
from reportlab.platypus import Image, Spacer
from reportlab.lib.utils import ImageReader
from .base import Block

class ImageBlock(Block):
    def __init__(self, path: str, style=None):
        self.path = path
        self.style = style
        
        self.width = getattr(style, 'width', None) if style else None
        self.height = getattr(style, 'height', None) if style else None
        self.border_radius = getattr(style, 'border_radius', 0) or 0 if style else 0

    def render(self, context: Optional['RenderContext'] = None):
        if self.style:
             if self.width is None: self.width = getattr(self.style, 'width', None)
             if self.height is None: self.height = getattr(self.style, 'height', None)
             if self.border_radius == 0: 
                 radius = getattr(self.style, 'border_radius', 0)
                 self.border_radius = radius if radius is not None else 0

        image_path = self.path
        
        if self.path.startswith('http://') or self.path.startswith('https://'):
            try:
                import hashlib
                fname = hashlib.md5(self.path.encode()).hexdigest() + ".jpg"
                temp_path = os.path.join(tempfile.gettempdir(), fname)
                
                if not os.path.exists(temp_path):
                    with urllib.request.urlopen(self.path) as response:
                        data = response.read()
                    with open(temp_path, 'wb') as f:
                        f.write(data)
                
                image_path = temp_path
            except Exception as e:
                print(f"Failed to download image: {e}")
                return Spacer(0, 0)

        if self.border_radius > 0:
            try:
                from PIL import Image as PILImage, ImageDraw, ImageOps
                
                with PILImage.open(image_path) as im:
                    im = im.convert("RGBA")
                    
                    mask = PILImage.new('L', im.size, 0)
                    draw = ImageDraw.Draw(mask)
                    
                    target_w_pts = self.width
                    target_h_pts = self.height
                    
                    if target_w_pts and target_h_pts:
                        scale = 3 
                        px_w = int(target_w_pts * scale)
                        px_h = int(target_h_pts * scale)
                        px_radius = int(self.border_radius * scale)
                        
                        im = im.resize((px_w, px_h), PILImage.LANCZOS)
                        
                        mask = PILImage.new('L', (px_w, px_h), 0)
                        draw = ImageDraw.Draw(mask)
                        draw.rounded_rectangle([(0,0), (px_w, px_h)], radius=px_radius, fill=255)
                        
                        im.putalpha(mask)
                        
                        fd, new_path = tempfile.mkstemp(suffix='.png')
                        os.close(fd)
                        im.save(new_path, format="PNG")
                        image_path = new_path
                        
            except ImportError:
                print("Pillow not installed, skipping border radius")
            except Exception as e:
                print(f"Failed to apply border radius: {e}")

        if (self.width is None or self.height is None) and self.width != self.height:
            try:
                utils = ImageReader(image_path)
                iw, ih = utils.getSize()
                aspect = ih / float(iw)
                
                if self.width and self.height is None:
                    self.height = self.width * aspect
                elif self.height and self.width is None:
                    self.width = self.height / aspect
            except Exception:
                pass

        return Image(image_path, width=self.width, height=self.height)
