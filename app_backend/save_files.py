from datetime import datetime
import os.path
import random
import shutil
from app_backend.create_files import create_docx_file, create_txt_file, create_json_file
from app_backend.communication_with_www_server import upload_file_on_server
import hashlib
import threading
from app_backend.logging_f import log_file_creation
import app_front.quickstart as google_cal


def create_note_id(note_title: str, note_datetime: str, language: str) -> str:
    """
    Generates a unique identifier (ID) for a note based on its title, datetime, and language.

    This function creates a unique hash string by concatenating the note title, language, datetime,
    and a random integer. The resulting string is then hashed using the SHA-256 algorithm to produce
    a fixed-length, cryptographically secure identifier.

    Args:
        note_title (str): The title of the note used as part of the ID generation.
        note_datetime (str): The datetime associated with the note, used to ensure uniqueness.
        language (str): The language code (e.g., 'en' or 'pl') used as part of the ID generation.

    Returns:
        str: A unique SHA-256 hash string that serves as the ID for the note.

    Example:
        >>> note_id = create_note_id("Meeting Notes", "01-02-2022 11:50:00", "en")
        >>> print(note_id)
        '5f4d2b89f...<hash_value>...'

    Notes:
        - This function uses the `hashlib` module to create the SHA-256 hash.
        - The function includes a random integer between 0 and 10,000 to increase the likelihood of uniqueness.
        - Ensure that the `hashlib` library is imported for this function to work properly.
        - The function returns a string of 64 hexadecimal characters.
    """
    v = f"{note_title}{language}{note_datetime}{str(random.randint(0,10000))}"
    hash_object = hashlib.sha256(v.encode('utf-8'))
    hash_str = hash_object.hexdigest()

    return hash_str


def sort_note_content(note_content: list) -> list:
    """
    Sorts a list of note content elements based on their timestamp and type.

    This function organizes the elements of a note's content in chronological order.
    If two elements have the same timestamp, they are further sorted based on their type
    according to a predefined order: 'img' (0), 'speaker' (1), and 'text' (2).

    Args:
        note_content (list): A list of dictionaries representing the content elements of a note.
                             Each dictionary must contain the following keys:
                             - `type` (str): The type of the content (`'img'`, `'speaker'`, or `'text'`).
                             - `timestamp` (int): The timestamp in seconds to be used for sorting.

    Returns:
        list: A new list of note content elements sorted first by timestamp and then by type.

    Example:
        >>> note_content = [
        ...     {'type': 'speaker', 'timestamp': 120, 'name': 'Alice'},
        ...     {'type': 'img', 'timestamp': 60, 'file_path': 'image.jpg'},
        ...     {'type': 'text', 'timestamp': 120, 'value': 'Some text content'}
        ... ]
        >>> sorted_content = sort_note_content(note_content)
        >>> print(sorted_content)
        [{'type': 'img', 'timestamp': 60, 'file_path': 'image.jpg'},
         {'type': 'speaker', 'timestamp': 120, 'name': 'Alice'},
         {'type': 'text', 'timestamp': 120, 'value': 'Some text content'}]

    Notes:
        - The function assumes that all dictionaries in the input list have the keys `type` and `timestamp`.
        - The sorting order for types is predefined: `img` is sorted first, then `speaker`, and `text` last.
        - This function uses a lambda function as the sorting key to achieve multi-level sorting.
    """
    type_order = {'img': 0, 'speaker': 1, 'text': 2}
    return sorted(note_content, key=lambda x: (x['timestamp'], type_order[x['type']]))


def send_and_delete_files(
        note_id: str,
        json_file_path: str,
        img_files_name: list,
        video_file_path: str,
        is_docx_file_created: bool,
        docx_file_path: str,
        is_docx_txt_created: bool,
        txt_file_path: str,
        tmp_dir_name: str
) -> None:
    """
    Sends files to a server and deletes them from the local temporary directory after uploading.

    This function handles the upload of various files associated with a specific note to the server.
    It uploads the JSON file, image files, and video file, and optionally uploads a DOCX or TXT file if created.
    Once all the files are uploaded, it deletes all files from the temporary directory to clean up.

    Args:
        note_id (str): The unique identifier of the note for which the files are being uploaded.
        json_file_path (str): The path to the JSON file that contains note data.
        img_files_name (list): A list of names of image files to be uploaded.
        video_file_path (str): The path to the video file to be uploaded.
        is_docx_file_created (bool): A flag indicating whether a DOCX file has been created.
        docx_file_path (str): The path to the DOCX file to be uploaded (if created).
        is_docx_txt_created (bool): A flag indicating whether a TXT file has been created.
        txt_file_path (str): The path to the TXT file to be uploaded (if created).
        tmp_dir_name (str): The name of tmp directory where are files.

    Returns:
        None: This function does not return a value. It performs file uploads and deletes files locally.

    Behavior on Failure:
        - The function assumes that the `upload_file_on_server` function handles errors during file upload.
        - If any file cannot be uploaded, the function does not retry or log the failure.

    Example:
        >>> send_and_delete_files(
        ...     note_id="12345",
        ...     json_file_path="note_data.json",
        ...     img_files_name=["image1.jpg", "image2.jpg"],
        ...     video_file_path="video.mp4",
        ...     is_docx_file_created=True,
        ...     docx_file_path="note.docx",
        ...     is_docx_txt_created=True,
        ...     txt_file_path="note.txt"
        ...     tmp_dir_name="notes_id_znadri"
        ... )

    Notes:
        - The function deletes directory '../tmp/{tmp_dir_name}' with all files after uploading, so use this with caution.
        - Ensure that the `upload_file_on_server` function is working correctly, as this function relies on it for uploads.
        - The `shutil` and `os` modules are used for file operations. Ensure they are imported at the top of the script.
    """
    upload_file_on_server(note_id, json_file_path)
    upload_file_on_server(note_id, video_file_path)
    for img_file in img_files_name:
        upload_file_on_server(note_id, f"../tmp/{tmp_dir_name}/{img_file}")

    if is_docx_file_created:
        upload_file_on_server(note_id, docx_file_path)
    if is_docx_txt_created:
        upload_file_on_server(note_id, txt_file_path)

    shutil.rmtree(f"../tmp/{tmp_dir_name}")


