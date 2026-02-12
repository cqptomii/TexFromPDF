from dataclasses import dataclass
from . import BaseModel
from typing import Optional, List

@dataclass
class Page:
    page_number: int
    content_blocks: Optional[List[BaseModel]]

    def to_dict(self) -> dict:
        returned_dict = {
            "page_number": self.page_number,
            "blocks_extracted": [ block.to_dict() for block in self.content_blocks]
        }

        return returned_dict
    def to_markdown(self) -> str:
        markdown_content : str = ""

        for block in self.content_blocks:
            markdown_content += block.to_markdown() + "\n"

        return markdown_content
    def to_html(self) -> str:
        html_content : str = ""

        for block in self.content_blocks:
            html_content += block.to_html() + "\n"

        return html_content
