import fitz
##
## Scanned Image detection
##

def image_coverage_ratio(page):
    """
        Function that computes the ratio of the image area covered by the page
    :param page: (fitz.Page) Page to compute the image coverage ratio for
    :return: (float) Image coverage ratio
    """
    page_area = page.rect.width * page.rect.height
    total_image_area = 0

    for img in page.get_images(full=True):
        xref = img[0]
        rects = page.get_image_rects(xref)
        for r in rects:
            total_image_area += r.width * r.height

    return total_image_area / page_area
def is_scanned_image(page) -> bool:
    """
        Function that checks if a page is a scanned image
        The image is considered scanned if:
             - It contains text
             - The image ratio is close to the page ratio
             - there is noise in the image

        Score >=5 : the page is a scanned image
        else : the page is not a scanned image
    :param page: (fitz.Page) Page to check if it's a scanned image
    :return: (bool) True if the page is a scanned image, False otherwise
    """
    score = 0
    ## Check if we can extract text
    if len(page.get_text("text").strip()) < 50:
        score += 3

    ## Check the ratio of image in the page
    if image_coverage_ratio(page) > 0.85:
        score += 3


    return score >= 5
def is_scanned_block(page, bbox, class_name : str) -> bool:
    """
        Function that checks if a spécific part of the page contains only scanned content
    :param page: (fitz.Page) Page to check
    :param bbox: (list[float]) Bounding box of the block to check
    :param class_name: (str) Class name of the block
    :return: (bool) True if the block contains only scanned content, False otherwise
    """
    if class_name == "picture":
        return is_scanned_image(page)
    elif class_name == "scanned-image":
        return True
    elif class_name == "table":
        ## Check if a table can be extracted from the page
        return len(page.find_tables(clip=fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3]))) == 0
    else:
        ## Check if the block contains text
        return len(page.get_textbox(rect=fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])).strip()) == 0