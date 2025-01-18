import ttkbootstrap as ttk2
from ttkbootstrap.constants import *

class NotificationWindow():
    """
        A class to create and display a notification window with an informational message.

        This window displays a message in a text widget and provides an "OK" button to close the window.

        Attributes:
            root (ttk2.Window): The main window for the notification.
            info_text (ttk2.Text): A text widget to display the informational message.
            ok_button (ttk2.Button): A button to close the window.

        Methods:
            set_info_text(text: str): Updates the informational message displayed in the window.
            close_window(): Closes the notification window.
            run(): Starts the window's main event loop.
    """
    def __init__(self, info_message):
        """
            Initializes a NotificationWindow with the specified informational message.

            Args:
                info_message (str): The message to display in the notification window.
        """
        self.root = ttk2.Window("io_app", "superhero", resizable=(True, True))

        self.info_text = ttk2.Text(
            self.root,
            wrap="word",
            font=("Arial", 9),
        )
        self.set_info_text(info_message)
        self.info_text.configure(state="disabled")
        self.info_text.pack(pady=40, padx=20, fill=X, expand=YES)

        self.ok_button = ttk2.Button(
            self.root,
            text="OK",
            command=self.close_window
        )
        self.ok_button.pack(pady=20)

    def set_info_text(self, text):
        """
            Updates the informational message displayed in the text widget.

            Adjusts the text widget's height and width based on the number of lines
            and the length of the longest line in the message.

            Args:
                text (str): The new message to display.
        """
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", text)
        self.info_text.configure(state="disabled")

        lines = text.split('\n')
        max_line_length = max(len(line) for line in lines)

        line_count = len(lines)
        self.info_text.configure(height=line_count, width=max_line_length)

    def close_window(self):
        """
          Closes the notification window.
        """
        self.root.destroy()

    def run(self):
        """
            Starts the notification window's main event loop.

            This keeps the window open until it is closed by the user.
        """
        self.root.mainloop()


def create_notification_window(info_message: str) -> None:
    """
        Creates and runs a notification window with the given informational message.

        Args:
            info_message (str): The message to display in the notification window.

        Returns:
            None: This function does not return any value.

        Example:
            >>> create_notification_window("This is an important message.")
            # Opens a window displaying the message with an "OK" button.
    """
    NotificationWindow(info_message).run()
    return None