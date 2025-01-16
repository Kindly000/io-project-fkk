import json
import os
from app_backend.communication_with_www_server import upload_file_on_server
from app_backend.logging_f import log_operations_on_file
from app_backend.save_files import delete_directory, copy_file


def check_and_create_unsuccessful_uploads_folder() -> None:
    """
    Checks if the 'unsuccessful_uploads' directory exists in the parent folder.
    If it does not exist, the directory is created.

    This function ensures that a dedicated folder for unsuccessful uploads
    is present before further operations that may involve storing files in it.

    Returns:
        None

    Example:
        >>> check_and_create_unsuccessful_uploads_folder()
    """
    if not os.path.exists('../unsuccessful_uploads'):
        os.mkdir('../unsuccessful_uploads')


def save_unsuccessful_upload(note_id: str, file_path: str) -> bool:
    """
        Saves an unsuccessful file upload by storing it in a specific directory and updating a JSON log.

        This function handles the case when a file upload fails. It saves the file to a designated folder
        (`../unsuccessful_uploads`) organized by `note_id`, and updates a JSON file (`failed_files.json`)
        to keep track of the failed uploads. If a folder for the `note_id` doesn't exist, it is created.
        The file is copied to the appropriate folder and the JSON log is updated with the new failed upload.

        Args:
            note_id (str): The unique identifier of the note related to the failed upload.
            file_path (str): The local path of the file that failed to upload.

        Returns:
            bool: `True` if the file was successfully saved and the JSON file was updated. `False` if an error occurred.

        Error Handling:
            - Logs errors during file operations using `log_operations_on_file`.

        Notes:
            - The function ensures the existence of the `unsuccessful_uploads` folder before saving the file.
            - If a directory for a specific `note_id` does not exist, it is created.
            - Updates or creates a JSON file `failed_files.json` to track the failed uploads.
            - Uses the `copy_file` function to move the file to the appropriate directory.

        Example:
            >>> success = save_unsuccessful_upload("80dd89ff24bd287237c31639ed6eff5b6a7e854a9e0b2b919598d1798bccf5bd", "example.pdf")
            >>> if success:
            ...     print("Failed upload saved successfully.")
            ... else:
            ...     print("Failed to save the unsuccessful upload.")
    """
    check_and_create_unsuccessful_uploads_folder()
    dir_for_unsuccessful_uploads = '../unsuccessful_uploads'
    fail_file_name = os.path.basename(file_path)
    try:
        if not os.path.exists(f'{dir_for_unsuccessful_uploads}/{note_id}'):
            os.mkdir(f'{dir_for_unsuccessful_uploads}/{note_id}')
        if not copy_file(file_path, f'{dir_for_unsuccessful_uploads}/{note_id}/{fail_file_name}'):
            return False
    except Exception as e:
        log_operations_on_file(f"[ERROR] save_unsuccessful_upload({note_id}, {file_path}): {repr(e)}")
        return False

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
    return True


def send_failed_files() -> None:
    """
        Attempts to re-upload failed files and updates the status of the upload process.

        This function checks for any previously failed uploads stored in `failed_files.json` within the `unsuccessful_uploads` directory.
        It attempts to re-upload each failed file using the `upload_file_on_server` function. If the upload is successful, the file is deleted.
        If the upload fails again, the file is retained for future attempts. After processing all files, the function updates the JSON file
        to reflect the current status of each failed upload, removing any successfully re-uploaded files and directories.

        Returns:
            None

        Error Handling:
            - Logs errors during file uploads using `log_operations_on_file`.
            - Handles `FileNotFoundError` gracefully if a file to upload is missing.

        Notes:
            - The function reads and updates the `failed_files.json` file, which tracks failed uploads.
            - Deletes the directory for a `note_id` if all files within that directory have been successfully re-uploaded.
            - Retains and re-attempts uploading any files that fail during the re-upload process.
            - Utilizes the `upload_file_on_server` function for uploading and `delete_directory` for cleaning up empty directories.

        Example:
            >>> send_failed_files()
            >>> # This will attempt to re-upload any files that failed during a previous upload attempt.
    """
    check_and_create_unsuccessful_uploads_folder()
    dir_for_unsuccessful_uploads = '../unsuccessful_uploads'
    json_path = f'{dir_for_unsuccessful_uploads}/failed_files.json'

    if not os.path.exists(json_path):
        return None

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    elements = data["elements"]
    if len(elements) == 0:
        return None

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
                log_operations_on_file(f"[ERROR] send_failed_files(): {repr(e)}")

        if len(failed_dir_content) == 0:
            delete_directory(f'{dir_for_unsuccessful_uploads}/{element["dir_name"]}')
        else:
            element["dir_content"] = failed_dir_content
            failed_elements.append(element)

    data["elements"] = failed_elements
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return None