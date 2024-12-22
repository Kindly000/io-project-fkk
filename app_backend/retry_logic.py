import json
import os
from app_backend.communication_with_www_server import upload_file_on_server


def send_failed_files():
    """
        Attempts to re-upload files listed in the `failed_files.json` log.

        This function reads the `failed_files.json` file from the `unsuccessful_uploads` directory, which contains a record of file upload
        failures. It iterates through each entry, attempting to re-upload each file. Successfully uploaded files are removed
        from the disk, while those that fail to upload are retained in the JSON log for future processing.

        If the `failed_files.json` file does not exist or contains no entries, the function exits without action.

        Workflow:
            - Reads the `failed_files.json` file to load the list of failed file uploads.
            - Iterates over each entry, attempting to upload the file using the `upload_file_on_server` function.
            - Deletes the file from the disk if the upload succeeds.
            - Keeps a record of failed uploads in the JSON log for further attempts.

        Notes:
            - The `unsuccessful_uploads` directory and `failed_files.json` file must exist in the current working directory for this function to operate.
            - The function assumes that `upload_file_on_server` is correctly implemented and available in the scope.
            - JSON file handling includes reading and writing with UTF-8 encoding.

        Example:
            >>> send_failed_files()
            # Attempts to re-upload all files from the `unsuccessful_uploads` directory that have previously failed.
    """
    directory = 'unsuccessful_uploads'

    json_path = os.path.join(directory, "failed_files.json")
    if not os.path.exists(json_path):
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    elements = data["elements"]
    if len(elements) == 0:
        return

    failed_elements = []

    for element in elements:
        note_id = element.get("note_id")
        file_path = os.path.join(directory, element.get("file_path", ""))

        if upload_file_on_server(note_id, file_path):
            os.remove(file_path)
        else:
            failed_elements.append(element)

    data["elements"] = failed_elements
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

