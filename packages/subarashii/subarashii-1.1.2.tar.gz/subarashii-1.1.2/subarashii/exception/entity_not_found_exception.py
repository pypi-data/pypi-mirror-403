class EntityNotFoundException(Exception):
    def __init__(self):
        super().__init__("entity not found")
