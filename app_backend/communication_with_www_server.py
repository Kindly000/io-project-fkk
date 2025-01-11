import requests
from app_backend.logging_f import log_communication_with_www_server


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
    Uploads a file to a server for a specified note.

    Args:
        note_id (str): The unique identifier of the note associated with the file.
        file_path (str): The local file path of the file to be uploaded.
        url (str, optional): The server API endpoint for file uploads. Defaults to
            "https://ioprojekt.atwebpages.com/api/upload_file".

    Returns:
        bool: `True` if the file upload is successful and the server responds with the expected message.
              `False` if an error occurs during the request or if the server response is unexpected.

    Raises:
        Exception: If the response status code is not 200 or the server response does
            not indicate a successful upload.

    Error Handling:
        - Logs communication errors with the server using `log_communication_with_www_server`.
        - Invokes a retry mechanism (`save_unsuccessful_upload`) to handle failed uploads.

    Notes:
        - Requires the `requests` library.
        - SSL certificate verification is disabled (`verify=False`), which may pose a security risk.
        - Ensures the file is properly closed after the upload attempt.

    Example:
        >>> success = upload_file_on_server("12345", "example.pdf")
        >>> if success:
        ...     print("File uploaded successfully.")
        ... else:
        ...     print("File upload failed. Check the 'unsuccessful_uploads' directory for details.")
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
        print(e)
        return False
    except Exception as e:
        log_communication_with_www_server(f"For upload_file_on_server({note_id}, {file_path}, {url}) - Error: {e}\n")
        from app_backend.retry_logic import save_unsuccessful_upload
        save_unsuccessful_upload(note_id, file_path)
        return False


def get_info_of_notes_from_server_if_note_contain_search_word(search_word: str, url: str = f"{URL}/api/search_in_notes") -> [dict|None]:
    """
    Fetches information about notes from the server that contain a specified search word (case insensitive).

    This function sends a POST request to the specified server URL with the search word as a parameter.
    It returns the server's JSON response if the request is successful, or `None` if an error occurs.

    Args:
        search_word (str): The word to search for in the notes.
        url (str): The URL of the API endpoint to fetch notes information from. Defaults to a predefined URL:
                       `https://ioprojekt.atwebpages.com//api/get_notes_info`.

    Returns:
        [dict | None]: A dictionary containing the JSON response from the server if successful,
            or `None` if an error occurs during the request.

    Behavior on Exception:
            - Logs errors using `log_communication_with_www_server`.
            - Returns `None` if an exception occurs.

        Notes:
            - SSL certificate verification is disabled (`verify=False`), which may introduce security risks.
            - Ensure the `requests` library is installed to use this function.

        Example:
            >>> info = get_info_of_notes_from_server_if_note_contain_search_word('VSS')
            >>> if info:
            ...     print("Notes Info:", info)
            ... else:
            ...     print("Failed to fetch notes information.")
    """
    try:
        text_data = {"phrase": search_word}
        response = requests.post(url, data=text_data, verify=False)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        log_communication_with_www_server(f"For get_info_of_notes_from_server_if_note_contain_search_word({search_word}, {url}) - Error: {e}\n")
        return None