import re

def normalize_text(text : str) -> str:
    """
        Function to normalize the text by replacing '\n' by ' ' and removing redundant ' '
    :param text: (str) text to be normalized
    :return: (str) normalized text
    """
    text = text.strip()
    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('\r', ' ')

    text = re.sub(r'\s+', ' ', text)

    if text == ' ':
        return ''
    else:
        return text
def is_empty(text : str) -> bool:
    if text.replace(" ", "") != "":
        return True
    else:
        return False