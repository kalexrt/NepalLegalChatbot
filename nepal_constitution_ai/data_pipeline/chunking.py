from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

def sentence_aware_chunking(text, chunk_size, chunk_overlap):
    sentences = re.split(r'(\n|  |\|)', text)
    chunks, current_chunk = [], ""

    for sentence in sentences:
        # Accumulate sentences until chunk_size is reached
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence
        else:
            # Append the current chunk
            chunks.append(current_chunk)
            
            # Start new chunk with overlap from the end of the last chunk
            overlap_start = max(0, len(current_chunk) - chunk_overlap)
            current_chunk = current_chunk[overlap_start:] + sentence

    # Append the last chunk if it has content
    if current_chunk:
        if len(current_chunk) > 200:
            chunks.append(current_chunk)
        else:
            # If the last chunk is too short, add it to the previous chunk
            chunks[-1] += current_chunk


    return chunks

def chunk_text_and_map_pages(doc, chunk_size, chunk_overlap):
    """
    Chunk concatenated Nepali text and map each chunk back to the page range it originated from.

    Parameters:
        pages (list): List of strings, where each string is the text content of a page.
        chunk_size (int): Maximum number of characters per chunk. Default is 100.
        chunk_overlap (int): Number of characters to overlap between chunks. Default is 20.

    Returns:
        list: List of dictionaries, each containing a chunk of text and the corresponding page range as a string.
    """

    pages = doc['pages']

    # Join all pages into a single string to maintain continuity across pages
    full_text = "\n".join(pages)

    # Calculate the starting index of each page in the concatenated full text
    page_start_indices = []
    current_index = 0
    for page_text in pages:
        page_start_indices.append(current_index)
        current_index += len(page_text) + 1  # +1 for the newline character between pages

    # # Initialize the RecursiveCharacterTextSplitter with chunking settings
    # text_splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=chunk_size,
    #     chunk_overlap=chunk_overlap,
    #     separators=["\n", " "]
    # )

    # Split the entire text into chunks
    chunks = sentence_aware_chunking(full_text, chunk_size, chunk_overlap)

    # Map each chunk to its corresponding page(s)
    chunks_dict_with_pagenum = []
    for chunk in chunks:
        # Find the start index of the chunk in the full text
        chunk_start_index = full_text.find(chunk)
        chunk_end_index = chunk_start_index + len(chunk)

        # Determine the pages the chunk spans
        chunk_pages = set()
        for page_num, page_start in enumerate(page_start_indices, start=1):
            page_end = page_start + len(pages[page_num - 1])
            # Check if the chunk overlaps with the page
            if (page_start <= chunk_start_index < page_end) or (page_start <= chunk_end_index <= page_end):
                chunk_pages.add(page_num)

        # Format page range as a string
        if len(chunk_pages) == 1:
            page_range = str(next(iter(chunk_pages)))
        else:
            page_range = f"{min(chunk_pages)}-{max(chunk_pages)}"

        # Append the chunk along with its page range to the results list
        chunks_dict_with_pagenum.append({
            "page": page_range,
            "text": chunk.strip(),
        })

    return chunks, chunks_dict_with_pagenum