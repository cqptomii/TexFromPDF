from src.datamodel.layout_blocks import BaseModel
from dataclasses import dataclass, field


@dataclass
class TextFormulaModel(BaseModel):
    content : str
    structured_blocks : dict = field(default_factory=lambda: {})

    def to_html(self):
        if self.class_name.lower() in ["title"]:
            return "<h2>" + self.content.replace("\n", " ") + "</h2>"

        return self.content + "\n"
    def to_markdown(self):
        if self.class_name.lower() in ["title"]:
            self.content = self.content.replace("\n", " ")
            markdown_text = "## " + self.content + "\n"
        else:
            markdown_text = self.content

        return markdown_text
    def to_dict(self):
        return self.__dict__

