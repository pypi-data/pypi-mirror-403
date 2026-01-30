class File:
    pass

class ContentFile(File):
    def __init__(self, content, name=None):
        self.content = content
        self.name = name
