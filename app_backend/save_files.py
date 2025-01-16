from datetime import datetime
import os.path
import random
import shutil
from app_backend.create_files import create_docx_file, create_txt_file, create_json_file
from app_backend.communication_with_www_server import upload_file_on_server
import hashlib
import threading
from app_backend.logging_f import log_operations_on_file, app_logs
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

    Notes:
        - This function uses the `hashlib` module to create the SHA-256 hash.
        - The function includes a random integer between 0 and 10,000 to increase the likelihood of uniqueness.
        - Ensure that the `hashlib` library is imported for this function to work properly.
        - The function returns a string of 64 hexadecimal characters.

    Example:
        >>> note_id = create_note_id("Meeting Notes", "01-02-2022 11:50:00", "en")
        >>> print(note_id)
        '5f4d2b89f...<hash_value>...'
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

    Notes:
        - The function assumes that all dictionaries in the input list have the keys `type` and `timestamp`.
        - The sorting order for types is predefined: `img` is sorted first, then `speaker`, and `text` last.
        - This function uses a lambda function as the sorting key to achieve multi-level sorting.

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
    """
    type_order = {'img': 0, 'speaker': 1, 'text': 2}
    return sorted(note_content, key=lambda x: (x['timestamp'], type_order[x['type']]))


def delete_directory(directory_path: str) -> bool:
    """
    Deletes a directory and its contents.

    This function attempts to delete a specified directory along with all its files and subdirectories.
    If the operation is successful, it returns `True`. If an error occurs during the deletion process,
    it logs the error and returns `False`.

    Args:
        directory_path (str): The path to the directory to be deleted.

    Returns:
        bool: `True` if the directory was deleted successfully. `False` if an error occurred.

    Error Handling:
        - Logs errors during the directory deletion process using `log_operations_on_file`.

    Notes:
        - Uses `shutil.rmtree()` to recursively delete the directory and its contents.
        - Ensure that the provided `directory_path` is correct to avoid accidental deletions.

    Example:
        >>> success = delete_directory("/path/to/directory")
        >>> if success:
        ...     print("Directory deleted successfully.")
        ... else:
        ...     print("Failed to delete the directory.")
    """
    try:
        shutil.rmtree(directory_path)
        return True
    except Exception as e:
        log_operations_on_file(f"[ERROR] delete_directory({directory_path}): {repr(e)}")
        return False


def copy_file(file_path: str, destination_file_path: str) -> bool:
    """
    Copies a file from one location to another.

    This function copies a file from the specified source (`file_path`) to the destination (`destination_file_path`).
    If the copy operation is successful, it returns `True`. If an error occurs during the copying process,
    it logs the error and returns `False`.

    Args:
        file_path (str): The path to the source file to be copied.
        destination_file_path (str): The path to the destination where the file should be copied.

    Returns:
        bool: `True` if the file was copied successfully. `False` if an error occurred.

    Error Handling:
        - Logs errors during the file copy process using `log_operations_on_file`.

    Notes:
        - Uses `shutil.copyfile()` to copy the file.
        - Ensure that both the source and destination file paths are valid.

    Example:
        >>> success = copy_file("example.txt", "/path/to/destination/example.txt")
        >>> if success:
        ...     print("File copied successfully.")
        ... else:
        ...     print("Failed to copy the file.")
    """
    try:
        shutil.copyfile(file_path, destination_file_path)
        return True
    except Exception as e:
        log_operations_on_file(f"[ERROR] copy_file({file_path}, {destination_file_path}): {repr(e)}")
        return False


def send_files_on_server_with_delete_directory(
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
    Uploads multiple files to a server and deletes the temporary directory.

    This function uploads a set of files (such as images, JSON, video, and optional text and DOCX files)
    associated with a specific note to the server. If any file fails to upload, it is saved for a retry later.
    After all files are processed, it deletes the temporary directory used for storing the files.

    Args:
        note_id (str): The unique identifier of the note associated with the files.
        json_file_path (str): The path to the JSON file to be uploaded.
        img_files_name (list): A list of image file names to be uploaded.
        video_file_path (str): The path to the video file to be uploaded.
        is_docx_file_created (bool): A flag indicating if the DOCX file is created and should be uploaded.
        docx_file_path (str): The path to the DOCX file to be uploaded (if created).
        is_docx_txt_created (bool): A flag indicating if the TXT file is created and should be uploaded.
        txt_file_path (str): The path to the TXT file to be uploaded (if created).
        tmp_dir_name (str): The name of the temporary directory containing the files to be uploaded.

    Returns:
        None

    Error Handling:
        - Logs failed uploads using `app_logs`.
        - Saves failed uploads for later retries using `save_unsuccessful_upload`.
        - The function will log each step of the upload process, including success or failure.

    Notes:
        - The function attempts to upload all specified files, including images, video, and text files.
        - If any file fails to upload, it is saved for a retry attempt.
        - Deletes the temporary directory once all file uploads are completed.

    Example:
        >>> send_files_on_server_with_delete_directory("12345", "note.json", ["img1.jpg", "img2.jpg"], "video.mp4", True, "note.docx", True, "note.txt", "tmp123")
        >>> # This will upload the files associated with the note and delete the temporary directory.
    """
    files_to_send = [f"../tmp/{tmp_dir_name}/{img_file}" for img_file in img_files_name]
    files_to_send.append(json_file_path)
    files_to_send.append(video_file_path)

    if is_docx_file_created:
        files_to_send.append(docx_file_path)
    if is_docx_txt_created:
        files_to_send.append(txt_file_path)

    from app_backend.retry_logic import save_unsuccessful_upload
    for file_path in files_to_send:
        if not upload_file_on_server(note_id, file_path):
            app_logs(f"[FAILED] Upload file {os.path.basename(file_path)}")
            if not save_unsuccessful_upload(note_id, file_path):
                app_logs(f"[FAILED] Save unsuccessful uploaded file {os.path.basename(file_path)}")
            else:
                app_logs(f"[SUCCESS] Save unsuccessful uploaded file {os.path.basename(file_path)}")
        else:
            app_logs(f"[SUCCESS] Upload file {os.path.basename(file_path)}")

    delete_directory(f"../tmp/{tmp_dir_name}")


