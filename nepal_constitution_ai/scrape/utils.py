import re

def clean_filename(title):
    """Clean the title to make it a valid filename"""
    # Remove invalid filename characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '', title)
    # Remove extra whitespace
    cleaned = '_'.join(cleaned.split())
    # Limit filename length
    cleaned = cleaned[:100]
    return cleaned + '.pdf'
