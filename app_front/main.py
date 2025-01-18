from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tkinter import filedialog, BooleanVar, Button, Toplevel
import re
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
import subprocess
import webbrowser
import os
import sys
import app_front.class_record as rec_vid  # Importing video recording class (likely used elsewhere)
import app_front.class_audio as rec_aud  # Importing audio recording class (likely used elsewhere)
from data_analyze import data_analyze  # Data analysis functions (imported but not used here)
import app_backend.communication_with_www_server as com_www_server  # Communication with a web server
import app_backend.save_files as sf  # Saving files (imported but not used here)
import app_front.quickstart as google_cal  # Google Calendar integration (likely used elsewhere)
import app_backend.retry_logic as retry_logic  # Retry logic for failed tasks (not used in this part)
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Change the current working directory to the script's location
import app_backend.logging_f as logg

# Main class for handling GUI and interactions
class IoFront(ttk.Frame):
    def __init__(self, master_window):
        """Initialization of the main window."""
        super().__init__(master_window, padding=(20, 10))  # Initialize parent frame with padding
        self.grid(row=0, column=0)  # Grid layout for placing the frame in the window

        """Threading setup"""
        self.executor = ThreadPoolExecutor(max_workers=3)  # ThreadPoolExecutor to run tasks concurrently
        self.recording_video = False  # Flag for tracking video recording status
        self.recording_audio = False  # Flag for tracking audio recording status
        self.check_if_record_in_progress = False  # Flag for checking if a recording is in progress

        """Directories for temporary files"""
        self.record_dir = ""  # Directory for storing recorded files (to be set later)
        self.analyze_dir = ""  # Directory for storing analyzed files (to be set later)

        """Google Calendar Authentication"""
        self.google_ = google_cal.Calendar()  # Initialize Google Calendar API connection

        """Fetching notes from the server"""
        self.import_from_server = com_www_server.get_info_of_notes_from_server()  # Retrieve notes from the server
        if self.import_from_server is not None:
            self.imported_notes = self.import_from_server["notes"]  # Store notes if available
        else:
            self.imported_notes = []  # Default to an empty list if no notes are fetched
        self.clicked_note = ""  # Placeholder for storing the clicked note ID

        """Date variables for note creation and analysis"""
        self.date_var = None  # Variable for storing the date related to the current note
        self.date_var_analyze = None  # Variable for storing date related to analysis (if any)

        """Variables for processing existing recording windows"""
        self.selected_download_dir_var = "../default_save_folder"  # Default folder for downloads
        self.existing_record_frequency_comparison_sec = "5"  # Frequency for comparing existing recordings (in seconds)
        self.existing_record_selected_dir_var = "../default_save_folder"  # Default folder for existing recordings
        self.existing_record_file_name = "notatka_testowa"  # Default file name for existing recordings
        self.existing_record_entered_name = ttk.StringVar()  # Store user input for file name
        self.existing_record_app_name = "MSTeams"  # Example application name for existing recordings
        self.existing_record_send_to_server_from_new_window_var = BooleanVar()  # Flag for whether to send to server
        self.existing_record_send_to_server_from_new_window = True  # Default to True for sending to the server
        self.existing_wav_file_to_process_var = ttk.StringVar()  # Store the selected WAV file to process
        self.existing_mp4_file_to_process_var = ttk.StringVar()  # Store the selected MP4 file to process
        self.existing_wav_file_to_process = ""  # Placeholder for WAV file
        self.existing_mp4_file_to_process = ""  # Placeholder for MP4 file

        """GUI setup"""
        """Left container for notes and treeview"""
        self.left_container = ttk.LabelFrame(self, text="Recordings")  # LabelFrame to group the recordings section
        self.left_container.pack(padx=5, pady=10, side=LEFT, fill=Y)  # Pack it on the left with padding
        self.tree = self.create_treeview()  # Create a treeview to display notes
        self.create_scrollbar_for_treeview()  # Create a scrollbar for the treeview

        """Right container for recording and actions"""
        self.right_container = ttk.Frame(self)  # Frame to contain the right-side elements
        self.new_record_container = ttk.LabelFrame(self.right_container, text="New recording")  # Frame for new recording controls
        self.start_recording_button()  # Create the start recording button
        self.stop_recording_button()  # Create the stop recording button
        self.new_record_container.pack(padx=5, pady=10)  # Pack the new recording section

        """Action container for managing recordings"""
        self.action_container = ttk.LabelFrame(self.right_container, text="Manage recording")  # Frame for action buttons
        self.open_in_browser_button()  # Create the open in browser button
        self.refresh_button()  # Create the refresh button
        self.process_files_main_app_button()  # Create the process files button
        self.action_container.pack(padx=5, pady=10)  # Pack the action section

        """Search container with entry and button"""
        self.search_container = ttk.LabelFrame(self.right_container, text="Search")  # Frame for the search functionality
        self.search_entry = self.create_entry()  # Create the search entry field
        self.create_search_button()  # Create the search button
        self.search_container.pack(padx=5, pady=10)  # Pack the search section
        self.right_container.pack(side=LEFT, padx=20, pady=10, fill=Y)  # Pack the right container

        """Function for retrying failed file uploads"""
        self.retry_logic()  # Call retry logic for handling file uploads that failed previously

        # Ensure proper cleanup when closing the window
        master_window.protocol("WM_DELETE_WINDOW", self.on_closing)

    """Create treeview widget to display notes"""
    def create_treeview(self):
        columns = ["id", "date", "name"]  # Columns for the treeview
        tree = ttk.Treeview(
            master=self.left_container,
            bootstyle="secondary",
            columns=columns,
            show="headings",
            height=20,  # Limit to 20 visible rows
        )
        tree.grid_configure(row=0, column=0, columnspan=4, rowspan=5, padx=20, pady=10)  # Position treeview in the grid

        # Configure columns' width and alignment
        tree.column("id", width=50, anchor=CENTER)
        tree.column("date", anchor=CENTER)
        tree.column("name", anchor=CENTER)

        # Set column headers
        tree.heading("id", text="id")
        tree.heading("date", text="date")
        tree.heading("name", text="name")

        tree.tag_configure("change_bg", background="#20374C")  # Styling for alternate rows

        data = self.imported_notes  # Data for populating the treeview

        tree.tag_configure("change_bg", background="#20374C")  # Alternate row color
        index = 0
        for i in data:
            # Insert rows into treeview, alternating row colors
            if int(index) % 2 == 1:
                tree.insert(
                    "",
                    "end",
                    values=[i["note_id"], i["datetime"], i["title"]],
                    tags="change_bg",
                    iid=index,
                )
            else:
                tree.insert(
                    "",
                    "end",
                    values=[i["note_id"], i["datetime"], i["title"]],
                    iid=index,
                )
            tree.bind("<<TreeviewSelect>>", self.tree_on_click_element)  # Bind row click event to handler

            index += 1

        return tree

    """Handle treeview item selection"""
    def tree_on_click_element(self, event):
        clickedItem = self.tree.focus()  # Get the selected item
        self.clicked_note = self.tree.item(clickedItem)["values"][0]  # Store the selected note's ID
        return

    """Create scrollbar for treeview"""
    def create_scrollbar_for_treeview(self):
        scrollbar = ttk.Scrollbar(
            master=self.left_container, orient="vertical", command=self.tree.yview
        )  # Create vertical scrollbar
        scrollbar.grid(row=0,rowspan=5, column=4, sticky="ns")  # Place it next to the treeview
        self.tree.configure(yscrollcommand=scrollbar.set)  # Link the scrollbar to the treeview

    """Create a button for processing existing files"""
    def process_files_main_app_button(self):
        button = ttk.Button(
            master=self.action_container, width=20, text="Process files"
        )  # Create button for file processing
        button.grid(row=1, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        button.bind(
            "<Button-1>",
            lambda x: [
                self.start_processing_button_main_app()  # Start the file processing task
            ]
        )

    """Create an entry widget for user input"""
    def create_entry(self):
        entry = ttk.Entry(master=self.search_container, width=20)  # Create an entry field
        entry.pack(padx=5, pady=10)  # Pack it into the search container
        return entry

    """Create a search button to trigger search functionality"""
    def create_search_button(self):
        button = ttk.Button(master=self.search_container, width=20, text="Search")
        button.bind("<Button-1>", lambda x: self.on_click_search())  # Trigger search function on click
        button.pack(padx=5, pady=10)  # Pack the search button
        return button

    # Function to create a dropdown menu for selecting the application for recording
    def drop_menu_app(self, master):
        # Create a menu button with options for selecting an application
        mb = ttk.Menubutton(master=master, width=16, text="Application")
        mb.pack(padx=5, pady=10)  # Pack the menu button into the parent container
        options = ["MSTeams", "Zoom", "Google Meet"]  # List of available applications for recording
        inside_menu = ttk.Menu(mb, tearoff=0)  # Create a menu with no tear-off feature

        # Function to handle selection of an option from the dropdown
        def on_click(option):
            self.existing_record_app_name = option  # Set the selected application name
            mb.config(text=option)  # Update the button text with the selected option

        # Add the options to the dropdown menu as radio buttons
        for option in options:
            inside_menu.add_radiobutton(
                label=option, command=lambda x=option: on_click(x)
            )
        mb["menu"] = inside_menu  # Attach the menu to the menubutton

    # Function to create a dropdown menu for selecting the application for recording (for existing file processing)
    def existing_record_drop_menu_app(self, master):
        # Create a menu button with options for selecting an application
        mb = ttk.Menubutton(master=master, width=16, text="Application")
        mb.pack(padx=5, pady=10)  # Pack the menu button into the parent container
        options = ["MSTeams", "Zoom", "Google Meet"]  # List of available applications for recording
        inside_menu = ttk.Menu(mb, tearoff=0)  # Create a menu with no tear-off feature

        # Function to handle selection of an option from the dropdown
        def on_click(option):
            self.existing_record_app_name = option  # Set the selected application name
            mb.config(text=option)  # Update the button text with the selected option

        # Add the options to the dropdown menu as radio buttons
        for option in options:
            inside_menu.add_radiobutton(
                label=option, command=lambda x=option: on_click(x)
            )
        mb["menu"] = inside_menu  # Attach the menu to the menubutton

    # Function to create a button that opens the selected recording in a web browser
    def open_in_browser_button(self):
        # Create a button to open the recording in the browser
        button = ttk.Button(
            master=self.action_container, width=20, text="Open in browser"
        )
        # Bind the button click to open the URL of the clicked note
        button.grid(row=3, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        button.bind(
            "<Button-1>",
            lambda x: webbrowser.open_new(
                f"https://ioprojekt.atwebpages.com/{self.clicked_note}"  # Open the note's URL in a new browser window
            ),
        )
        return button  # Return the created button

    # Function to create a refresh button for the treeview in the main window
    def refresh_button(self):
        # Create a refresh button to refresh the data shown in the treeview
        button = ttk.Button(master=self.action_container, width=20, text="Refresh")
        button.grid(row=5, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        # Bind the button click to refresh the data and retry logic
        button.bind(
            "<Button-1>", lambda x: [self.on_click_refresh(), self.retry_logic()]
        )
        return button  # Return the created button

    # Function to handle the refresh action by fetching updated data from the server
    def on_click_refresh(self):
        # Fetch the latest data from the server
        data = com_www_server.get_info_of_notes_from_server()["notes"]
        # Clear the existing treeview entries
        index = 0
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Populate the treeview with the updated data
        for i in data:
            if int(index) % 2 == 1:  # Alternate row colors
                self.tree.insert(
                    "",
                    "end",
                    values=[i["note_id"], i["datetime"], i["title"]],
                    tags="change_bg",
                    iid=index,
                )
            else:
                self.tree.insert(
                    "",
                    "end",
                    values=[i["note_id"], i["datetime"], i["title"]],
                    iid=index,
                )
            self.tree.bind("<<TreeviewSelect>>", self.tree_on_click_element)  # Bind selection event to handler

            index += 1

    # Function to search for notes based on the search term entered by the user
    def on_click_search(self):
        data = ""
        get_text = self.search_entry.get()  # Get the text from the search entry field
        # Fetch notes from the server that contain the search term
        if com_www_server.get_info_of_notes_from_server_if_note_contain_search_word(get_text) is not None:
            data = com_www_server.get_info_of_notes_from_server_if_note_contain_search_word(get_text)["notes"]

        if data != "":
            # Clear existing entries in the treeview
            index = 0
            for i in self.tree.get_children():
                self.tree.delete(i)

            # Populate the treeview with the search results
            for i in data:
                if int(index) % 2 == 1:  # Alternate row colors
                    self.tree.insert(
                        "",
                        "end",
                        values=[i["note_id"], i["datetime"], i["title"]],
                        tags="change_bg",
                        iid=index,
                    )
                else:
                    self.tree.insert(
                        "",
                        "end",
                        values=[i["note_id"], i["datetime"], i["title"]],
                        iid=index,
                    )
                self.tree.bind("<<TreeviewSelect>>", self.tree_on_click_element)  # Bind selection event to handler

                index += 1

    # Function to create a button to start the recording and create a new directory for recording
    def start_recording_button(self):
        button = ttk.Button(
            master=self.new_record_container, width=20, text="Start recording"
        )

        # Function to check if a recording is running and start it if not
        def check_if_record_is_running():
            if not self.check_if_record_in_progress:
                self.check_if_record_in_progress = True  # Set flag to indicate recording is in progress
                self.new_directory()  # Create a new directory for the recording
                self.start_recordings()  # Start the recording process

        # Bind the button click to the check function
        button.bind(
            "<Button-1>", lambda e: [
                check_if_record_is_running()  # Start recording if not already in progress
            ]
        )
        button.grid(row=1, column=1, padx=5, pady=10)  # Position the button in the grid
        return button  # Return the created button

    # Function to create a button to stop the recording and combine the recordings
    def stop_recording_button(self):
        button = ttk.Button(
            master=self.new_record_container, width=20, text="Stop recording"
        )

        # Function to check if a recording is running and stop it
        def check_if_record_is_running_stop():
            if self.check_if_record_in_progress:
                self.check_if_record_in_progress = False  # Set flag to indicate recording is stopped
                self.stop_recordings()  # Stop the recording process
                self.combining_recordings()  # Combine the audio/video files
                self.stop_recording_button_new_window()  # Open a new window for further actions

        # Bind the button click to the stop function
        button.bind(
            "<Button-1>",
            lambda e: [
                check_if_record_is_running_stop()  # Stop the recording if it's in progress
            ],
        )
        button.grid(row=2, column=1, padx=5, pady=10)  # Position the button in the grid
        return button  # Return the created button

    # Function to open a new window after stopping the recording with options for further actions
    def stop_recording_button_new_window(self):
        """Function to check if 'combined.mp4' file is present and handle actions accordingly."""

        def check_file_presence():
            if self.record_dir:
                file_path = os.path.join("../tmp/", self.record_dir, "combined.mp4")
                if os.path.isfile(file_path):  # Check if the combined video file exists
                    return True
                else:
                    logg.app_logs(f"[ERROR] File not found {file_path}")
                    return False
            else:
                logg.app_logs(f"[INFO] Directory not set")

        # Function to process the file if it's present
        def check_file_and_process():
            if check_file_presence():
                self.start_processing_button_new_window()  # Start processing the file if present
                new_window.destroy()  # Close the window after starting the processing

        # Function to download the file if it's present
        def check_file_and_download():
            if check_file_presence():
                self.save_audio_and_video_files()  # Save the audio and video files to the selected directory

        # Create a new window for actions after stopping the recording
        new_window = Toplevel(self.new_record_container)
        new_window.title("Choose action")
        new_window.geometry("400x300")

        # Label and button for selecting a download directory
        download_label = ttk.Label(new_window, text="Select dir to local download", font=("Arial", 9))
        download_label.pack(pady=10)
        button_dir = ttk.Button(new_window, text="Choose directory")
        button_dir.bind("<Button-1>",
                        lambda e: [self.open_download_directory_picker(),
                                   button_dir.config(text=self.selected_download_dir_var)])
        button_dir.pack(pady=10)

        # Button to trigger downloading the files
        download_button = ttk.Button(new_window, text="Download")
        download_button.bind("<Button-1>", lambda e: [check_file_and_download()])
        download_button.pack(pady=10)

        # Label and button for processing the recording
        info_label = ttk.Label(new_window, text="Download files locally, later still you can make notes from them",
                               font=("Arial", 9), bootstyle="secondary")
        info_label.pack(pady=10)
        process_recording_label = ttk.Label(new_window, text="Process recording", font=("Arial", 9))
        process_recording_label.pack(pady=10)
        process_recording_button = ttk.Button(new_window, text="Process recording")
        process_recording_button.pack(pady=10)
        process_recording_button.bind(
            "<Button-1>",
            lambda e: [check_file_and_process()]
        )

        check_file_presence()  # Check if the file is present when the window is created

    # Function to create a processing window after finishing recording
    def start_processing_button_new_window(self):

        # Validating the title of the note entered by the user
        def validate_title():
            title = entry_title.get()  # Get the title entered by the user
            # Regular expression check to allow letters, numbers, spaces, hyphens, and underscores
            if not re.match(r"^[\w\-. ]+$", title):
                validation_label.config(
                    text="Nazwa może zawierać tylko litery, cyfry, spacje, myślniki i podkreślenia!",
                    bootstyle="danger")
                return False
            if title == "":
                validation_label.config(text="Nie może być pusta", bootstyle="danger")  # Ensure the title isn't empty
                return False
            validation_label.config(text="Nazwa poprawna!", bootstyle="success")  # Title is valid
            return True

        # Create a new window for processing the recording details
        new_window = Toplevel(self.new_record_container)
        new_window.title("Details")
        new_window.geometry("300x700")  # Window size

        # Display the paths to the files for processing (WAV and MP4)
        label_paths = ttk.Label(new_window, text="Paths to files", font=("Arial", 9))
        label_paths.pack(pady=10)

        # Show the existing WAV file path for the user
        entry_path_wav = ttk.Entry(new_window, width=30, state="normal",
                                   textvariable=self.existing_wav_file_to_process_var)
        entry_path_wav.delete(0, END)
        entry_path_wav.insert(0, self.existing_wav_file_to_process)  # Set the path
        entry_path_wav.config(state="readonly")  # Make it read-only
        entry_path_wav.pack(pady=10)

        # Show the existing MP4 file path for the user
        entry_path_mp4 = ttk.Entry(new_window, width=30, state="normal",
                                   textvariable=self.existing_mp4_file_to_process_var)
        entry_path_mp4.delete(0, END)
        entry_path_mp4.insert(0, self.existing_mp4_file_to_process)  # Set the path
        entry_path_mp4.config(state="readonly")  # Make it read-only
        entry_path_mp4.pack(pady=10)

        # Prompt the user to enter a title for the note
        label_title = ttk.Label(new_window, text="Enter note title", font=("Arial", 9))
        label_title.pack(pady=10)

        entry_title = ttk.Entry(new_window, width=30, textvariable=self.existing_record_entered_name)
        entry_title.pack(pady=10)

        # Display validation messages for title input
        validation_label = ttk.Label(new_window, text="", font=("Arial", 9))
        validation_label.pack(pady=5)

        # Prompt the user to choose a directory for saving the note
        label_dir = ttk.Label(new_window, text="Choose directory for note", font=("Arial", 9))
        label_dir.pack(pady=10)

        button_dir = ttk.Button(new_window, text="Choose directory")
        button_dir.bind(
            "<Button-1>",
            lambda e: [
                self.open_directory_picker(),
                button_dir.config(text=self.existing_record_selected_dir_var)
            ]
        )
        button_dir.pack(pady=10)

        # Provide a dropdown menu to choose the application for the note (e.g., MSTeams, Zoom, etc.)
        label_app = ttk.Label(new_window, text="Choose app", font=("Arial", 9))
        label_app.pack(pady=10)
        self.drop_menu_app(new_window)

        # Prompt for the frequency of comparison (e.g., 5 seconds, 10 seconds, etc.)
        label_seconds = ttk.Label(new_window, text="Enter frequency of comparison", font=("Arial", 9))
        label_seconds.pack(pady=10)

        mb_sec = ttk.Menubutton(new_window, width=16, text="Seconds")
        mb_sec.pack(padx=5, pady=10)
        options_sec = ["1", "5", "6", "7", "9", "10"]
        inside_menu_sec = ttk.Menu(mb_sec, tearoff=0)

        def on_click_sec(option):
            self.existing_record_frequency_comparison_sec = option  # Set the selected frequency
            mb_sec.config(text=option)

        # Add options to the frequency menu
        for option in options_sec:
            inside_menu_sec.add_radiobutton(label=option, command=lambda x=option: on_click_sec(x))
        mb_sec["menu"] = inside_menu_sec

        # Checkbox to indicate whether the note should be sent to the server
        checkbox_label = ttk.Label(new_window, text="Send to server", font=("Arial", 9))
        checkbox_label.pack(pady=10)
        self.existing_record_send_to_server_from_new_window_var.set(True)  # Default to True
        checkbox = ttk.Checkbutton(new_window, variable=self.existing_record_send_to_server_from_new_window_var)
        checkbox.pack(pady=10)

        # Button to start processing the files
        start_process_button = ttk.Button(new_window, text="Start processing")
        start_process_button.bind(
            "<Button-1>",
            lambda e: [
                validate_title() and self.save_name_dir_in_variables_existing_record(),
                # Validate the title and save variables
                self.executor.submit(self.start_data_analyze, self.record_dir,
                                     self.date_var) if validate_title() else None,  # Start analysis if title is valid
                new_window.destroy() if validate_title() else None  # Close the window if title is valid
            ]
        )
        start_process_button.pack(pady=10)

    # Function to create a processing window for an existing recording from the main app
    def start_processing_button_main_app(self):

        # Validating the title of the note entered by the user
        def validate_title():
            title = entry_title.get()  # Get the title entered by the user
            if not re.match(r"^[\w\-. ]+$", title):  # Check for valid characters in title
                validation_label.config(
                    text="Nazwa może zawierać tylko litery, cyfry, spacje, myślniki i podkreślenia!",
                    bootstyle="danger")
                return False
            if title == "":
                validation_label.config(text="Nie może być pusta", bootstyle="danger")  # Ensure the title is not empty
                return False
            if self.existing_wav_file_to_process == "" or self.existing_mp4_file_to_process == "":  # Ensure WAV and MP4 files are selected
                validation_label.config(text="Nie może być pusta", bootstyle="danger")
                return False
            validation_label.config(text="Nazwa poprawna!", bootstyle="success")  # Title is valid
            return True

        # Create a new window for processing an existing recording
        new_window = Toplevel(self.new_record_container)
        new_window.title("Process existing recording")
        new_window.geometry("300x700")  # Window size

        # Display the paths for selecting files
        label_paths = ttk.Label(new_window, text="Paths to files", font=("Arial", 9))
        label_paths.pack(pady=10)

        # Button to choose a .wav file directory
        def existing_record_wav_files_directory_picker():
            selected_directory = filedialog.askopenfilename(title="Choose file", filetypes=[("WAV files", "*.wav")])
            if selected_directory:
                self.existing_wav_file_to_process = selected_directory
                self.existing_wav_file_to_process_var.set(selected_directory)  # Set the selected WAV file path
            else:
                self.existing_wav_file_to_process = ""
                self.existing_wav_file_to_process_var.set("")

        button_wav_dir = ttk.Button(new_window, text="Choose .wav file")
        button_wav_dir.bind(
            "<Button-1>",
            lambda e: [
                existing_record_wav_files_directory_picker(),
                button_wav_dir.config(text=self.existing_wav_file_to_process)
            ]
        )
        button_wav_dir.pack(pady=10)

        # Button to choose a .mp4 file directory
        def existing_record_mp4_files_directory_picker():
            selected_directory = filedialog.askopenfilename(title="Choose file", filetypes=[("MP4 files", "*.mp4")])
            if selected_directory:
                self.existing_mp4_file_to_process = selected_directory
                self.existing_mp4_file_to_process_var.set(selected_directory)  # Set the selected MP4 file path
            else:
                self.existing_mp4_file_to_process = ""
                self.existing_mp4_file_to_process_var.set("")

        button_mp4_dir = ttk.Button(new_window, text="Choose .mp4 file")
        button_mp4_dir.bind(
            "<Button-1>",
            lambda e: [
                existing_record_mp4_files_directory_picker(),
                button_mp4_dir.config(text=self.existing_mp4_file_to_process)
            ]
        )
        button_mp4_dir.pack(pady=10)

        # Prompt for the title of the note
        label_title = ttk.Label(new_window, text="Enter note title", font=("Arial", 9))
        label_title.pack(pady=10)

        entry_title = ttk.Entry(new_window, width=30, textvariable=self.existing_record_entered_name)
        entry_title.pack(pady=10)

        # Display validation messages for title input
        validation_label = ttk.Label(new_window, text="", font=("Arial", 9))
        validation_label.pack(pady=5)

        # Prompt for directory selection for the note
        label_dir = ttk.Label(new_window, text="Choose directory for note", font=("Arial", 9))
        label_dir.pack(pady=10)

        button_dir = ttk.Button(new_window, text="Choose directory")
        button_dir.bind(
            "<Button-1>",
            lambda e: [
                self.existing_record_open_directory_picker(),
                button_dir.config(text=self.existing_record_selected_dir_var)
            ]
        )
        button_dir.pack(pady=10)

        # Dropdown for selecting the app associated with the note
        label_app = ttk.Label(new_window, text="Choose app", font=("Arial", 9))
        label_app.pack(pady=10)
        self.existing_record_drop_menu_app(new_window)

        # Dropdown for selecting the frequency of comparison
        label_seconds = ttk.Label(new_window, text="Enter frequency of comparison", font=("Arial", 9))
        label_seconds.pack(pady=10)

        mb_sec = ttk.Menubutton(new_window, width=16, text="Seconds")
        mb_sec.pack(padx=5, pady=10)
        options_sec = ["1", "5", "6", "7", "9", "10"]
        inside_menu_sec = ttk.Menu(mb_sec, tearoff=0)

        def on_click_sec(option):
            self.existing_record_frequency_comparison_sec = option  # Set the selected frequency

        # Add options to the frequency menu
        for option in options_sec:
            inside_menu_sec.add_radiobutton(label=option, command=lambda x=option: on_click_sec(x))
        mb_sec["menu"] = inside_menu_sec

        # Checkbox to indicate whether the note should be sent to the server
        checkbox_label = ttk.Label(new_window, text="Send to server", font=("Arial", 9))
        checkbox_label.pack(pady=10)
        self.existing_record_send_to_server_from_new_window_var.set(True)  # Default to True
        checkbox = ttk.Checkbutton(new_window, variable=self.existing_record_send_to_server_from_new_window_var)
        checkbox.pack(pady=10)

        # Button to start processing the files
        start_process_button = ttk.Button(new_window, text="Start processing")
        start_process_button.bind(
            "<Button-1>",
            lambda e: [
                validate_title() and self.save_name_dir_in_variables_existing_record(),
                # Validate title and save variables
                self.placeholder() if validate_title() else None,  # Placeholder action
                new_window.destroy() if validate_title() else None  # Close the window if title is valid
            ]
        )
        start_process_button.pack(pady=10)

    """function to run in thread combine audio and video files"""

    def combining_recordings(self):
        # Submits the _combining_recordings method to the executor to run in a separate thread
        self.executor.submit(self._combining_recordings)

    """function to combine audio and video files by using ffmpeg"""

    def _combining_recordings(self):
        try:
            # FFmpeg command to combine audio and video files into one MP4 file
            cmd = f"ffmpeg -i ../tmp/{self.record_dir}/audio_output.wav -i ../tmp/{self.record_dir}/video_output.avi -c:v libx264 -c:a aac -strict experimental ../tmp/{self.record_dir}/combined.mp4"

            # Open a log file to store FFmpeg's output
            with open(f"../tmp/{self.record_dir}/ffmpeg_log", "w") as log_file:
                # Executes the FFmpeg command and writes stdout and stderr to the log file
                subprocess.call(cmd, shell=True, stdout=log_file, stderr=subprocess.STDOUT)

            logg.app_logs(f"[SUCCESS] Mixing is complete!")

            # Store the path to the newly created combined MP4 file
            self.existing_mp4_file_to_process = f"../tmp/{self.record_dir}/combined.mp4"

        except Exception as e:
            logg.app_logs(f"[ERROR] Mixing error {e}")

    """function to create new directory for notes"""

    def new_directory(self):
        # Get the current date and time for the directory name
        self.date_var = datetime.now()
        date_current = self.date_var.strftime("%Y-%m-%d_%H-%M-%S")

        # Create a directory name based on the date
        self.record_dir = f"files_for_notes_{date_current}"

        # Create a new nested directory under the temporary folder
        nested_dir = Path(f"../tmp/{self.record_dir}")
        nested_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist

    """function to create new directory for notes from analysis window"""

    def new_directory_for_analyze(self):
        # Same as new_directory, but for analysis purposes
        self.date_var_analyze = datetime.now()
        date_current = self.date_var_analyze.strftime("%Y-%m-%d_%H-%M-%S")

        self.analyze_dir = f"files_for_notes_{date_current}"
        nested_dir = Path(f"../tmp/{self.analyze_dir}")
        nested_dir.mkdir(parents=True, exist_ok=True)

    """function to start recording"""

    def start_recordings(self):
        # Set flags to indicate recording is in progress
        self.recording_video = True
        self.recording_audio = True
        logg.app_logs(f"[INFO] Start recording")


        # Start audio and video recording in separate threads
        self.executor.submit(self.start_audio_recording)
        self.executor.submit(self.start_video_recording)

    """function to stop recording"""

    def stop_recordings(self):
        # Set flags to stop the recording
        self.recording_video = False
        self.recording_audio = False
        logg.app_logs(f"[INFO] Stopped recording")

        # Stop audio and video recording and release resources
        self.stop_video_recording()
        self.stop_audio_recording()

    """function to run methods for recording video"""

    def start_video_recording(self):
        # Initialize screen recorder for video
        self.screen_recorder = rec_vid.ScreenRecorder(self.record_dir)
        self.screen_recorder.start_record()  # Start recording video

    """function to run methods to stop recording video and release resources"""

    def stop_video_recording(self):
        if hasattr(self, "screen_recorder"):
            self.screen_recorder.stop_record()  # Stop recording video
            del self.screen_recorder  # Delete the screen recorder object

    """function to run methods for recording audio"""

    def start_audio_recording(self):
        # Initialize audio recorder for audio
        self.audio_recorder = rec_aud.AudioRecorder(f"../tmp/{self.record_dir}/audio_output.wav")
        self.audio_recorder.start_recording()  # Start recording audio

    """function to run methods to stop recording audio and release resources"""

    def stop_audio_recording(self):
        if hasattr(self, "audio_recorder"):
            # Stop the audio recording and store the file path
            self.existing_wav_file_to_process = self.audio_recorder.stop_recording()

    """function to run data analysis"""

    def start_data_analyze(self, temp_dir_name, note_datetime):
        try:
            # Call the data analysis method (e.g., transcription, etc.)
            data_analyze.main(
                temp_dir_name=temp_dir_name,
                filename_audio=self.existing_wav_file_to_process,
                filename_video=self.existing_mp4_file_to_process,
                application_name=self.existing_record_app_name,
                user_dir=self.existing_record_selected_dir_var,
                title=self.existing_record_file_name,
                datetime=note_datetime,
                n_frame=int(self.existing_record_frequency_comparison_sec),
                send_to_server=self.existing_record_send_to_server_from_new_window
            )
            self.master.after(0, lambda: logg.app_logs(f"[SUCCESS] Transcription finished"))  # Safely update the UI
        except Exception as e:
            logg.app_logs(f"[ERROR] Error in data_analyze: {e}")

    """function to retry sending files from server"""

    def retry_logic(self):
        retry_logic.retry_logic()  # Call the retry logic function

    """function to open directory picker in analysis window"""

    def open_directory_picker(self):
        selected_directory = filedialog.askdirectory(title="Choose directory")  # Open directory picker
        if selected_directory:
            self.existing_record_selected_dir_var = selected_directory  # Store the selected directory path

    """function to open download directory picker in existing recording analysis window"""

    def existing_record_open_directory_picker(self):
        selected_directory = filedialog.askdirectory(title="Choose directory")  # Open directory picker for download
        if selected_directory:
            self.existing_record_selected_dir_var = selected_directory  # Store the selected directory path

    """function to open directory picker in download window"""

    def open_download_directory_picker(self):
        selected_directory = filedialog.askdirectory(title="Choose directory")  # Open directory picker for download
        if selected_directory:
            self.selected_download_dir_var = selected_directory  # Store the selected download directory path

    """function to get values from different variables"""

    def save_name_dir_in_variables_existing_record(self):
        # Save various variables related to the existing recording and the selected directory
        self.existing_record_file_name = self.existing_record_entered_name.get()
        self.existing_record_send_to_server_from_new_window = self.existing_record_send_to_server_from_new_window_var.get()
        self.existing_wav_file_to_process = self.existing_wav_file_to_process_var.get()
        self.existing_mp4_file_to_process = self.existing_mp4_file_to_process_var.get()
        # Print the variables for debugging purposes

    """function to save audio and video files to user directory"""

    def save_audio_and_video_files(self):
        logg.app_logs(f"[INFO] Start saving files to user directory {self.selected_download_dir_var}")
        # Call a method to save the audio and video files to the selected directory
        sf.save_audio_and_video_files_to_user_directory(
            self.selected_download_dir_var,
            self.record_dir,
            self.existing_wav_file_to_process,
            self.existing_mp4_file_to_process
        )

    """function to run analysis in thread and create new directory for analysis"""

    def placeholder(self):
        # Create a new directory for analysis and run the data analysis in a separate thread
        self.new_directory_for_analyze()
        self.executor.submit(self.start_data_analyze, self.analyze_dir, self.date_var_analyze)

    """function to close application with threads"""

    def on_closing(self):
        """Closes the application and shuts down all tasks in the ThreadPoolExecutor."""
        logg.app_logs(f"[INFO] Shutting down executor")
        self.stop_video_recording()  # Stop video recording
        self.stop_audio_recording()  # Stop audio recording
        self.executor.shutdown(wait=False)  # Shutdown the executor and wait for tasks to finish
        logg.app_logs(f"[SUCCESS] Executor shut down")
        self.master.destroy()  # Destroy the main window
        sys.exit()  # Exit the application

    """create main app window"""
if __name__ == "__main__":
    # Create the main app window using `ttk.Window`
    app = ttk.Window("io_app", "superhero", resizable=(True, True))
    app.geometry("880x550")  # Set window size
    app.iconphoto(True, ttk.PhotoImage(file="assets/icon.png"))  # Set application icon
    IoFront(app)  # Initialize the main app logic
    app.mainloop()  # Start the Tkinter main loop to run the application
