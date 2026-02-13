from typing import List, Dict, Any
from ultralytics import YOLO
from pathlib import Path
import fitz, os, json, numpy as np

from src.config.main_config import MainConfig
from utils.numpy_encoder import NumpyJSONEncoder
from utils.bounding_box import *
from utils.scanned import is_scanned_image, is_scanned_block

class PdfClassifier:
    def __init__(self, config : MainConfig):

        self._config = config.classifier_config

        self._model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models/layout_detection", self._config.model_name)
        self._verbose = config.verbose
        self._output_dir = config.output_dir
        self._page_rotations = {}


        ## Rasterization parameters
        self._dpi = 450
        self._zoom = self._dpi / 72

        ## Load layout detection model
        self._load_model()
    def _load_model(self):
        self._model = YOLO(self._model_path)

    ##
    ## Rotation Dectection
    ##
    def _detect_page_orientation(self, page) -> int:
        """
            Detect the page orientation based on the text direction
        :param page: (fitz.Page) Page to detect orientation for
        :return: (int) Rotation angle (0, 90, 180, 270)
        """
        text_dict = page.get_text("dict")

        if not text_dict.get("blocks"):
            return 0

        ## Analyze the text direction
        horizontal_chars = 0
        vertical_chars = 0
        upside_down_chars = 0

        for block in text_dict["blocks"]:
            if block.get("type") == 0:
                for line in block.get("lines", []):
                    line_dir = line.get("dir", [1, 0])

                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue

                        char_count = len(text)

                        ## Analyze the vector direction
                        ## dir = [1, 0] -> Horizontal text (0°)
                        ## dir = [0, 1] -> Vertical text descendant (90°)
                        ## dir = [-1, 0] -> Horizontal Upside-down text (180°)
                        ## dir = [0, -1] -> Vertical ascendant text (270°)

                        x_dir = round(line_dir[0], 2)
                        y_dir = round(line_dir[1], 2)

                        if abs(x_dir) > 0.9 and abs(y_dir) < 0.1:  # Horizontal
                            if x_dir > 0:
                                horizontal_chars += char_count
                            else:
                                upside_down_chars += char_count
                        elif abs(y_dir) > 0.9 and abs(x_dir) < 0.1:  # Vertical
                            vertical_chars += char_count

        total_chars = horizontal_chars + vertical_chars + upside_down_chars

        if total_chars == 0:
            return 0

        if self._verbose:
            print(
                f"Orientation analysis - Horizontal: {horizontal_chars}, Vertical: {vertical_chars}, Upside-down: {upside_down_chars}")

        max_chars = max(horizontal_chars, vertical_chars, upside_down_chars)

        if max_chars == horizontal_chars:
            return 0
        elif max_chars == vertical_chars:

            return 270
        elif max_chars == upside_down_chars:
            return 180

        return 0
    def _detect_page_orientation_by_projection(self, page) -> int:
        """
            Detect the page orientation based on the projection of the image
            Use detection of text with OpenCV
        :return: (int) Rotation angle (0, 90, 180, 270)
        """
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        gray = np.dot(img_data[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)

        ## Image binarisation
        threshold = np.mean(gray)
        binary = (gray < threshold).astype(np.uint8) * 255

        ## Calculate projections
        h_projection = np.sum(binary, axis=1)
        v_projection = np.sum(binary, axis=0)

        ## Calculate variance of projections
        h_variance = np.var(h_projection)
        v_variance = np.var(v_projection)

        if self._verbose:
            print(f"Projection variance - Horizontal: {h_variance:.2f}, Vertical: {v_variance:.2f}")

        ## If the horizontal variance is much higher, the text is horizontal
        ## If the vertical variance is higher, the text is vertical
        ratio = h_variance / (v_variance + 1e-6)

        if ratio > 1.2:
            return 0  # Horizontal text
        elif ratio < 0.8:
            return 270  ## Vertical text, Rotation needed

        return 0
    def _correct_page_rotation(self, page) -> int:
        """
            Method that corrects the page rotation based on the text detected
        :param page: (fitz.Page) Page to correct rotation for
        :return: (int) angle of rotation correction
        """

        rotation_text = self._detect_page_orientation(page)

        ## If there is no text, we can determine the rotation based on the projection of the image
        if rotation_text == 0:
            rotation_image = self._detect_page_orientation_by_projection(page)
            rotation_needed = rotation_image
        else:
            rotation_needed = rotation_text

        if rotation_needed != 0:
            current_rotation = page.rotation
            new_rotation = (current_rotation + rotation_needed) % 360
            page.set_rotation(new_rotation)
            if self._verbose:
                print(
                    f"Page {page.number + 1} rotated from {current_rotation}° to {new_rotation}° (applied {rotation_needed}°)")

        return rotation_needed

    def _page_rasterization(self, doc, dpi: int = 300, page_format = "png") -> List[dict]:
        """
            Méthod that rasterize a pdf page
        :return:
        """

        os.makedirs(self._output_dir, exist_ok=True)
        os.makedirs(os.path.join(self._output_dir, "rasterized_pages"), exist_ok=True)

        rasterized_dir = os.path.join(self._output_dir, "rasterized_pages")

        matrix = fitz.Matrix(self._zoom, self._zoom)
        pages_metadata = []

        for i, page in enumerate(doc):

            ## Page directory setup
            page_dir = os.path.join(rasterized_dir, f"page_{i + 1:04d}")
            os.makedirs(page_dir, exist_ok=True)

            pix = page.get_pixmap(
                matrix=matrix,
                alpha=False,
                colorspace=fitz.csRGB
            )

            image_path = os.path.join(page_dir, f"page_{i + 1:04d}.{page_format}")
            pix.save(image_path)

            page_metadata = {
                    "page_index": i,
                    "page_number": i + 1,
                    "image_path": str(image_path),
                    "image_width": pix.width,
                    "image_height": pix.height,
                    "page_width": page.rect.width,
                    "page_height": page.rect.height,
                    "page_rotation": self._page_rotations.get(i, 0),
                    "dpi": dpi,
                    "scale": self._zoom,
                    "is_scanned": is_scanned_image(page)
            }

            pages_metadata.append(page_metadata)

            ## Save metadata
            metadata_path = os.path.join(page_dir, f"page_{i + 1:04d}.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(page_metadata, f, indent=2, ensure_ascii=False)

        return pages_metadata
    def _classify_page(self, page, page_metadata : dict) -> Tuple[List[dict], set]:
        """
            Method that classifies each element of a pdf page using classification model
            Each element is returned as a dictionary containing its class ID, name, confidence, bounding box and rotated bbox
            The dictionary is sorted by appearance order into the page left to right and top to bottom
        :param page: ('fitz.Page') Page to classify
        :param page_metadata: (dict) Metadata of the page
        :return: (list) List of dictionaries containing each element of the page and its classification
        """
        results = self._model.predict(
            page_metadata.get("image_path", ""),
            device=self._config.device,
            verbose=self._verbose,
            conf=0.25,
            save=True,
            save_dir=f"{self._output_dir}/predictions/page_{page_metadata.get('page_number'):04d}"
        )

        detected_blocks = []
        block_removed = set()
        for r in results:
            boxes = r.boxes

            cls_ids = boxes.cls.cpu().numpy().astype(int)  # Class IDs
            confidences = boxes.conf.cpu().numpy()  # Confidence score
            bboxes = boxes.xyxy.cpu().numpy()  # Bbox coordinate [x1, y1, x2, y2]

            class_names = [r.names[int(cls_id)] for cls_id in cls_ids]
            scale = page_metadata.get("scale", 1.0)

            # Récupérer la rotation appliquée à l'image
            rotation = page_metadata.get("page_rotation", 0)

            # Dimensions ORIGINALES de la page PDF (avant rotation)
            original_pdf_width = page_metadata.get("page_width")
            original_pdf_height = page_metadata.get("page_height")

            for i, (cls_id, conf, bbox, class_name) in enumerate(zip(cls_ids, confidences, bboxes, class_names)):
                pdf_bbox_rotated = image_bbox_to_pdf(bbox, scale)

                if rotation != 0:
                    pdf_bbox = transform_bbox_for_rotation(
                        pdf_bbox_rotated,
                        rotation,
                        original_pdf_width,
                        original_pdf_height
                    )
                else:
                    pdf_bbox = pdf_bbox_rotated


                ## In case of the detected class is an image, check if it's a scanned image
                if is_scanned_block(page=page, bbox=pdf_bbox, class_name=class_name):
                    class_name = "scanned-image"

                detection = {
                    "id": i,
                    "class_id": int(cls_id),
                    "class_name": class_name,
                    "confidence": float(conf),
                    "bbox_image": bbox,
                    "bbox_pdf": pdf_bbox,
                }

                detected_blocks.append(detection)

                if self._verbose:
                    print(f"Block #{i}: Class={class_name}({cls_id}), Confidence={conf:.3f}")
                    print(f"  Bbox Image: {bbox.tolist()}")
                    print(f"  Bbox PDF (rotated space): {pdf_bbox_rotated}")
                    print(f"  Bbox PDF (original space): {pdf_bbox}")
                    print(f"  Rotation: {rotation}°")

            ## Check if there are redundant blocks identified
            blocks_corrected, block_removed = correct_blocks_redundancy(
                blocks=detected_blocks,
                class_list=self._config.labels
            )

            ## Sort the detections block by appearance order into the page
            detected_blocks = sort_blocks_by_position(
                blocks=blocks_corrected
            )
        return detected_blocks, block_removed
    def _show_predictions(self, prediction_dict: dict, page):
        """
            Method that shows each prediction on the PDF page itself
            Store the pdf file with prediction boxes in the output directory
        :param prediction_dict: (dict) Dictionary containing each element of the page and its classification
        :param page: (fitz.Page) Page to show predictions on
        :return: None
        """
        blocks = prediction_dict.get("blocks", [])

        colors = {
            "text": (1, 0, 0),
            "title": (0, 1, 0),
            "picture": (0, 0, 1),
            "table": (1, 0.5, 0),
            "list-item": (0.5, 0, 0.5),
            "formula": (0, 1, 1),
            "footnote": (0.5, 0.5, 0),
            "page-footer": (1, 0.5, 0.5),
            "page-header": (0.5, 1, 0.5),
            "section-header": (0.5, 0.5, 1),
            "caption": (1, 0.5, 1),
        }

        for prediction in blocks:
            bbox = prediction.get("bbox_pdf", [])

            if not bbox or len(bbox) != 4:
                print(f"Invalid bbox: {bbox}")
                continue

            class_name = prediction.get("class_name", "").lower()
            confidence = prediction.get("confidence", 0)

            color = colors.get(class_name, (0.5, 0.5, 0.5))  # Gray by default

            ## Draw the rectangle on the page
            rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
            page.draw_rect(rect, color=color, width=1.5, fill=color, fill_opacity=0.2)

            ## Annotate the rectangle with the class name and confidence
            text_point = fitz.Point(bbox[0], bbox[1] - 5)
            page.insert_text(
                text_point,
                f"{class_name} ({confidence:.2f})",
                fontsize=8,
                color=color
            )

        ## Save annotated PDF
        annotated_pdf_path = os.path.join(self._output_dir, f"predictions/page_{prediction_dict.get("page_number", 0):04d}/debug")
        os.makedirs(annotated_pdf_path, exist_ok=True)

        print(f"Saving annotated PDF to {annotated_pdf_path}")

        img_annotated = page.get_pixmap(
            alpha=False
        )
        img_annotated.save(annotated_pdf_path + f"/page_{prediction_dict.get("page_number", 0):04d}_annotated.png")

    def classify(self, pdf_path: Path):
        """
            Méthod that classifies each element of a pdf page
        :param pdf_path: (Path) Path to the pdf file
        :return: (dict) Dictionary containing each element of the page and its classification
        """

        doc = fitz.open(pdf_path)
        ## Correct page rotation
        for i,page in enumerate(doc):
            self._page_rotations[i] = self._correct_page_rotation(page)

        ## Rasterize each pages
        pages_metadata = self._page_rasterization(
            doc=doc,
            dpi=self._dpi
        )

        pages_classifications : List[dict] = []
        for i, page in enumerate(doc):
            print(f"Processing page {i}")
            page_metadata = pages_metadata[i]

            page_dict = {
                "page_index": page_metadata.get("page_index"),
                "page_number": page_metadata.get("page_number"),
                "image_path": page_metadata.get("image_path"),
                "image_dimensions": {
                    "width": page_metadata.get("image_width"),
                    "height": page_metadata.get("image_height")
                },
                "pdf_dimensions": {
                    "width": page_metadata.get("page_width"),
                    "height": page_metadata.get("page_height")
                },
                "page_rotation": page_metadata.get("page_rotation"),
                "blocks": [],
                "removed_blocks": []
            }

            blocks, removed_blocks = self._classify_page(page=page, page_metadata=page_metadata)
            page_dict["blocks"] = blocks
            page_dict["removed_blocks"] = list(removed_blocks)

            ## Classify page
            pages_classifications.append(
                page_dict
            )

            ## Debug predictions
            self._show_predictions(
                prediction_dict=page_dict,
                page=page
            )

        ## Save page classifications
        with open( os.path.join(self._output_dir, "classifications.json"), "w", encoding="utf-8") as f:
            json.dump(pages_classifications, f, indent=2, cls=NumpyJSONEncoder, ensure_ascii=False)

        return pages_classifications