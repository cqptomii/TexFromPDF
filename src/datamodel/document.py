from dataclasses import dataclass
from .page import Page
from typing import Optional, List

@dataclass
class Document:
    id: str
    pages: Optional[List[Page]]

    def to_dict(self):
        return {
            "id": self.id,
            "pages": [page.to_dict() for page in self.pages]
        }
    def to_markdown(self, page_number : int = 0, page_separator : str = "\n---\n\n"):
        """
            Method that returns the markdown representation of the document
            If page_number (starting at 1) is specified, returns the markdown representation of the corresponding page
            ELSE (page_number = 0) returns the concatenation of the markdown representation of all pages
        :param page_separator: (str) Separator between each page
        :param page_number: (int) Page number to return (1-based), 0 for all pages
        :return: (str) Markdown representation of the document
        """
        if page_number > 0:
            if page_number <= len(self.pages):
                return self.pages[page_number - 1].to_markdown()
            raise IndexError("Page number out of range")

        return page_separator.join(page.to_markdown() for page in self.pages)
    def to_html(self, page_number : int = 0):
        """
            Method that returns the html representation of the document
            IF page_number (starting at 1) is specified, returns the html representation of the corresponding page
            Else (page_number = 0) returns the concatenation of the html representation of all pages
        :param page_number: (int) Page number to return (1-based), 0 for all pages
        :return: (str) Html representation of the document
        """
        if page_number > 0:
            if page_number <= len(self.pages):
                return self.pages[page_number - 1].to_html()
            raise IndexError("Page number out of range")

        return "<hr>\n".join(page.to_html() for page in self.pages)
