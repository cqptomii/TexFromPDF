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
    def to_markdown(self, page_number : int = 0, page_separator : str = "---"):
        """
            Method that returns the markdown representation of the document
            If page_number is specified, returns the markdown representation of the corresponding page
            ELSE returns the concatenation of the markdown representation of all pages
        :param page_separator: (str) Separator between each page
        :param page_number: (int) Page number to return
        :return: (str) Markdown representation of the document
        """
        document_content : str = ""

        if page_number >= 0:

            if page_number < len(self.pages):
                return self.pages[page_number].to_markdown()
            else:
                raise IndexError("Page number out of range")
        else:

            for page in self.pages:
                document_content += page.to_markdown() + page_separator

            return document_content
    def to_html(self, page_number : int = 0):
        """
            Method that returns the html representation of the document
            IF page_number is specified, returns the html representation of the corresponding page
            Else returns the concatenation of the html representation of all pages
        :param page_number: (int) Page number to return
        :return: (str) Html representation of the document
        """
        html_content : str = ""

        if page_number >= 0:

            if page_number < len(self.pages):
                return self.pages[page_number].to_html()
            else:
                raise IndexError("Page number out of range")
        else:
            for page in self.pages:
                html_content += page.to_html() + "\n"

            return html_content