from .icon import IconBlock

class LucideIconBlock(IconBlock):
    BASE_URL = "https://unpkg.com/lucide-static/icons/{name}.svg"

    def __init__(self, icon_name: str, size=None, color=None, style=None):
        url = self.BASE_URL.format(name=icon_name)
        super().__init__(url, size=size, color=color, is_url=True, style=style)
        self.icon_name = icon_name
