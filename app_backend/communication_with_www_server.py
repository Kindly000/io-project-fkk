import requests
import os
import json
import shutil
from app_backend.logging_f import log_communication_with_www_server, log_file_creation

URL = "https://ioprojekt.atwebpages.com"
# URL = "https://localhost"

def get_info_of_notes_from_server(url: str = f"{URL}/api/get_notes_list") -> [dict|None]:
    """
        Fetches information about notes from a server.

        This function sends an HTTP GET request to a specified URL to retrieve information about notes from the server
        in JSON format. The default URL points to a predefined API endpoint. If the request is successful, the function
        returns the parsed JSON response as a dictionary. If an error occurs, it logs the error and returns `None`.

        Args:
            url (str): The URL of the API endpoint to fetch notes information from. Defaults to a predefined URL:
                       `https://ioprojekt.atwebpages.com//api/get_notes_info`.

        Returns:
            dict | None: A dictionary representing the JSON response if the request is successful,
                         or `None` if an error occurs.

        Behavior on Exception:
            - Logs errors using `log_communication_with_www_server`.
            - Returns `None` if an exception occurs.

        Notes:
            - SSL certificate verification is disabled (`verify=False`), which may introduce security risks.
            - Ensure the `requests` library is installed to use this function.

        Example:
            >>> info = get_info_of_notes_from_server()
            >>> if info:
            ...     print("Notes Info:", info)
            ... else:
            ...     print("Failed to fetch notes information.")
    """
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        log_communication_with_www_server(f"For get_info_of_notes_from_server({url}) - Error: {e}\n")
        return None


def upload_file_on_server(note_id: str, file_path: str, url: str = f"{URL}/api/upload_file") -> bool:
    """
    Uploads a file to a server for a specific note.

    This function sends an HTTP POST request to upload a file associated with a specified note ID to the given server URL.
    If the upload fails, the file is saved to a dedicated directory for failed uploads, and the failure details
    (note ID and file name) are recorded in a local JSON file.

    Args:
        note_id (str): The unique identifier for the note associated with the file.
        file_path (str): The local path of the file to be uploaded.
        url (str): The URL of the API endpoint for file uploads. Defaults to
                   `"https://ioprojekt.atwebpages.com//api/upload_file"`.

    Returns:
        bool: `True` if the file upload is successful and the server responds with the expected message.
              `False` if an error occurs during the request or if the server response is unexpected.

    Behavior on Failure:
        - Copies the failed file to the `../unsuccessful_uploads` directory.
        - Logs failure details (note ID and file name) in a JSON file located at `../unsuccessful_uploads/failed_files.json`.
        - Ensures no duplicate entries are added to the failure log.

    Exceptions:
        - Catches all exceptions during the process.
        - Logs error details to the logging mechanism specified by `log_communication_with_www_server`.

    Notes:
        - SSL certificate verification is disabled (`verify=False`), which may pose a security risk.
        - Requires the `requests`, `shutil`, and `os` libraries.
        - The `../unsuccessful_uploads` directory must exist for proper failure handling, or errors may occur.

    Example:
        >>> success = upload_file_on_server("12345", "example.pdf")
        >>> if success:
        ...     print("File uploaded successfully.")
        ... else:
        ...     print("File upload failed. Check the 'unsuccessful_uploads' directory for details.")

    Local File Management:
        - The failed file is stored in the `../unsuccessful_uploads` directory with its original name.
        - Failure details are stored in `../unsuccessful_uploads/failed_files.json` in the following structure:
          ```json
          {
              "elements": [
                  {"note_id": "12345", "file_path": "example.pdf"}
              ]
          }
          ```
    """
    try:
        text_data = {"note_id": note_id}
        files = {"file": open(file_path, "rb")}

        response = requests.post(url, data=text_data, files=files, verify=False)

        files['file'].close()

        if response.status_code == 200 and response.json()['message'] == 'File on Server':
            return True
        raise Exception
    except OSError as e:
        return False
    except Exception as e:
        log_communication_with_www_server(f"For upload_file_on_server({note_id}, {file_path}, {url}) - Error: {e}\n")

        dir_for_unsuccessful_uploads = '../unsuccessful_uploads'
        fail_file_name = os.path.basename(file_path)
        try:
            shutil.copyfile(file_path, f'{dir_for_unsuccessful_uploads}/{fail_file_name}')
        except shutil.SameFileError as e:
            pass

        json_path = '../unsuccessful_uploads/failed_files.json'
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"elements": []}

        new_element = {"note_id": note_id, "file_path": fail_file_name}
        if new_element not in data["elements"]:
            data["elements"].append(new_element)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        return False


def get_info_of_notes_from_server_if_note_contain_search_word(search_word: str, url: str = f"{URL}/api/search_in_notes") -> [dict|None]:
    """
    Fetches information about notes from the server that contain a specified search word.

    This function sends a POST request to the specified server URL with the search word as a parameter.
    It returns the server's JSON response if the request is successful, or `None` if an error occurs.

    Args:
        search_word (str): The word to search for in the notes.
        url (str): The URL of the API endpoint to fetch notes information from. Defaults to a predefined URL:
                       `https://ioprojekt.atwebpages.com//api/get_notes_info`.

    Returns:
        [dict | None]: A dictionary containing the JSON response from the server if successful,
            or `None` if an error occurs during the request.

    Logs:
        Logs any errors encountered during the request to the server using the
        `log_communication_with_www_server` function.

    Raises:
        None: Any exceptions raised during the request are caught and logged, and the function
        returns `None`.
    """
    try:
        text_data = {"phrase": search_word}
        response = requests.post(url, data=text_data, verify=False)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        log_communication_with_www_server(f"For get_info_of_notes_from_server_if_note_contain_search_word({search_word}, {url}) - Error: {e}\n")
        return None

if __name__ == '__main__':
    # print(get_info_of_notes_from_server())
    print(get_info_of_notes_from_server_if_note_contain_search_word('co'))