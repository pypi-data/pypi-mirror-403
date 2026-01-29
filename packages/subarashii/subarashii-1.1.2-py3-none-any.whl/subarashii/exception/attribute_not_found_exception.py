class AttributeNotFoundException(Exception):
    def __init__(self):
        super().__init__("attribute not found")
