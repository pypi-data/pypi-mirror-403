class Page:
    def __init__(self, bg_color=None):
        self.blocks = []
        self.bg_color = bg_color

    def add_block(self, block):
        self.blocks.append(block)

    def get_renderables(self, context=None):
        story = []
        for b in self.blocks:
            r = b.render(context)
            if isinstance(r, list):
                story.extend(r)
            else:
                story.append(r)
        return story
