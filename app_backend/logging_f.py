import datetime
import os


def check_and_create_error_logs_folder() -> None:
    """
    Checks if the 'error_logs' folder exists in the parent directory.
    If it does not exist, creates the folder to store error logs.

    This function ensures that the necessary directory for error logs is available
    before attempting to write any error logs to it.

    Returns:
        None

    Example:
        >>> check_and_create_error_logs_folder()
    """
    if not os.path.exists('../error_logs'):
        os.mkdir('../error_logs')


def app_logs(text: str) -> None:
    """
    Logs a message to a file for tracking process of program.

    This function writes a log entry to a specific log file, including a timestamp and the provided text.
    The log file is specifically as `logs.log`. The function
    appends new entries to the file to ensure that previous logs are not overwritten.

    Args:
        text (str): The message to be logged. This should contain details about the event being recorded.

    Returns:
        None: This function does not return a value. It performs a file-writing operation for logging purposes.

    Example:
        >>> log_operations_on_file("[INFO] Start uploading files")
        >>> log_operations_on_file("[FAILED] Upload file")

    Notes:
        - The function writes logs using UTF-8 encoding to support a wide range of characters.
        - Logs include the current timestamp for tracking when the event occurred.

    Limitations:
        - The function does not handle potential file I/O errors such as permission issues or disk space limitations.
    """
    with open(file="../logs.log", mode="a", encoding='utf-8') as log:
        log.write(f"{datetime.datetime.now()} {text}\n")


def log_operations_on_file(text: str) -> None:
    """
    Logs a message to a file for tracking errors or events related to file creation.

    This function writes a log entry to a specific log file, including a timestamp and the provided text.
    The log file is located in the `error_logs/` directory, specifically as `operations_on_file.log`. The function
    appends new entries to the file to ensure that previous logs are not overwritten.

    Args:
        text (str): The message to be logged. This should contain details about the event or error being recorded.

    Returns:
        None: This function does not return a value. It performs a file-writing operation for logging purposes.

    Example:
        >>> log_operations_on_file("[ERROR] Unable to create the file due to insufficient permissions.")

    Notes:
        - Ensure that the `check_and_create_error_logs_folder` funkcion exists to avoid any issues when writing the log file.
        - The function writes logs using UTF-8 encoding to support a wide range of characters.
        - Logs include the current timestamp for tracking when the event occurred.

    Limitations:
        - The function does not handle potential file I/O errors such as permission issues or disk space limitations.
    """
    check_and_create_error_logs_folder()
    with open(file="../error_logs/operations_on_file.log", mode="a", encoding='utf-8') as log:
        log.write(f"{datetime.datetime.now()} {text}\n")


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
        None: This function does not return a value. It performs a file-writing operation for logging purposes.

    Example:
        >>> log_communication_with_www_server("[ERROR] Received 404 Not Found response.")

    Notes:
        - Ensure that the `check_and_create_error_logs_folder` funkcion exists to avoid any issues when writing the log file.
        - The function writes logs using UTF-8 encoding to support a wide range of characters.
        - Logs include the current timestamp for tracking when the event occurred.

    Limitations:
        - The function does not handle potential file I/O errors such as permission issues or disk space limitations.
    """
    check_and_create_error_logs_folder()
    with open(file="../error_logs/communication_with_www_server.log", mode="a", encoding='utf-8') as log:
        log.write(f"{datetime.datetime.now()} {text}\n")


def log_data_analyze(text: str) -> None:
    """
    Logs a message related to data analysisfor debugging or tracking purposes.

    This function appends a message to a log file that records relevant events or issues related
    to data analysis or server interactions. Each log entry includes a timestamp, providing context
    for when the event took place. This can be valuable for debugging, performance tracking, or
    understanding the sequence of actions in data analysis processes.

    Args:
        text (str): The message to be logged. This could include details of data analysis steps,
                    server communication, or any issues encountered during these processes.

    Returns:
        None: The function does not return any value but performs a logging operation to a file.

    Example:
        >>> log_data_analyze("[ERROR] Data analysis process failed.")

    Notes:
        - Ensure that the `check_and_create_error_logs_folder` function exists and is functional
          to avoid errors when accessing the log file.
        - The function writes to the log using UTF-8 encoding, ensuring compatibility with a wide range
          of characters.
        - Each log entry includes the current timestamp to help track the timing of events.

    Limitations:
        - This function does not handle file I/O exceptions such as permission issues or disk space problems,
          which could prevent the log from being written successfully.
    """
    check_and_create_error_logs_folder()
    with open(file="../error_logs/data_analyze.log", mode="a", encoding="utf-8") as log:
        log.write(f"{datetime.datetime.now()} {text}\n")
