def find_key_by_filename(data, filename):
    """
    Search for a key in the JSON structure by matching the filename.
    
    :param data: JSON object (can be a dictionary or a list).
    :param filename: The filename to search for.
    :return: The key or parent key containing the filename, or None if not found.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict) or isinstance(value, list):
                # Recursively search in nested structures
                result = find_key_by_filename(value, filename)
                if result:
                    return key if isinstance(data, dict) else None
            elif key == "filename" and value.strip() == filename.strip():
                return key
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) or isinstance(item, list):
                # Recursively search in nested structures
                result = find_key_by_filename(item, filename)
                if result:
                    return result
    return None

def find_entry_by_filename(data, filename):
    """
    Search for an entry in the JSON structure by matching the filename.
    
    :param data: JSON object (can be a dictionary or a list).
    :param filename: The filename to search for.
    :return: The entire entry containing the filename, or None if not found.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict) or isinstance(value, list):
                # Recursively search in nested structures
                result = find_entry_by_filename(value, filename)
                if result:
                    return result
            elif key == "filename" and value.strip() == filename.strip():
                # Return the entire dictionary or list containing the matching filename
                return data
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) or isinstance(item, list):
                # Recursively search in nested structures
                result = find_entry_by_filename(item, filename)
                if result:
                    return result
    return None

