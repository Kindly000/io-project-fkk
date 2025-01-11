import os
import re


def find_word_in_notes(directory_path: str, word: str) -> list[str]:
    """
    Searches for a specific word in all `.txt` files within a given directory.

    This function scans each `.txt` file in the specified directory and checks if the
    given word appears in the file's content. The search is case-insensitive and matches
    whole words only (not substrings). If the word is found in a file, the filename is
    added to the result list.

    Args:
        directory_path (str): The path to the directory containing `.txt` files to search.
        word (str): The word to search for within the files.

    Returns:
        list: A list of filenames where the word was found.

    Notes:
        - If a file cannot be opened due to encoding or file access issues, an error message
          will be printed, and the file will be skipped.
        - The function uses regular expressions to ensure whole-word matching.

    Example:
        >>> find_word_in_notes('/path/to/directory', 'example')
        ['file1.txt', 'file2.txt']
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
            except (UnicodeDecodeError, FileNotFoundError) as e:
                print(f"Nie można otworzyć pliku {filename}: {e}")

    return matching_files