def save_files_to_user_directory(
        directory_path: str,
        tmp_dir_name: str,
        is_docx_file_created: bool,
        docx_file_path: str,
        is_txt_file_created: bool,
        txt_file_path: str,
        img_files_name: list,
        video_file_path: str
) -> None:
    """
    Copies specific files to a user-specified directory and logs any errors encountered during the process.

    This function checks if DOCX, TXT, image, and video files have been created and, if so, attempts to copy
    them to the specified directory. Any failures during the copying process are logged with detailed error
    messages to the file creation log.

    Args:
        directory_path (str): The path to the directory where the files should be saved.
        tmp_dir_name (str): The name of tmp directory where are files.
        is_docx_file_created (bool): A flag indicating if the DOCX file was created.
        docx_file_path (str): The path to the DOCX file to be copied.
        is_txt_file_created (bool): A flag indicating if the TXT file was created.
        txt_file_path (str): The path to the TXT file to be copied.
        img_files_name (list): A list of image file names to be copied from the temporary directory.
        video_file_path (str): The path to the video file to be uploaded.

    Returns:
        None: This function does not return a value. It performs file copying and logging.

    Behavior on Failure:
        - Logs the error to `error_logs/file_creation.log` with a timestamp, indicating the source of the failure.
        - If copying any file fails, the process continues with the next file.

    Example:
        >>> save_files_to_user_directory(
        ...     directory_path="../user_notes/",
        ...     tmp_dir_name="notes_id_znadri",
        ...     is_docx_file_created=True,
        ...     docx_file_path="note.docx",
        ...     is_txt_file_created=True,
        ...     txt_file_path="note.txt",
        ...     img_files_name=["image1.jpg", "image2.jpg"],
        ...     video_file_path="video.mp4"
        ... )

    Notes:
        - The `shutil` and `os` modules are used for file operations. Ensure they are imported at the top of the script.
        - The function handles each file type separately and logs any issues during the copying process.
        - The function assumes that the source files are located in the `../tmp/{tmp_dir_name}` directory for image.
        - The `error_logs/` directory should exist for logging; otherwise, the function will fail to log errors.
    """
    if is_docx_file_created:
        try:
            shutil.copyfile(docx_file_path, f'{directory_path}/{os.path.basename(docx_file_path)}')
        except Exception as e:
            log_file_creation(
                f"For save_files()->shutil.copyfile({docx_file_path}, {directory_path}/{os.path.basename(docx_file_path)}) - Error: {e} - Cannot copy file\n"
            )

    if is_txt_file_created:
        try:
            shutil.copyfile(txt_file_path, f'{directory_path}/{os.path.basename(txt_file_path)}')
        except Exception as e:
            log_file_creation(
                f"For save_files()->shutil.copyfile({txt_file_path}, {directory_path}/{os.path.basename(txt_file_path)}) - Error: {e} - Cannot copy file\n"
            )

    for img_file_name in img_files_name:
        try:
            shutil.copyfile(f"../tmp/{tmp_dir_name}/{img_file_name}", f'{directory_path}/{img_file_name}')
        except Exception as e:
            log_file_creation(
                f"For save_files()->shutil.copyfile(../tmp/{tmp_dir_name}/{img_file_name}, {directory_path}/{img_file_name}) - Error: {e} - Cannot copy file\n"
            )

    try:
        shutil.copyfile(video_file_path, f'{directory_path}/{os.path.basename(video_file_path)}')
    except Exception as e:
        log_file_creation(
            f"For save_files()->shutil.copyfile({video_file_path}, {directory_path}/{os.path.basename(video_file_path)}) - Error: {e} - Cannot copy file\n"
        )


