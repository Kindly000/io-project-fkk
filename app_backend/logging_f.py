import datetime

def log_file_creation(text: str) -> None:
    """
    Logs a message to a file for tracking errors or events related to file creation.

    This function writes a log entry to a specific log file, including a timestamp and the provided text.
    The log file is located in the `error_logs/` directory, specifically as `file_creation.log`. The function
    appends new entries to the file to ensure that previous logs are not overwritten.

    Args:
        text (str): The message to be logged. This should contain details about the event or error being recorded.

    Returns:
        None: This function does not return a value. It performs a file-writing operation for logging purposes.

    Example:
        >>> log_file_creation("File creation process started.")
        >>> log_file_creation("Error: Unable to create the file due to insufficient permissions.")

    Notes:
        - Ensure that the `error_logs/` directory exists to avoid any issues when writing the log file.
        - The function writes logs using UTF-8 encoding to support a wide range of characters.
        - Logs include the current timestamp for tracking when the event occurred.

    Limitations:
        - The function does not handle potential file I/O errors such as permission issues or disk space limitations.
    """
    with open(file="../error_logs/file_creation.log", mode="a", encoding='utf-8') as log:
        log.write(f"{datetime.datetime.now()} {text}")


def log_communication_with_www_server(text: str) -> None:
    """
    Logs a message related to communication with a web server for debugging or tracking purposes.

    This function appends a message to a dedicated log file that records interactions or issues
    with a web server. The log entry includes a timestamp and the provided message, which can
    be useful for troubleshooting network requests or server communication failures.

    Args:
        text (str): The message to be logged. This could include information about HTTP requests,
                    responses, or any relevant details regarding server communication.

    Returns:
        None: This function does not return a value. It writes the log entry to a file as a side effect.

    Example:
        >>> log_communication_with_www_server("HTTP GET request sent to the server.")
        >>> log_communication_with_www_server("Received 404 Not Found response.")

    Notes:
        - The log entries are written to `../error_logs/communication_with_www_server.log` in the
          current working directory. Ensure that the `error_logs/` directory exists to avoid errors.
        - Logs are recorded in the default system encoding, which may vary by environment.
        - The function does not handle potential I/O exceptions, such as permission issues or file write errors.
    """
    with open(file="../error_logs/communication_with_www_server.log", mode="a") as log:
        log.write(f"{datetime.datetime.now()} {text}")
