import requests
from app_backend.logging_f import log_communication_with_www_server

# Request Warning will not show up in console
requests.packages.urllib3.disable_warnings()

# URL of WEB Server:
URL = "https://ioprojekt.atwebpages.com"

def get_info_of_notes_from_server(url: str = f"{URL}/api/get_notes_list") -> [dict|None]:
    """
    Retrieves information about notes from the server.

    This function sends an HTTP GET request to a specified URL to fetch a list of notes from the server
    in JSON format. The default URL points to a predefined API endpoint. If the request is successful,
    the function returns the parsed JSON response as a dictionary. If an error occurs, it logs the error
    and returns `None`.

    Args:
        url (str, optional): The server API endpoint for retrieving notes information. Defaults to
            "https://ioprojekt.atwebpages.com/api/get_notes_list".

    Returns:
        dict | None: A dictionary containing the notes information if the request is successful.
                     `None` if an error occurs during the request.

    Raises:
        Exception: If the response status code is not 200 or the server response is not in the expected format.

    Error Handling:
        - Logs communication errors with the server using `log_communication_with_www_server`.

    Notes:
        - Requires the `requests` library.
        - SSL certificate verification is disabled (`verify=False`), which may pose a security risk.

    Example:
        >>> notes = get_info_of_notes_from_server()
        >>> if notes:
        ...     print("Notes retrieved successfully.")
        ... else:
        ...     print("Failed to retrieve notes. Check server logs for details.")
    """
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        log_communication_with_www_server(f"[ERROR] get_info_of_notes_from_server({url}): {repr(e)}")
    return None


def upload_file_on_server(note_id: str, file_path: str, url: str = f"{URL}/api/upload_file") -> bool:
    """
    Uploads a file to a server for a specified note.

    This function sends an HTTP POST request to a specified URL to upload a file associated with a note ID.
    The default URL points to a predefined API endpoint. If the upload is successful, the server responds
    with a confirmation message and the function returns `True`. Otherwise, it logs the error and returns `False`.

    Args:
        note_id (str): The unique identifier of the note associated with the file.
        file_path (str): The local file path of the file to be uploaded.
        url (str, optional): The server API endpoint for file uploads. Defaults to
            "https://ioprojekt.atwebpages.com/api/upload_file".

    Returns:
        bool: `True` if the file upload is successful and the server responds with the expected message.
              `False` if an error occurs during the request or if the server response is unexpected.

    Raises:
        Exception: If the response status code is not 201 or the server response does
            not indicate a successful upload.

    Error Handling:
        - Logs communication errors with the server using `log_communication_with_www_server`.

    Notes:
        - Requires the `requests` library.
        - SSL certificate verification is disabled (`verify=False`), which may pose a security risk.
        - Ensures the file is properly closed after the upload attempt.

    Example:
        >>> success = upload_file_on_server("12345", "example.pdf")
        >>> if success:
        ...     print("File uploaded successfully.")
        ... else:
        ...     print("File upload failed. Check server logs for details.")
    """
    try:
        text_data = {"note_id": note_id}
        files = {"file": open(file_path, "rb")}

        response = requests.post(url, data=text_data, files=files, verify=False)

        files['file'].close()

        if response.status_code == 201 and response.json()['message'] == 'File on Server':
            return True
    except Exception as e:
        log_communication_with_www_server(f"[ERROR] upload_file_on_server({note_id}, {file_path}, {url}): {repr(e)}")
    return False


def get_info_of_notes_from_server_if_note_contain_search_word(search_word: str, url: str = f"{URL}/api/search_in_notes") -> [dict|None]:
    """
    Searches for notes on the server containing a specified search word.

    This function sends an HTTP POST request to a specified URL with a search word as part of the request data.
    The server responds with a list of notes containing the specified word in JSON format. The default URL
    points to a predefined API endpoint. If the request is successful, the function returns the parsed JSON
    response as a dictionary. If an error occurs, it logs the error and returns `None`.

    Args:
        search_word (str): The search word or phrase to find within the notes.
        url (str, optional): The server API endpoint for searching notes. Defaults to
            "https://ioprojekt.atwebpages.com/api/search_in_notes".

    Returns:
        dict | None: A dictionary containing the search results if the request is successful.
                     `None` if an error occurs during the request.

    Raises:
        Exception: If the response status code is not 200 or the server response is not in the expected format.

    Error Handling:
        - Logs communication errors with the server using `log_communication_with_www_server`.

    Notes:
        - Requires the `requests` library.
        - SSL certificate verification is disabled (`verify=False`), which may pose a security risk.

    Example:
        >>> results = get_info_of_notes_from_server_if_note_contain_search_word("important")
        >>> if results:
        ...     print("Search results:", results)
        ... else:
        ...     print("No results found or an error occurred.")
    """
    try:
        text_data = {"phrase": search_word}
        response = requests.post(url, data=text_data, verify=False)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        log_communication_with_www_server(f"[ERROR] get_info_of_notes_from_server_if_note_contain_search_word({search_word}, {url}): {repr(e)}")
        return None