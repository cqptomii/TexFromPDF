from src.processors import BaseProcessor


class TableProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()

    def process(self, page, page_number: int, block: dict):
        pass