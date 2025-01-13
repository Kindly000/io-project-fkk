import json
import os
from app_backend.communication_with_www_server import upload_file_on_server
from app_backend.logging_f import log_operations_on_file
from app_backend.save_files import delete_directory, copy_file


def check_and_create_unsuccessful_uploads_folder():
    """
    Checks if the 'unsuccessful_uploads' directory exists in the parent folder.
    If it does not exist, the directory is created.

    This function ensures that a dedicated folder for unsuccessful uploads
    is present before further operations that may involve storing files in it.

    Returns:
        None
    """
    if not os.path.exists('../unsuccessful_uploads'):
        os.mkdir('../unsuccessful_uploads')


def save_unsuccessful_upload(note_id: str, file_path: str) -> None:
    """
    Saves details of an unsuccessful file upload for a given note.

    This function handles two primary tasks:
    1. Copies the file associated with the unsuccessful upload to a dedicated directory,
       creating a subdirectory for the specific note ID if it doesn't already exist.
    2. Updates a JSON file (`failed_files.json`) to log the details of the unsuccessful upload,
       including the note ID and file name.

    Args:
        note_id (str): The unique identifier of the note associated with the upload.
        file_path (str): The path to the file that failed to upload.

    Directory structure:
        - Files are stored under `../unsuccessful_uploads/<note_id>/<file_name>`.
        - The JSON log file is stored at `../unsuccessful_uploads/failed_files.json`.

    JSON log format:
        {
            "elements": [
                {
                    "dir_name": "<note_id>",
                    "dir_content": [
                        {
                            "note_id": "<note_id>",
                            "file_name": "<file_name>"
                        }
                    ]
                }
            ]
        }

    Notes:
        - If the JSON file already contains an entry for the specified note ID,
          the new file is appended to the existing entry.
        - If the file is already located at the target path, it will silently skip copying.
        - If the `../unsuccessful_uploads` or subdirectories do not exist, they are created automatically.

    Exceptions:
        - Silently handles `shutil.SameFileError` if the source and destination file paths are the same.

    Example:
        >>> save_unsuccessful_upload("80dd89ff24bd287237c31639ed6eff5b6a7e854a9e0b2b919598d1798bccf5bd", "example.txt")
    """
    check_and_create_unsuccessful_uploads_folder()
    dir_for_unsuccessful_uploads = '../unsuccessful_uploads'
    fail_file_name = os.path.basename(file_path)
    try:
        if not os.path.exists(f'{dir_for_unsuccessful_uploads}/{note_id}'):
            os.mkdir(f'{dir_for_unsuccessful_uploads}/{note_id}')
        copy_file(file_path, f'{dir_for_unsuccessful_uploads}/{note_id}/{fail_file_name}')
    except Exception as e:
        log_operations_on_file(f"For save_unsuccessful_upload({note_id}, {file_path}) - os.mkdir Error: {e}")

    json_path = f'{dir_for_unsuccessful_uploads}/failed_files.json'
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"elements": []}

    is_added = False
    for element in data["elements"]:
        if element["dir_name"] == note_id:
            new_dir_content = {
                "note_id": note_id,
                "file_name": fail_file_name
            }
            element["dir_content"].append(new_dir_content)
            is_added = True
            break

    if not is_added:
        new_element = {
            "dir_name": note_id,
            "dir_content": [
                {
                    "note_id": note_id,
                    "file_name": fail_file_name
                }
            ]
        }
        data["elements"].append(new_element)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def send_failed_files() -> None:
    """
    Attempts to upload files stored in a directory for unsuccessful uploads.

    This function processes a JSON file located in the `../unsuccessful_uploads` directory
    that tracks failed file uploads. For each entry in the JSON file:
    - Attempts to re-upload the files using the `upload_file_on_server` function.
    - If a file is successfully uploaded, it is deleted from the local filesystem.
    - If all files in a directory are successfully uploaded, the directory is removed.
    - If some files in a directory still fail to upload, the JSON file is updated to reflect the remaining files.

    If the JSON file does not exist or contains no elements, the function exits without performing any action.

    Exceptions:
        - `FileNotFoundError`: If a file listed in the JSON is not found during upload, it is ignored.

    Notes:
        - The `upload_file_on_server` function must be implemented separately and is assumed to handle the actual upload logic.
        - The function modifies the `failed_files.json` file to reflect the current status of uploads.

    Returns:
        None

    Example:
        >>> send_failed_files()
    """
    check_and_create_unsuccessful_uploads_folder()
    dir_for_unsuccessful_uploads = '../unsuccessful_uploads'
    json_path = f'{dir_for_unsuccessful_uploads}/failed_files.json'

    if not os.path.exists(json_path):
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    elements = data["elements"]
    if len(elements) == 0:
        return

    failed_elements = []
    for element in elements:
        failed_dir_content = []
        for dir_content in element["dir_content"]:
            note_id = dir_content["note_id"]
            file_name = dir_content["file_name"]
            file_path = f'{dir_for_unsuccessful_uploads}/{note_id}/{file_name}'

            try:
                if upload_file_on_server(note_id, file_path):
                    os.remove(file_path)
                else:
                    failed_dir_content.append(dir_content)
            except FileNotFoundError:
                pass
            except Exception as e:
                log_operations_on_file(f"For send_failed_files() - os.remove Error: {e}")
        if len(failed_dir_content) == 0:
            delete_directory(f'{dir_for_unsuccessful_uploads}/{element["dir_name"]}')
        else:
            element["dir_content"] = failed_dir_content
            failed_elements.append(element)

    data["elements"] = failed_elements
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)