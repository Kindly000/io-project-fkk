import json
import os
from docx import Document
from docx.shared import Inches

from app_backend.logging_f import log_operations_on_file


def format_timestamp(seconds: int) -> str:
    """
    Converts a time duration in seconds into a formatted timestamp string.

    This function takes an integer value representing a time duration in seconds and converts it
    into a human-readable timestamp in the format `[HH:MM:SS]`.

    Args:
        seconds (int): The time duration in seconds to format.

    Returns:
        str: A formatted string representing the time duration in `[HH:MM:SS]` format,
             where `HH` is hours, `MM` is minutes, and `SS` is seconds, all zero-padded to two digits.

    Example:
        >>> format_timestamp(3661)
        '[01:01:01]'

        >>> format_timestamp(45)
        '[00:00:45]'

    Notes:
        - Handles durations longer than 24 hours (e.g., 90000 seconds -> '[25:00:00]').
        - The input should be a non-negative integer. Negative values may result in unexpected output.
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return f"[{hours:02}:{minutes:02}:{seconds:02}]"


def create_docx_file(note_title: str, note_summary: str,  note_content: list, docx_file_path: str, language: str ='pl') -> bool:
    """
    Creates a .docx file with structured content including a title, summary, and additional elements.

    This function generates a Word document (.docx) based on the provided title, summary, and content elements.
    The content may include text, speaker annotations, and images, each formatted appropriately. Headings in
    the document are language-sensitive, supporting both Polish and English.

    Args:
        note_title (str): The title of the note to include in the document.
        note_summary (str): A summary of the note, displayed below the title.
        note_content (list): A list of content elements. Each element is a dictionary with the following structure:
            - `type` (str): The type of content (`'img'`, `'speaker'`, or `'text'`).
            - `timestamp` (int): A timestamp in seconds, displayed as `[HH:MM:SS]`.
            - Additional keys based on the `type`:
                - `'img'`: Includes `file_path` (str), the path to the image.
                - `'speaker'`: Includes `name` (str), the speaker's name.
                - `'text'`: Includes `value` (str), the text content.
        docx_file_path (str): The file path where the .docx file will be saved.
        language (str, optional): The language for the document headings. Defaults to `'pl'` (Polish).
                                  Use `'en'` for English headings.

    Returns:
        bool: `True` if the file is successfully created, otherwise `False`.

    Behavior on Error:
        - Logs error details to the logging mechanism specified by `log_file_creation`.
        - Returns `False` if an exception occurs.

    Example:
        >>> note_content = [
        ...     {'type': 'speaker', 'timestamp': 45, 'name': 'John'},
        ...     {'type': 'img', 'timestamp': 90, 'file_path': 'diagram.png'},
        ...     {'type': 'text', 'timestamp': 120, 'value': 'This is the main note content.'}
        ... ]
        >>> create_docx_file("Project Update", "Overview of project status", note_content, "project_update.docx", language='en')
        True

    Notes:
        - This function requires the `python-docx` library to create Word documents.
        - Images are added with a width of 4 inches to maintain consistent formatting.

    Limitations:
        - Only supports adding images, speaker annotations, and plain text. Unsupported types are not handled.
        - Does not validate file paths for images; ensure images exist before calling this function.
    """
    title = "Title"
    summary = "Summary"
    if language == 'pl':
        title = "Tytuł"
        summary = "Podsumowanie"

    try:
        docx_file = Document()
        docx_file.add_heading(f"{title}: {note_title}", level=1)
        docx_file.add_heading(f"{summary}:", level=1)
        docx_file.add_paragraph(note_summary)
        docx_file.add_paragraph()

        for content in note_content:
            if content['type'] == 'img':
                docx_file.add_paragraph(format_timestamp(content['timestamp']))
                docx_file.add_picture(content['file_path'], width=Inches(4))
            elif content['type'] == 'speaker':
                docx_file.add_paragraph(f"{format_timestamp(content['timestamp'])} {content['name']}:")
            elif content['type'] == 'text':
                docx_file.add_paragraph(f"{format_timestamp(content['timestamp'])} {content['value']}")

        docx_file.save(docx_file_path)
        return True
    except Exception as e:
        log_operations_on_file(f"For create_docx_file() - Error: {e}")
        return False


def create_txt_file(note_title: str, note_summary: str, note_content: list, txt_file_path: str, language: str ='pl') -> bool:
    """
    Creates a .txt file with structured content including a title, summary, and text elements.

    This function generates a plain text (.txt) file based on the provided note title, summary, and content elements.
    The content includes speaker annotations and text elements, formatted with timestamps. Images are ignored.

    Args:
        note_title (str): The title of the note to include in the text file.
        note_summary (str): A summary of the note, added below the title.
        note_content (list): A list of content elements. Each element should be a dictionary with keys:
            - `type` (str): The type of content (`'img'`, `'speaker'`, or `'text'`).
            - `timestamp` (int): A timestamp in seconds, formatted as `[HH:MM:SS]`.
            - Additional keys depend on the type:
                - For `'speaker'`: `name` (str) specifies the speaker's name.
                - For `'text'`: `value` (str) specifies the text content.
        txt_file_path (str): The file path where the .txt file will be saved.
        language (str, optional): The language for the document headings. Defaults to `'pl'` (Polish).
                                  Use `'en'` for English headings.

    Returns:
        bool: `True` if the file is successfully created, otherwise `False`.

    Behavior on Error:
        - Logs error details to the logging mechanism specified by `log_file_creation`.
        - Returns `False` to indicate failure.

    Example:
        >>> note_content = [
        ...     {'type': 'speaker', 'timestamp': 30, 'name': 'Alice'},
        ...     {'type': 'text', 'timestamp': 60, 'value': 'This is a note content.'}
        ... ]
        >>> create_txt_file("Meeting Notes", "Summary of the meeting", note_content, "meeting_notes.txt", language='en')
        True

    Notes:
        - Images (`'img'` type) are skipped and not included in the text file.
        - The file is written with UTF-8 encoding for compatibility with various languages.
    """
    title = "Title"
    summary = "Summary"
    if language == 'pl':
        title = "Tytuł"
        summary = "Podsumowanie"

    try:
        with open(txt_file_path, "w", encoding='utf-8') as txt_file:
            txt_file.write(f"{title}: {note_title}\n")
            txt_file.write(f"{summary}:\n")
            txt_file.write(f"{note_summary}\n\n")

            for content in note_content:
                if content['type'] == 'speaker':
                    txt_file.write(f"{format_timestamp(content['timestamp'])} {content['name']}:\n")
                elif content['type'] == 'text':
                    txt_file.write(f"{format_timestamp(content['timestamp'])} {content['value']}\n")
        return True
    except Exception as e:
        log_operations_on_file(f"For create_txt_file() - Error: {e}")
        return False


def create_json_file(note_title: str, note_summary: str, note_content: list, note_datetime: str, video_file_name: str, docx_file_name: str, txt_file_name: str, json_file_path: str, language='pl') -> bool:
    """
    Creates a .json file with structured note information, including metadata, summary, and content details.

    This function generates a JSON file containing note metadata such as title, summary, and datetime, as well as a
    structured representation of the note's content. Content items can include text, speaker annotations, and images,
    each with a formatted timestamp.

    Args:
        note_title (str): The title of the note.
        note_summary (str): A summary of the note's content.
        note_content (list): A list of content elements. Each element should be a dictionary with keys:
            - `type` (str): The type of content (`'img'`, `'speaker'`, or `'text'`).
            - `timestamp` (int): A timestamp in seconds, formatted as `[HH:MM:SS]` in the output.
            - Additional keys depend on the type:
                - For `'img'`: `file_path` (str) specifies the image's file path.
                - For `'speaker'`: `name` (str) specifies the speaker's name.
                - For `'text'`: `value` (str) specifies the text content.
        note_datetime (str): The date and time of the note's creation or occurrence.
        video_file_name (str): The name of the associated video file.
        docx_file_name (str): The name of the associated DOCX file.
        txt_file_name (str): The name of the associated TXT file.
        json_file_path (str): The file path where the JSON file will be saved.
        language (str, optional): The language for the document headings. Defaults to `'pl'` (Polish).
                                  Use `'en'` for English headings.

    Returns:
        bool: `True` if the file is successfully created, otherwise `False`.

    JSON Structure:
        The generated JSON file will have the following structure:
        ```json
        {
            "note_id": "<file_name_without_extension>",
            "title": "<note_title>",
            "datetime": "<note_datetime>",
            "summary": "<note_summary>",
            "language": "<language>",
            "video": "<video_file_name>",
            "docx": "<docx_file_name>",
            "txt": "<txt_file_name>",
            "content": [
                {"type": "img", "val": "<image_file_name>", "timestamp_str": "[HH:MM:SS]"},
                {"type": "speaker", "val": "<speaker_name>", "timestamp_str": "[HH:MM:SS]"},
                {"type": "txt", "val": "<text_content>", "timestamp_str": "[HH:MM:SS]"}
            ]
        }
        ```

    Behavior on Error:
        - Logs error details to the logging mechanism specified by `log_file_creation`.
        - Returns `False` to indicate failure.

    Example:
        >>> note_content = [
        ...     {'type': 'img', 'timestamp': 60, 'file_path': 'image1.jpg'},
        ...     {'type': 'speaker', 'timestamp': 120, 'name': 'Alice'},
        ...     {'type': 'txt', 'timestamp': 180, 'value': 'This is a sample note content.'}
        ... ]
        >>> create_json_file(
        ...     "Meeting Notes",
        ...     "Summary of the meeting",
        ...     note_content,
        ...     "meeting_video.mp4",
        ...     "meeting_notes.docx",
        ...     "meeting_notes.txt",
        ...     "meeting_notes.json",
        ...     note_datetime="2024-11-29 10:00:00",
        ...     language='en'
        ... )
        True

    Notes:
        - JSON is written with UTF-8 encoding and formatted with an indentation of 4 spaces.
        - The `note_id` is derived from the JSON file name (excluding the `.json` extension).
    """
    data_content = []
    for content in note_content:
        if content['type'] == 'img':
            data_content.append({"type": "img", "val": f"{os.path.basename(content['file_path'])}", "timestamp_str": f"{format_timestamp(content['timestamp'])}"})
        elif content['type'] == 'speaker':
            data_content.append({"type": "speaker", "val": f"{content['name']}", "timestamp_str": f"{format_timestamp(content['timestamp'])}"})
        elif content['type'] == 'text':
            data_content.append({"type": "txt", "val": f"{content['value']}", "timestamp_str": f"{format_timestamp(content['timestamp'])}"})

    data = {
        "note_id": os.path.basename(json_file_path)[:-5], # -5 -> without .json
        "title": note_title,
        "datetime": note_datetime,
        "summary": note_summary,
        "language": language,
        "video": video_file_name,
        "docx": docx_file_name,
        "txt": txt_file_name,
        "content": data_content
    }

    try:
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        log_operations_on_file(f"For create_json_file() - Error: {e}")
        return False