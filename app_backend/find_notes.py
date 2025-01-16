import os
import re
from app_backend.logging_f import log_operations_on_file


def find_word_in_notes(directory_path: str, word: str) -> list[str]:
    """
    Finds all text files in a directory that contain a specified word.

    This function scans all `.txt` files in a given directory and searches for a word, ensuring that the word
    is matched as a whole word (using word boundaries). If a file contains the word, it is added to the list of
    matching files. The function is case-insensitive and will return a list of filenames that contain the word.

    Args:
        directory_path (str): The path to the directory containing the `.txt` files to be searched.
        word (str): The word to search for within the text files.

    Returns:
        list[str]: A list of filenames (as strings) of the `.txt` files that contain the specified word.

    Error Handling:
        - Logs file operation errors using `log_operations_on_file`.

    Notes:
        - The search is case-insensitive.
        - The word is matched as a whole word using word boundaries (`\b`).
        - This function only processes files with a `.txt` extension.

    Example:
        >>> matching_files = find_word_in_notes("/path/to/notes", "important")
        >>> print(matching_files)
        ['note1.txt', 'note3.txt']
    """
    matching_files = []
    pattern = r'\b' + re.escape(word) + r'\b'

    for filename in os.listdir(directory_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(directory_path, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        if re.search(pattern, line, re.IGNORECASE):
                            matching_files.append(filename)
                            break
            except Exception as e:
                log_operations_on_file(f"[ERROR] find_word_in_notes({directory_path}, {word}): {repr(e)}")

    return matching_files


