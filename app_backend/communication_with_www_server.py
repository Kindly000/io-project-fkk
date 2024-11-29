import requests
import os
import json
import shutil
import datetime

def get_info_of_notes_from_server(url: str = "https://ioprojekt.atwebpages.com//api/get_notes_info") -> [dict|None]:
    """
        Fetches information about notes from a server.

        This function sends an HTTP GET request to the specified URL to retrieve JSON-formatted information
        about notes from the server. The default URL points to a predefined API endpoint. It handles
        potential HTTP errors gracefully and returns the response data as a dictionary if the request succeeds.

        Args:
            url (str): The URL of the API endpoint to fetch notes information from. Defaults to
                       "https://ioprojekt.atwebpages.com//api/get_notes_info".

        Returns:
            dict | None: The JSON response from the server parsed into a Python dictionary if the request
                         is successful. Returns `None` if an error occurs during the request.

        Exceptions:
            This function handles `requests.exceptions.RequestException` internally, logging the error message
            and returning `None`.

        Notes:
            - SSL certificate verification is disabled (`verify=False`), which may pose a security risk.
            - Ensure that the `requests` library is installed before using this function.

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
        with open(file="../error_logs/communication_with_www_server.log", mode="a") as log:
            log.write(f"{datetime.datetime.now()} For get_info_of_notes_from_server({url}) - Error: {e}\n")
        return None


def upload_file_on_server(note_id: str, file_path: str, url: str = "https://ioprojekt.atwebpages.com//api/upload_file") -> bool:
    """
        Uploads a file to a server for a specific note.

        This function sends an HTTP POST request to upload a file associated with a given note ID to the specified server URL.
        In the event of a failure, it saves a record of the failed upload to a local JSON file and copies the file to a dedicated
        directory for failed uploads.

        Args:
            note_id (str): The unique identifier for the note associated with the file.
            file_path (str): The local file path of the file to be uploaded.
            url (str): The URL of the API endpoint for file upload. Defaults to "https://ioprojekt.atwebpages.com//api/upload_file".

        Returns:
            bool: `True` if the file upload is successful and the server responds with the expected message.
                  `False` if an error occurs during the request or the server returns an unexpected response.

        Behavior on Failure:
            - Copies the failed file to the `unsuccessful_uploads` directory.
            - Records details of the failed upload (note ID and file name) in a JSON file located at `unsuccessful_uploads/failed_files.json`.
            - Ensures that each failed file entry is unique in the JSON log.

        Exceptions:
            This function catches all exceptions during the process and handles them by logging an error message,
            saving the file locally, and updating the failure log.

        Notes:
            - SSL certificate verification is disabled (`verify=False`), which may pose a security risk.
            - Ensure that the `requests`, `shutil`, and `os` libraries are installed and functional.

        Example:
            >>> success = upload_file_on_server("12345", "example.pdf")
            >>> if success:
            ...     print("File uploaded successfully.")
            ... else:
            ...     print("File upload failed. Check the 'unsuccessful_uploads' directory for details.")

        Local File Management:
            - The `unsuccessful_uploads` directory must exist in the current working directory, or an error may occur while saving failed files.
            - Failed upload records are stored in a JSON file named `failed_files.json` within the `unsuccessful_uploads` directory.
        """
    try:
        text_data = {"note_id": note_id}
        files = {"file": open(file_path, "rb")}

        response = requests.post(url, data=text_data, files=files, verify=False)

        files['file'].close()

        if response.status_code == 200 and response.json()['message'] == 'File on Server':
            return True
        raise Exception

    except Exception as e:
        with open(file="../error_logs/communication_with_www_server.log", mode="a") as log:
            log.write(f"{datetime.datetime.now()} For upload_file_on_server({note_id}, {file_path}, {url}) - Error: {e}\n")

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