def save_files(
    note_title: str,
    note_summary: str,
    note_datetime: str,
    note_content_img: list,
    note_content_text: list,
    note_content_speaker: list,
    video_file_name: str,
    tmp_dir_name: str,
    directory_path: str,
    language: str = 'pl'
) -> None:
    """
    Saves structured content from a note to specified directories and prepares files for upload to a server.

    This function organizes and compiles content from different parts of a note, creates various file formats
    (e.g., DOCX, TXT, JSON) and saves them to a designated directory. It then initiates a background process to
    upload the files to a server while handling file creation and potential errors.

    Args:
        note_title (str): The title of the note.
        note_summary (str): A brief summary of the note.
        note_datetime (str): The date and time when the note was created.
        note_content_img (list): A list of image content elements, each represented as a dictionary.
        note_content_text (list): A list of text content elements, each represented as a dictionary.
        note_content_speaker (list): A list of speaker content elements, each represented as a dictionary.
        video_file_name (str): The name of the video file.
        tmp_dir_name (str): The name of tmp directory where are files.
        directory_path (str): The path to the directory where the files should be saved.
        language (str, optional): The language for the document headings (`'pl'` for Polish or `'en'` for English).
                                  Defaults to `'pl'`.

    Returns:
        None: This function does not return a value. It performs file creation, saving, and initiates an upload.

    File Creation Process:
        - Organizes content into a single list and sorts it based on timestamp and type.
        - Generates a unique note ID and paths for DOCX, TXT, and JSON files.
        - Creates a DOCX and a TXT file with the note's content.
        - Copies the created files and other media (images and video) to the specified directory.

    Upload Process:
        - Initiates a background thread to upload the created files (JSON, DOCX, TXT, images, and video) to the server.
        - Deletes temporary files after uploading to maintain a clean working directory.

    Behavior on Failure:
        - Logs errors related to file creation, saving, or uploading with timestamps to `error_logs/file_creation.log`.

    Example:
        >>> save_files(
        ...     note_title="Project Notes",
        ...     note_summary="Summary of project notes",
        ...     note_datetime="01-02-2022 11:50:00",
        ...     note_content_img=[{'type': 'img', 'timestamp': 45, 'file_path': 'image1.png'}],
        ...     note_content_text=[{'type': 'text', 'timestamp': 60, 'value': 'Text content'}],
        ...     note_content_speaker=[{'type': 'speaker', 'timestamp': 30, 'name': 'Alice'}],
        ...     video_file_name="video",
        ...     tmp_dir_name="notes_id_znadri",
        ...     directory_path='../user_notes',
        ...     language='en'
        ... )

    Notes:
        - Ensure the `python-docx` library is installed for DOCX file creation.
        - Ensure `shutil`, `os`, `threading`, and `datetime` libraries are imported and available.
        - The `../tmp/{tmp_dir_name}` directory should be writable for temporary file creation.
        - The function assumes that images have the `.png` extension for image processing.
        - The `error_logs/` directory should exist for error logging; otherwise, logging will fail silently.
    """
    note_content = []
    note_content.extend(note_content_img)
    note_content.extend(note_content_speaker)
    note_content.extend(note_content_text)

    note_content = sort_note_content(note_content)
    note_id = create_note_id(note_title, note_datetime, language)

    docx_file_name = f"{note_title} {note_datetime}.docx"
    docx_file_path = f"../tmp/{tmp_dir_name}/{docx_file_name}"
    txt_file_name =  f"{note_title} {note_datetime}.txt"
    txt_file_path = f"../tmp/{tmp_dir_name}/{txt_file_name}"
    json_file_path = f"../tmp/{tmp_dir_name}/{note_id}.json"
    video_file_path = f"../tmp/{tmp_dir_name}/{video_file_name}"
    img_files_name = [f for f in os.listdir(f"../tmp/{tmp_dir_name}") if f.endswith('.png')]

    is_docx_file_created = create_docx_file(note_title, note_summary, note_content, docx_file_path=docx_file_path, language=language)
    is_txt_file_created = create_txt_file(note_title, note_summary, note_content, txt_file_path=txt_file_path, language=language)

    save_files_to_user_directory(directory_path, tmp_dir_name, is_docx_file_created, docx_file_path, is_txt_file_created, txt_file_path, img_files_name, video_file_path)

    if create_json_file(note_title, note_summary, note_content, note_datetime, video_file_name=video_file_name, docx_file_name=docx_file_name, txt_file_name=txt_file_name, json_file_path=json_file_path, language=language):
        threading.Thread(
            send_and_delete_files(note_id, json_file_path, img_files_name, video_file_path, is_docx_file_created,
                                  docx_file_path, is_txt_file_created, txt_file_path, tmp_dir_name)
        )

    google_ = google_cal.Calendar()
    google_.add_event(note_title, datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), f"https://ioprojekt.atwebpages.com/{note_id}")