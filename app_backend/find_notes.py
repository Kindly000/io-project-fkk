import os
import re


def find_word_in_notes(directory_path: str, word: str):
    """
    Searches for a word in .txt files within the specified directory.

    Args:
        directory_path (str): The path to the directory.
        word (str): The word to search for (case insensitive).

    Returns:
        list: A list of filenames (with .txt extension) that contain the word.
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

if __name__ == '__main__':
    print(find_word_in_notes('../tmp', 'CO'))


