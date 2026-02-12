import fitz, os
from pathlib import (Path)
from PIL import Image, ImageDraw
from src.processors import BaseProcessor
from src.datamodel import TableModel


class TableProcessor(BaseProcessor):
    def __init__(self, output_dir: Path, table_settings : dict = None):
        super().__init__()
        self._output_dir = output_dir if output_dir is not None else os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        self._table_settings = table_settings if table_settings is not None else {
                "strategy": "lines",
                "snap_tolerance": 4,
                "join_tolerance": 4,
                "edge_min_length": 4,
                "intersection_tolerance": 10,
                "text_tolerance": 4
            }

    def _save_debug_image(self, page, table, page_number: int, block: dict):
        zoom = 300 / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(img)

        for i, table in enumerate(table.tables):
            rect = table.bbox
            x0, y0, x1, y1 = [v * 300 / 72 for v in rect]

            draw.rectangle([x0, y0, x1, y1], outline="red", width=4)
            draw.text((x0, y0 - 10), f"Table {i + 1}", fill="red")

            # Dessiner les cellules
            for cell in table.cells:
                cx0, cy0, cx1, cy1 = [v * zoom for v in cell]
                draw.rectangle([cx0, cy0, cx1, cy1], outline="blue", width=2)

        img_dir = os.path.join(self._output_dir, "predictions", f"page_{page_number:04d}", "table")
        os.makedirs(img_dir, exist_ok=True)

        print(f"Saving debug image to {img_dir}")
        img.save(os.path.join(img_dir, f"page_{block.get("id",-1)}_{page_number:04d}.png"))

    def process(self, page, page_number: int, block: dict) -> TableModel:
        bbox = block.get("bbox_pdf", [])
        confidence = block.get("confidence", 0)
        class_name = block.get("class_name", "table")
        rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])

        ## Extract the table from the page
        table = page.find_tables(rect, **self._table_settings)

        if not table or not table.tables:
            print("There is no table detected on this bbox :", bbox)
            return TableModel(
                page=page_number,
                bbox=bbox,
                class_name=class_name,
                confidence=confidence,
                structured_content=[]
            )

        ## Save the table identified for debuging
        self._save_debug_image(page, table, page_number, block)

        table = table.tables[0].extract()

        matrix = []
        first_line = []
        other_lines = table[1:]

        for i, cell in enumerate(table[0]):
            if cell is not None:
                if not cell.strip():
                    delete_cell = True
                    ## Check if there is a non-empty cell in the other lines
                    for other_line in other_lines:
                        if other_line[i]:
                            delete_cell = False
                            break

                    if not delete_cell:
                        first_line.append(cell)
                    else:
                        ## Delete each cell in the other lines
                        for other_line in other_lines:
                            other_line.pop(i)
                else:
                    first_line.append(cell)
            elif i > 0:
                first_line.append(first_line[i - 1])

        matrix.append(first_line)

        other_lines_corrected = []
        ## Update the matrix with the other lines
        for row in other_lines:
            filtered_row = []
            for i, col in enumerate(row):

                if col and col.strip():
                    filtered_row.append(col.strip())
                else:
                    if i < len(first_line):
                        if first_line[i]:
                            filtered_row.append(col)
                            continue

            ## Keep the line if it contains at least one cell
            if filtered_row:
                nb_val = len([cell for cell in filtered_row if cell and cell.strip() and cell != ''])
                if nb_val > 0:
                    other_lines_corrected.append(filtered_row)

        matrix.extend(other_lines_corrected)

        ## Check if there are empty columns in the other lines
        for i, cell in enumerate(other_lines_corrected[0]):
            if cell is None:
                ## Check if there is a non-empty cell in the other lines
                for other_line in other_lines_corrected[1:]:
                    if other_line[i]:
                        break
                else:
                    for line in matrix:
                        line.pop(i)

        ## Cells propagation
        for i, row in enumerate(matrix):
            for j, cell in enumerate(row):
                if cell is None and i > 0:
                    row[j] = matrix[i - 1][j]


        print("=" *30)
        for line in matrix:
            print(line)
        print("=" *30)


        return TableModel(
            page=page_number,
            bbox=bbox,
            class_name=class_name,
            confidence=confidence,
            structured_content=matrix
        )