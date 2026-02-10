from abc import ABC, abstractmethod



class BaseProcessor(ABC):
    @abstractmethod
    def process(self, page , page_number : int, block : dict):
        pass