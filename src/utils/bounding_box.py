from typing import Tuple
import numpy as np

## Bounding box transformation functions
def image_bbox_to_pdf(bbox, scale):
    """
        Function that transforms a bbox from the image space to the PDF space
    :param bbox: ([x0, y0, x1, y1]) Bounding box in the image space
    :param scale: (float) Scale factor
    :return: ([x0, y0, x1, y1]) Bounding box in the PDF space
    """
    x0, y0, x1, y1 = bbox
    return [
        (x0 / scale) -5,
        (y0 / scale) -2,
        (x1 / scale) + 5,
        (y1 / scale) + 2
    ]
def transform_bbox_for_rotation(bbox, rotation, page_width, page_height):
    """
       Function that transforms a bbox according to the rotation of the page
    :param bbox: [x0, y0, x1, y1] Bounding box in the image space
    :param rotation: rotation angle (0, 90, 180, 270)
    :param page_width: width of the page PDF originale
    :param page_height: height of the page PDF originale
    :return: [x0, y0, x1, y1] Bounding box updated
    """
    x0, y0, x1, y1 = bbox

    if rotation == 0:
        return bbox
    elif rotation == 90:
        return [
            y0,
            page_width - x1,
            y1,
            page_width - x0
        ]
    elif rotation == 180:
        return [
            page_width - x1,
            page_height - y1,
            page_width - x0,
            page_height - y0
        ]
    elif rotation == 270:
        return [
            page_height - y1,
            x0,
            page_height - y0,
            x1
        ]

    return bbox

## Bounding box checking functions
def check_overlap(x: float, y: float, tolerance: int = 10) -> bool:
    """
        Function that checks if two points are close enough to be considered as overlapping
    :param x: (float)
    :param y: (float)
    :param tolerance: (int) Maximum distance between two points to consider them overlapping
    :return: (bool) True if the points are overlapping, False otherwise
    """
    return abs(x - y) <= tolerance
def is_superimposed(bbox_1, bbox_2, tolerance : int = 10) -> bool:
    """
        Function that checks if two bounding boxes are superimposed
    :param bbox_1: ([x0, y0, x1, y1]) first Bounding box
    :param bbox_2: ([x0, y0, x1, y1]) second Bounding box
    :param tolerance: (int) Maximum distance between two bounding boxes points to consider them superimposed
    :return: (bool) True if the bounding boxes are superimposed, False otherwise
    """
    return check_overlap(bbox_1[0], bbox_2[0], tolerance) and check_overlap(bbox_1[1], bbox_2[1], tolerance) and check_overlap(bbox_1[2], bbox_2[2], tolerance) and check_overlap(bbox_1[3], bbox_2[3], tolerance)
def overlaps(bbox_1, bbox_2) -> bool:
    """
        Function that checks if two bounding boxes overlap
    :param bbox_1: ([x0, y0, x1, y1]) first Bounding box
    :param bbox_2: ([x0, y0, x1, y1]) second Bounding box
    :return: (bool) True if the bounding boxes overlap, False otherwise
    """
    if bbox_1[2] < bbox_2[0]:
        return False
    if bbox_1[0] > bbox_2[2]:
        return False
    if bbox_1[3] < bbox_2[1]:
        return False
    if bbox_1[1] > bbox_2[3]:
        return False
    return True
def contained(bbox_1, bbox_2, tolerance : int = 10) -> bool:
    """
        Function that checks if bbox_1 is contained in bbox_2
    :param bbox_1: ([x0, y0, x1, y1]) first Bounding box
    :param bbox_2: ([x0, y0, x1, y1]) second Bounding box
    :param tolerance: (int) Maximum distance between two bounding boxes points to consider them contained
    :return: (bool) True if bbox_1 is contained in bbox_2, False otherwise
    """
    return (bbox_2[0] - tolerance) <= bbox_1[0] and \
        (bbox_2[1] - tolerance) <= bbox_1[1] and \
        (bbox_2[2] + tolerance) >= bbox_1[2] and \
        (bbox_2[3] + tolerance) >= bbox_1[3]