def save_audio_and_video_files_to_user_directory(
        directory_path: str,
        tmp_dir_name: str,
        audio_file_path: str,
        video_file_path: str
) -> bool:
    """
    Saves audio and video files to a user directory with detailed logging.

    This function creates a subdirectory within the specified directory path if it does not already exist.
    It then attempts to copy the specified audio and video files into this subdirectory. Logs are generated
    to indicate the success or failure of each operation.

    Args:
        directory_path (str): The base directory path where the files will be saved.
        tmp_dir_name (str): The name of the temporary subdirectory to be created within the base directory.
        audio_file_path (str): The path to the audio file to be copied.
        video_file_path (str): The path to the video file to be copied.

    Returns:
        bool: `True` if both files are successfully copied to the directory. `False` otherwise.

    Error Handling:
        - Uses the `copy_file` function for copying files, which handles file copy errors.
        - Logs errors and successes for each file operation using `app_logs`.

    Notes:
        - Ensures the directory structure is created before attempting to copy files.
        - Generates logs for each file, indicating whether the operation was successful or failed.
        - Returns `False` if any of the file copy operations fail, but continues to process remaining files.

    Example:
        >>> success = save_audio_and_video_files_to_user_directory("/user/files", "tmp123", "audio.mp3", "video.mp4")
        >>> if success:
        ...     print("Files saved successfully.")
        ... else:
        ...     print("Failed to save files.")
    """

    if not os.path.exists(f'{directory_path}/{tmp_dir_name}'):
        os.mkdir(f'{directory_path}/{tmp_dir_name}')
    directory_path = f'{directory_path}/{tmp_dir_name}'
    return_value = True
    if not copy_file(video_file_path, f'{directory_path}/{os.path.basename(video_file_path)}'):
        app_logs(f"[FAILED] Save {os.path.basename(video_file_path)} in {directory_path}")
        return_value = False
    else:
        app_logs(f"[SUCCESS] Save {os.path.basename(video_file_path)} in {directory_path}")

    if not copy_file(audio_file_path, f'{directory_path}/{os.path.basename(audio_file_path)}'):
        app_logs(f"[FAILED] Save {os.path.basename(audio_file_path)} in {directory_path}")
        return_value = False
    else:
        app_logs(f"[SUCCESS] Save {os.path.basename(video_file_path)} in {directory_path}")

    return return_value


