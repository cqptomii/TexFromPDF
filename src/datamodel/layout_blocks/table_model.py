from dataclasses import dataclass
from typing import List
from src.datamodel.layout_blocks.base_model import BaseModel

@dataclass
class TableModel(BaseModel):
    structured_content: List[list]

    def to_dict(self):
        return self.__dict__

    def _convert_table_to_html(self) -> str:
        """
            Method that converts the table to html format
        :return: (str) Html representation of the table
        """
        if not self.structured_content:
            return "<table></table>"

        num_rows = len(self.structured_content)
        num_cols = len(self.structured_content[0]) if num_rows > 0 else 0

        processed = [[False for _ in range(num_cols)] for _ in range(num_rows)]

        html_table = "<table>"

        for i in range(num_rows):
            html_table += "<tr>"

            for j in range(num_cols):
                if processed[i][j]:
                    continue

                cell_content = self.structured_content[i][j].strip()

                # Calculate the colspan (merge horizontally)
                colspan = 1
                while (j + colspan < num_cols and
                       self.structured_content[i][j + colspan].strip() == cell_content):
                    processed[i][j + colspan] = True
                    colspan += 1

                # Calculate the rowspan (merge vertically)
                rowspan = 1
                can_expand = True
                while can_expand and i + rowspan < num_rows:
                    for k in range(colspan):
                        if self.structured_content[i + rowspan][j + k].strip() != cell_content:
                            can_expand = False
                            break

                    if can_expand:
                        for k in range(colspan):
                            processed[i + rowspan][j + k] = True
                        rowspan += 1

                cell_attrs = []
                if rowspan > 1:
                    cell_attrs.append(f'rowspan="{rowspan}"')
                if colspan > 1:
                    cell_attrs.append(f'colspan="{colspan}"')

                attrs_str = " " + " ".join(cell_attrs) if cell_attrs else ""
                html_table += f"<td{attrs_str}>{cell_content}</td>"

                processed[i][j] = True

            html_table += "</tr>"

        html_table += "</table>"
        return html_table
    def _convert_table_to_json_blocks(self) -> str:
        """
            Method that converts the table to a list of blocks in json format
        :return: (str) Json representation of the table
        """
        pass

    def to_markdown(self, table_format: str = "html"):
        """
            Method that converts the table to markdown format
        :param table_format: (str) Format of the table to return (html, json)
        :return: (str) Markdown representation of the table
        """
        if table_format == "json":
            return self._convert_table_to_json_blocks()
        else:
            return self._convert_table_to_html()
    def to_html(self) -> str:
        """
            Method that converts the table to html format
        :return: (str) Html representation of the table
        """
        return self._convert_table_to_html()