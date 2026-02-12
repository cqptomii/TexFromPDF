from dataclasses import dataclass

from src.datamodel.layout_blocks.base_model import BaseModel


@dataclass
class TextModel(BaseModel):
    content: str

    def to_dict(self):
        return self.__dict__
    def to_markdown(self) -> str:
        if self.class_name.lower() in ["title", "section-header"]:
            self.content = self.content.replace("\n", " ")
            markdown_text = "## " + self.content + "\n"
        else:
            markdown_text = self.content + "\n"

        return markdown_text
    def to_html(self) -> str:
        if self.class_name.lower() in ["title", "section-header"]:
            html_text = "<h2>" + self.content + "</h2>"
        else:
            html_text = self.content + "\n"

        return html_text