def save_final_files_to_user_directory(
        directory_path: str,
        tmp_dir_name: str,
        is_docx_file_created: bool,
        docx_file_path: str,
        is_txt_file_created: bool,
        txt_file_path: str,
        img_files_name: list,
        video_file_path: str
) -> bool:
    """
    Saves final files, including documents, images, and videos, to a user directory with logging.

    This function creates a subdirectory within the specified directory path if it does not already exist.
    It then attempts to copy the specified files (e.g., images, documents, and video) into this subdirectory.
    Success or failure of each file operation is logged.

    Args:
        directory_path (str): The base directory path where the files will be saved.
        tmp_dir_name (str): The name of the temporary subdirectory to be created within the base directory.
        is_docx_file_created (bool): Whether a DOCX file is to be saved.
        docx_file_path (str): The path to the DOCX file to be copied (if created).
        is_txt_file_created (bool): Whether a TXT file is to be saved.
        txt_file_path (str): The path to the TXT file to be copied (if created).
        img_files_name (list): A list of image file names to be saved.
        video_file_path (str): The path to the video file to be copied.

    Returns:
        bool: `True` if all files are successfully copied to the directory. `False` if any file fails to copy.

    Error Handling:
        - Uses the `copy_file` function for copying files, which handles file copy errors.
        - Logs errors and successes for each file operation using `app_logs`.

    Notes:
        - Ensures the directory structure is created before attempting to copy files.
        - Checks for the existence of optional files (e.g., DOCX and TXT) and includes them if present.
        - Continues processing remaining files even if some file operations fail.

    Example:
        >>> success = save_final_files_to_user_directory(
        ...     "/user/files", "tmp123", True, "document.docx", True, "summary.txt",
        ...     ["image1.png", "image2.jpg"], "video.mp4"
        ... )
        >>> if success:
        ...     print("Files saved successfully.")
        ... else:
        ...     print("Failed to save some files.")
    """
    if not os.path.exists(f'{directory_path}/{tmp_dir_name}'):
        os.mkdir(f'{directory_path}/{tmp_dir_name}')
    directory_path = f'{directory_path}/{tmp_dir_name}'

    files_path_to_save = [f"../tmp/{tmp_dir_name}/{img_file_name}" for img_file_name in img_files_name]
    if is_docx_file_created:
        files_path_to_save.append(docx_file_path)
    if is_txt_file_created:
        files_path_to_save.append(txt_file_path)

    files_path_to_save.append(video_file_path)

    return_value = True
    for file_path in files_path_to_save:
        if not copy_file(file_path, f"{directory_path}/{os.path.basename(file_path)}"):
            app_logs(f"[FAILED] Save {os.path.basename(file_path)} in {directory_path}")
            return_value = False
        else:
            app_logs(f"[SUCCESS] Save file {os.path.basename(file_path)} in {directory_path}")

    return return_value