def identified_bbox_mask(image, blocks_list):
    if isinstance(image, np.ndarray):
        height, width = image.shape[:2]
    else:
        width, height = image.size

    xs = {0, width}
    ys = {0, height}

    clean_blocks = []

    ## Clamp each block bbox within the image width and height
    for bbox in blocks_list:
        if not bbox or len(bbox) != 4:
            continue

        x1, y1, x2, y2 = bbox
        x1, x2 = sorted((max(0, x1), min(width, x2)))
        y1, y2 = sorted((max(0, y1), min(height, y2)))

        clean_blocks.append((x1, y1, x2, y2))
        xs.update([x1, x2])
        ys.update([y1, y2])

    xs = sorted(xs)
    ys = sorted(ys)

    ## Create cells corresponding to the image
    cells = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):

            cell = (xs[i], ys[j], xs[i + 1], ys[j + 1])

            covered = False
            for bx in clean_blocks:
                if contained(cell, bx) or contained(bx, cell) or is_superimposed(cell, bx) or is_superimposed(bx, cell):
                    covered = True
                    break

            if not covered:
                cells.append(cell)


    ## Merge cells horizontaly
    lines = {}
    for r in cells:
        key = (r[1], r[3])  # y1, y2
        lines.setdefault(key, []).append(r)

    merged = []

    for (y1, y2), line_rects in lines.items():

        line_rects.sort(key=lambda r: r[0])

        current = line_rects[0]

        for r in line_rects[1:]:

            if r[0] == current[2]:
                current = (current[0], y1, r[2], y2)
            else:
                merged.append(current)
                current = r

        merged.append(current)



    return merged

def correct_blocks_redundancy(blocks : list, class_list : list[str]) -> Tuple[list, set]:
    """
        Function that checks if there are redundant blocks in the list
        Blocks are considered redundant if they have the same bounding box or if  the bounding box is contained in another block bounding boxe
    :param class_list: (list[str]) list of classifications classes to consider
    :param blocks: (list[dict]) list of blocks to check
    :return: (list[dict]) list of blocks without redundant blocks
    """
    blocks_to_keep = []
    blocks_to_remove = set()

    for i, block in enumerate(blocks):
        if i in blocks_to_remove:
            continue

        current_bbox = block["bbox_pdf"]
        current_class = block["class_name"]
        should_keep = True

        for j, other_block in enumerate(blocks):

            if i==j or j in blocks_to_remove:
                continue

            other_bbox = other_block["bbox_pdf"]
            other_class = other_block["class_name"]

            if is_superimposed(current_bbox, other_bbox):
                ## Choose the block to keep depending on the class
                print(current_class.lower(), other_class.lower())
                if current_class == other_class:
                    blocks_to_remove.add(j)
                elif (current_class.lower() in class_list and current_class.lower() not in ["table", "picture", "scanned-image"]) and other_class.lower() == "formula":
                    print(f"Remove other class {other_class.lower()}")
                    blocks_to_remove.add(j)
                elif (other_class.lower() in class_list and other_class.lower() not in ["table", "picture", "scanned-image"]) and current_class.lower() == "formula":
                    print(f"Remove current class {current_class.lower()}")
                    blocks_to_remove.add(i)
                elif current_class.lower() not in ["picture", "scanned-image"] and other_class.lower() in ["picture", "scanned-image"] :
                    print(f"Remove other class {other_class.lower()}")
                    blocks_to_remove.add(j)
                elif current_class.lower() in ["picture", "scanned-image"] and current_class.lower() not in ["picture", "scanned-image"] :
                    print(f"Remove current class {current_class.lower()}")
                    blocks_to_remove.add(i)
                elif other_class.lower() == "table" and current_class.lower() in ["picture", "scanned-image"]:
                    print(f"Remove current class {current_class.lower()}")
                    blocks_to_remove.add(i)
                elif current_class.lower() == "table" and other_class.lower() in ["picture", "scanned-image"]:
                    print(f"Remove current class {other_class.lower()}")
                    blocks_to_remove.add(j)
                else:
                    print(f"Remove no classes")
            ## If the other block is contained in the current block, keep the current block
            elif contained(current_bbox, other_bbox):
                should_keep = False
                break
                # Si l'autre bloc est contenu dans le bloc courant
            elif contained(other_bbox, current_bbox):
                blocks_to_remove.add(j)

        if should_keep and i not in blocks_to_remove:
            blocks_to_keep.append(block)

    return blocks_to_keep, blocks_to_remove
def sort_blocks_by_position(blocks : list[dict], y_tolerance: int = 10):
    """
        Function that sorts the blocks by their position on the page with their bbox_pdf coordinates

        Sorting parameters :
        bbox[1]  : y_min
        bbox[0]  : x_min

    :param blocks: (list[dict]) List of blocks to sort
    :param y_error: (int) Maximum distance between two blocks to consider them on the same line
    :return: (list[dict]) Sorted blocks
    """

    blocks_sorted = sorted(blocks, key=lambda x: x.get("bbox_pdf")[1])

    lines = []
    current_line = []

    for block in blocks_sorted:
        y = block["bbox_pdf"][1]

        if not current_line:
            current_line.append(block)
            continue

        last_y = current_line[0]["bbox_pdf"][1]

        if abs(y - last_y) <= y_tolerance:
            current_line.append(block)
        else:
            ## Sort the line with the x_min coordinate
            lines.append(sorted(current_line, key=lambda b: b["bbox_pdf"][0]))
            current_line = [block]

    if current_line:
        lines.append(sorted(current_line, key=lambda b: b["bbox_pdf"][0]))

    return [block for line in lines for block in line]