def save_files(
    note_title: str,
    note_summary: str,
    note_datetime: datetime,
    note_content_img: list,
    note_content_text: list,
    note_content_speaker: list,
    video_file_path: str,
    tmp_dir_name: str,
    directory_path: str,
    send_to_server: bool,
    language: str = 'pl'
) -> None:
    """
    Saves and manages files related to a note, including DOCX, TXT, JSON, and video files, with options
    for local storage and server upload.

    This function processes and organizes note content, creates files, and stores them locally.
    If specified, it also handles sending files to a server and adds an event to Google Calendar.

    Args:
        note_title (str): The title of the note.
        note_summary (str): A summary of the note's content.
        note_datetime (datetime): The datetime of the note.
        note_content_img (list): List of image-related content for the note.
        note_content_text (list): List of text-related content for the note.
        note_content_speaker (list): List of speaker-related content for the note.
        video_file_path (str): Path to the video file associated with the note.
        tmp_dir_name (str): Temporary directory name for processing files.
        directory_path (str): The base directory for saving final files.
        send_to_server (bool): Flag indicating whether files should be uploaded to the server.
        language (str, optional): Language setting for file creation. Defaults to 'pl'.

    Returns:
        None

    Workflow:
        1. Combines and sorts all note content (images, text, speakers).
        2. Generates a unique note ID based on the title, datetime, and language.
        3. Creates DOCX and TXT files based on the note content.
        4. Saves all processed files to a user-specified directory.
        5. If `send_to_server` is True:
            - Creates a JSON metadata file for the note.
            - Uploads all files (including JSON, DOCX, TXT, images, and video) to the server.
            - Deletes the temporary processing directory after upload.
            - Adds a calendar event with a link to the note's server location.
        6. If `send_to_server` is False, deletes the temporary directory after processing.

    Error Handling:
        - Ensures temporary directories are deleted in both local and server workflows.
        - Logs successes and failures at each step using `app_logs`.
        - Handles file creation and upload failures gracefully.

    Example:
        >>> save_files(
        ...     note_title="Meeting Notes",
        ...     note_summary="Discussion about project milestones.",
        ...     note_datetime=datetime(2025, 1, 15, 14, 30),
        ...     note_content_img=[{"file_path": "image1.png", "timestamp": 123}],
        ...     note_content_text=[{"value": "Initial project proposal", "timestamp": 345}],
        ...     note_content_speaker=[{"name": "Alice", "timestamp": 456}],
        ...     video_file_path="meeting_video.mp4",
        ...     tmp_dir_name="temp123",
        ...     directory_path="/user/notes",
        ...     send_to_server=True,
        ...     language="en"
        ... )
    """
    note_content = []
    note_content.extend(note_content_img)
    note_content.extend(note_content_speaker)
    note_content.extend(note_content_text)

    note_content = sort_note_content(note_content)
    note_id = create_note_id(note_title, note_datetime.strftime("%Y-%m-%d %H:%M:%S"), language)

    docx_file_name = f"{note_title} {note_datetime.strftime("%Y-%m-%d %H-%M-%S")}.docx"
    docx_file_path = f"../tmp/{tmp_dir_name}/{docx_file_name}"
    txt_file_name =  f"{note_title} {note_datetime.strftime("%Y-%m-%d %H-%M-%S")}.txt"
    txt_file_path = f"../tmp/{tmp_dir_name}/{txt_file_name}"
    json_file_path = f"../tmp/{tmp_dir_name}/{note_id}.json"
    video_file_name = os.path.basename(video_file_path)
    img_files_name = [f for f in os.listdir(f"../tmp/{tmp_dir_name}") if f.endswith('.png')]

    is_docx_file_created = create_docx_file(note_title, note_summary, note_content, docx_file_path=docx_file_path, language=language)
    is_txt_file_created = create_txt_file(note_title, note_summary, note_content, txt_file_path=txt_file_path, language=language)

    save_final_files_to_user_directory(directory_path, tmp_dir_name, is_docx_file_created, docx_file_path,
                                       is_txt_file_created, txt_file_path, img_files_name, video_file_path)

    if send_to_server:
        if create_json_file(note_title, note_summary, note_content, note_datetime.strftime("%Y-%m-%d %H:%M:%S"), video_file_name=video_file_name, docx_file_name=docx_file_name, txt_file_name=txt_file_name, json_file_path=json_file_path, language=language):
            threading.Thread(
                send_files_on_server_with_delete_directory(note_id, json_file_path, img_files_name, video_file_path,
                                                           is_docx_file_created, docx_file_path, is_txt_file_created,
                                                           txt_file_path, tmp_dir_name)
            )
            google_cal.Calendar().add_event(note_title, note_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                                            f"https://ioprojekt.atwebpages.com/{note_id}")
    else:
        delete_directory(f"../tmp/{tmp_dir_name}")