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
import app_front.class_record as rec_vid
import app_front.class_audio as rec_aud
from data_analyze import data_analyze
import app_backend.communication_with_www_server as com_www_server
import app_backend.save_files as sf
import app_front.quickstart as google_cal
import app_backend.retry_logic as retry_logic
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class IoFront(ttk.Frame):
    def __init__(self, master_window):
        """Iinitialation of main window"""
        super().__init__(master_window, padding=(20, 10))
        self.grid(row=0, column=0)

        """threading"""
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.recording_video = False
        self.recording_audio = False
        self.is_record_in_progress = False

        """directory to tmp files"""
        self.record_dir = ""
        self.analyze_dir = ""

        """logowanie do google"""
        self.google_ = google_cal.Calendar()

        """pobieranie danych z serwera"""
        self.import_from_server = com_www_server.get_info_of_notes_from_server()
        if self.import_from_server is not None:
            self.imported_notes = self.import_from_server["notes"]
        else:
            self.imported_notes = []
        self.clicked_note = ""

        """date variable"""
        self.date_var = None
        self.date_var_analyze = None

        """variables for processing recording windows from main"""
        self.selected_download_dir_var = "../default_save_folder"
        self.existing_record_frequency_comparison_sec = "5"
        self.existing_record_selected_dir_var = "../default_save_folder"
        self.existing_record_file_name = "notatka_testowa"
        self.existing_record_entered_name = ttk.StringVar()
        self.existing_record_app_name = "MSTeams"
        self.existing_record_send_to_server_from_new_window_var = BooleanVar()
        self.existing_record_send_to_server_from_new_window = True
        self.existing_wav_file_to_process_var = ttk.StringVar()
        self.existing_mp4_file_to_process_var = ttk.StringVar()
        self.existing_wav_file_to_process = ""
        self.existing_mp4_file_to_process = ""

        """GUI setup"""
        """left container"""
        self.left_container = ttk.LabelFrame(self, text="Recordings")
        self.left_container.pack(padx=5, pady=10, side=LEFT, fill=Y)
        self.tree = self.create_treeview()
        self.create_scrollbar_for_treeview()

        """right container"""
        self.right_container = ttk.Frame(self)
        self.new_record_container = ttk.LabelFrame(
            self.right_container, text="New recording"
        )
        self.start_recording_button()
        self.stop_recording_button()
        self.new_record_container.pack(padx=5, pady=10)

        """action container"""
        self.action_container = ttk.LabelFrame(
            self.right_container, text="Manage recording"
        )
        self.open_in_browser_button()
        self.refresh_button()
        self.process_files_main_app_button()
        self.action_container.pack(padx=5, pady=10)
        """search container and entry and button"""
        self.search_container = ttk.LabelFrame(self.right_container, text="Search")
        self.search_entry = self.create_entry()
        self.create_search_button()
        self.search_container.pack(padx=5, pady=10)
        self.right_container.pack(side=LEFT, padx=20, pady=10, fill=Y)

        """resend failed files function"""
        self.send_failed_files()
        
        master_window.protocol("WM_DELETE_WINDOW", self.on_closing)

    """create treeview and scrollbar for it"""
    def create_treeview(self):
        columns = ["id", "date", "name"]
        tree = ttk.Treeview(
            master=self.left_container,
            bootstyle="secondary",
            columns=columns,
            show="headings",
            height=20,
        )
        tree.grid_configure(row=0, column=0, columnspan=4, rowspan=5, padx=20, pady=10)

        tree.column("id", width=50, anchor=CENTER)
        tree.column("date", anchor=CENTER)
        tree.column("name", anchor=CENTER)

        tree.heading("id", text="id")
        tree.heading("date", text="date")
        tree.heading("name", text="name")

        tree.tag_configure("change_bg", background="#20374C")

        data = self.imported_notes

        tree.tag_configure("change_bg", background="#20374C")
        index = 0
        for i in data:
            print(i)
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
            tree.bind("<<TreeviewSelect>>", self.tree_on_click_element)

            index += 1

        return tree

    """create element for treeview"""
    def tree_on_click_element(self, event):
        clickedItem = self.tree.focus()
        print(self.tree.item(clickedItem)["values"])
        self.clicked_note = self.tree.item(clickedItem)["values"][0]
        return

    """create scrollbar for treeview"""
    def create_scrollbar_for_treeview(self):
        scrollbar = ttk.Scrollbar(
            master=self.left_container, orient="vertical", command=self.tree.yview
        )
        scrollbar.grid(row=0,rowspan=5, column=4, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    """create button for processing existing files"""
    def process_files_main_app_button(self):
        button = ttk.Button(
            master=self.action_container, width=20, text="Process files"
        )
        button.grid(row=1, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        button.bind(
            "<Button-1>",
            lambda x: [
                self.start_processing_button_main_app()
            ]
        )

    """create entry widged"""
    def create_entry(self):
        entry = ttk.Entry(master=self.search_container, width=20)
        entry.pack(padx=5, pady=10)
        return entry

    """create search button for treeview and entry"""
    def create_search_button(self):
        button = ttk.Button(master=self.search_container, width=20, text="Search")
        button.bind("<Button-1>", lambda x: self.on_click_search())
        button.pack(padx=5, pady=10)
        return button

    """create drop menu to choose application for recording"""
    def drop_menu_app(self, master):
        mb = ttk.Menubutton(master=master, width=16, text="Application")
        mb.pack(padx=5, pady=10)
        options = ["MSTeams", "Zoom", "Google Meet"]
        inside_menu = ttk.Menu(mb, tearoff=0)

        def on_click(option):
            self.existing_record_app_name = option
            mb.config(text=option)
            print(option)

        for option in options:
            inside_menu.add_radiobutton(
                label=option, command=lambda x=option: on_click(x)
            )
        mb["menu"] = inside_menu

    """create drop menu to choose application for recording for processing existing files window"""
    def existing_record_drop_menu_app(self, master):
        mb = ttk.Menubutton(master=master, width=16, text="Application")
        mb.pack(padx=5, pady=10)
        options = ["MSTeams", "Zoom", "Google Meet"]
        inside_menu = ttk.Menu(mb, tearoff=0)

        def on_click(option):
            self.existing_record_app_name = option
            mb.config(text=option)
            print(option)

        for option in options:
            inside_menu.add_radiobutton(
                label=option, command=lambda x=option: on_click(x)
            )
        mb["menu"] = inside_menu

    """create button for opening recording in browser for main window"""
    def open_in_browser_button(self):
        button = ttk.Button(
            master=self.action_container, width=20, text="Open in browser"
        )
        button.grid(row=3, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        button.bind(
            "<Button-1>",
            lambda x: webbrowser.open_new(
                f"https://ioprojekt.atwebpages.com/{self.clicked_note}"
            ),
        )
        return button

    """create refresh button for treeview for main window"""
    def refresh_button(self):
        button = ttk.Button(master=self.action_container, width=20, text="Refresh")
        button.grid(row=5, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        button.bind(
            "<Button-1>", lambda x: [self.on_click_refresh(), self.send_failed_files()]
        )
        return button

    """create function to send data to server on click refresh button for main window"""
    def on_click_refresh(self):
        data = com_www_server.get_info_of_notes_from_server()["notes"]
        print(data)
        index = 0
        for i in self.tree.get_children():
            self.tree.delete(i)

        for i in data:
            # print(i)
            if int(index) % 2 == 1:
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
            self.tree.bind("<<TreeviewSelect>>", self.tree_on_click_element)

            index += 1

        return

    """create data search function for treeview for main window on click search button"""
    def on_click_search(self):
        data = ""
        get_text = self.search_entry.get()
        if com_www_server.get_info_of_notes_from_server_if_note_contain_search_word(
            get_text
        ) is not None:
            data = com_www_server.get_info_of_notes_from_server_if_note_contain_search_word(
                get_text
            )["notes"]

        if data != "":
            index = 0
            for i in self.tree.get_children():
                self.tree.delete(i)

            for i in data:
                # print(i)
                if int(index) % 2 == 1:
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
                self.tree.bind("<<TreeviewSelect>>", self.tree_on_click_element)

                index += 1

        return

    """create button to start recording for main window, creates new directory for recording"""
    def start_recording_button(self):
        button = ttk.Button(
            master=self.new_record_container, width=20, text="Start recording"
        )

        """check if record is in progress"""
        def check_if_record_in_progress():
            if not self.is_record_in_progress:
                self.is_record_in_progress = True
                self.new_directory(),
                self.start_recordings()

        button.bind(
            "<Button-1>", lambda e: [
                check_if_record_in_progress(),
            ]
        )
        button.grid(row=1, column=1, padx=5, pady=10)
        return button

    """create button to stop recording for main window, combines recordings, opens new window for further actions"""
    def stop_recording_button(self):
        button = ttk.Button(
            master=self.new_record_container, width=20, text="Stop recording"
        )

        """check if record is in progress"""
        def check_if_record_in_progress():
            if self.is_record_in_progress:
                self.is_record_in_progress = False
                self.stop_recordings()
                self.combining_recordings()
                self.stop_recording_button_new_window()

        button.bind(
            "<Button-1>",
            lambda e: [
                check_if_record_in_progress()
            ],
        )
        button.grid(row=2, column=1, padx=5, pady=10)
        return button

    """new action window after finishing recording """
    def stop_recording_button_new_window(self):

        """check if combined.mp4 file is present"""
        def check_file_presence():
            if self.record_dir:
                file_path = os.path.join("../tmp/",self.record_dir, "combined.mp4")
                if os.path.isfile(file_path):
                    return  True
                else:
                    print(f"File not found: {file_path}")
                    return False
            else:
                print("Record directory not set.")

            """check if file is present and start processing if so"""
        def check_file_and_process():
            if check_file_presence():
                self.start_processing_button_new_window(),
                new_window.destroy()

        def check_file_and_download():
            if check_file_presence():
                print(self.selected_download_dir_var)
                self.save_audio_and_video_files()

        """new window"""
        new_window = Toplevel(self.new_record_container)
        new_window.title("Choose action")
        new_window.geometry("400x300")

        """label and button to choose directory for download"""
        download_label = ttk.Label(new_window, text="Select dir to local download", font=("Arial", 9))
        download_label.pack(pady=10)
        button_dir = ttk.Button(new_window, text="Choose directory")
        button_dir.bind("<Button-1>",
                        lambda e: [self.open_download_directory_picker(),
                                button_dir.config(text=self.selected_download_dir_var)
                                ])
        button_dir.pack(pady=10)
        download_button = ttk.Button(new_window, text="Download")
        download_button.bind("<Button-1>",
                             lambda e: [
                                 check_file_and_download(),
                             ])
        download_button.pack(pady=10)


        """label and button to choose directory for processing"""
        info_label = ttk.Label(new_window, text="Download files locally, later still you can make notes from them", font=("Arial", 9), bootstyle="secondary")
        info_label.pack(pady=10)

        process_recording_label = ttk.Label(new_window, text="Process recording", font=("Arial", 9))
        process_recording_label.pack(pady=10)

        process_recording_button = ttk.Button(new_window, text="Process recording")
        process_recording_button.pack(pady=10)
        process_recording_button.bind(
            "<Button-1>",
            lambda e: [
                check_file_and_process()
            ]
        )
        check_file_presence()

    """record processing window after finishing recording"""
    def start_processing_button_new_window(self):

        """validating name of the file"""
        def validate_title():
            title = entry_title.get()
            if not re.match(r"^[\w\-. ]+$", title):
                validation_label.config( text="Nazwa może zawierać tylko litery, cyfry, spacje, myślniki i podkreślenia!", bootstyle="danger",)
                return False
            if(title == ""):
                validation_label.config(text="Nie może być pusta",bootstyle="danger", )
                return False
            validation_label.config(text="Nazwa poprawna!", bootstyle="success")
            return True

        """creating new window"""
        new_window = Toplevel(self.new_record_container)
        new_window.title("Details")
        new_window.geometry("300x700")

        """adding labels and entries to the window for showing directories"""
        label_paths = ttk.Label(new_window, text="Paths to files", font=("Arial", 9))
        label_paths.pack(pady=10)

        entry_path_wav = ttk.Entry(new_window, width=30, state="normal", textvariable=self.existing_wav_file_to_process_var)
        entry_path_wav.delete(0, END)
        entry_path_wav.insert(0, self.existing_wav_file_to_process)
        entry_path_wav.config(state="readonly")
        entry_path_wav.pack(pady=10)

        entry_path_mp4 = ttk.Entry(new_window, width=30, state="normal", textvariable=self.existing_mp4_file_to_process_var)
        entry_path_mp4.delete(0, END)
        entry_path_mp4.insert(0, self.existing_mp4_file_to_process)
        entry_path_mp4.config(state="readonly")
        entry_path_mp4.pack(pady=10)

        """adding labels and entries to the window to get title of the note"""
        label_title = ttk.Label(new_window, text="Enter note title", font=("Arial", 9))
        label_title.pack(pady=10)

        entry_title = ttk.Entry(new_window, width=30, textvariable=self.existing_record_entered_name)
        # entry_title.insert(0, f"New_Note_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
        entry_title.pack(pady=10)

        validation_label = ttk.Label(new_window, text="", font=("Arial", 9))
        validation_label.pack(pady=5)

        """adding labels and entries to the window to get directory of the note"""
        label_dir = ttk.Label(new_window, text="Choose directory for note", font=("Arial", 9))
        label_dir.pack(pady=10)

        button_dir = ttk.Button(new_window, text="Choose directory")
        button_dir.bind(
            "<Button-1>",
            lambda e: [
                self.open_directory_picker(),
                button_dir.config(text=self.existing_record_selected_dir_var),
            ],
        )
        button_dir.pack(pady=10)


        """adding labels and entries to the window to get app of the note and checkboxes for sending to server and frequency of comparison"""
        label_app = ttk.Label(new_window, text="Choose app", font=("Arial", 9))
        label_app.pack(pady=10)
        self.drop_menu_app(new_window)

        label_seconds = ttk.Label(
            new_window, text="Enter frequency of comparison", font=("Arial", 9)
        )
        label_seconds.pack(pady=10)

        mb_sec = ttk.Menubutton(new_window, width=16, text="Seconds")
        mb_sec.pack(padx=5, pady=10)
        options_sec = ["5", "6", "7", "9", "10"]
        inside_menu_sec = ttk.Menu(mb_sec, tearoff=0)

        """on click element in frequency of comparison menu"""
        def on_click_sec(option):
            self.existing_record_frequency_comparison_sec = option
            mb_sec.config(text=option)
            print(option)

        for option in options_sec:
            inside_menu_sec.add_radiobutton(
                label=option, command=lambda x=option: on_click_sec(x)
            )
        mb_sec["menu"] = inside_menu_sec

        checkbox_label = ttk.Label(new_window, text="Send to server", font=("Arial", 9))
        checkbox_label.pack(pady=10)
        self.existing_record_send_to_server_from_new_window_var.set(True)
        checkbox = ttk.Checkbutton(new_window, variable=self.existing_record_send_to_server_from_new_window_var)
        checkbox.pack(pady=10)

        """Start processing files button"""
        start_process_button = ttk.Button(
            new_window,
            text="Start processing",
        )
        start_process_button.bind(
            "<Button-1>",
            lambda e: [
                validate_title() and self.save_name_dir_in_variables_existing_record(),
                self.executor.submit(self.start_data_analyze, self.record_dir, self.date_var) if validate_title() else None,
                new_window.destroy() if validate_title() else None,
            ],
        )
        start_process_button.pack(pady=10)

    """open processing menu for existing recording from main window"""
    def start_processing_button_main_app(self):

        """validating name of the file"""
        def validate_title():
            title = entry_title.get()
            if not re.match(r"^[\w\-. ]+$", title):
                validation_label.config(text="Nazwa może zawierać tylko litery, cyfry, spacje, myślniki i podkreślenia!", bootstyle="danger",)
                return False
            if (title == ""):
                validation_label.config(text="Nie może być pusta", bootstyle="danger", )
                return False
            if (self.existing_wav_file_to_process =="" or self.existing_mp4_file_to_process == ""):
                validation_label.config(text="Nie może być pusta", bootstyle="danger", )
                return False
            validation_label.config(text="Nazwa poprawna!", bootstyle="success")
            return True

        """creating new window"""
        new_window = Toplevel(self.new_record_container)
        new_window.title("Process existing recording")
        new_window.geometry("300x700")

        """adding labels and entries to the window for choosing files directories"""
        label_paths = ttk.Label(new_window, text="Paths to files", font=("Arial", 9))
        label_paths.pack(pady=10)

        """button to choose .wav file directory"""
        def existing_record_wav_files_directory_picker():
            selected_directory = filedialog.askopenfilename(title="Choose file", filetypes=[("WAV files", "*.wav")] )
            if selected_directory:
                self.existing_wav_file_to_process = selected_directory
                self.existing_wav_file_to_process_var.set(selected_directory)
            else:
                self.existing_wav_file_to_process = ""
                self.existing_wav_file_to_process_var.set("")

        button_wav_dir = ttk.Button(new_window, text="Choose .wav file")
        button_wav_dir.bind(
            "<Button-1>",
            lambda e: [
                existing_record_wav_files_directory_picker(),
                button_wav_dir.config(text=self.existing_wav_file_to_process),
            ],
        )
        button_wav_dir.pack(pady=10)

        """button to choose .mp4 file directory"""
        def existing_record_mp4_files_directory_picker():
            selected_directory = filedialog.askopenfilename(title="Choose file", filetypes=[("MP4 files", "*.mp4")])
            if selected_directory:
                self.existing_mp4_file_to_process = selected_directory
                self.existing_mp4_file_to_process_var.set(selected_directory)
            else:
                self.existing_mp4_file_to_process = ""
                self.existing_mp4_file_to_process_var.set("")

        button_mp4_dir = ttk.Button(new_window, text="Choose .mp4 file")
        button_mp4_dir.bind(
            "<Button-1>",
            lambda e: [
                existing_record_mp4_files_directory_picker(),
                button_mp4_dir.config(text=self.existing_mp4_file_to_process),
            ],
        )
        button_mp4_dir.pack(pady=10)

        """adding labels and entries to the window to get title of the note"""
        label_title = ttk.Label(new_window, text="Enter note title", font=("Arial", 9))
        label_title.pack(pady=10)

        entry_title = ttk.Entry(new_window, width=30, textvariable=self.existing_record_entered_name)
        # entry_title.insert(0, f"New_Note_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
        entry_title.pack(pady=10)

        validation_label = ttk.Label(new_window, text="", font=("Arial", 9))
        validation_label.pack(pady=5)

        """adding labels and entries to the window to get directory of the note"""
        label_dir = ttk.Label(new_window, text="Choose directory for note", font=("Arial", 9))
        label_dir.pack(pady=10)

        button_dir = ttk.Button(new_window, text="Choose directory")
        button_dir.bind(
            "<Button-1>",
            lambda e: [
                self.existing_record_open_directory_picker(),
                button_dir.config(text=self.existing_record_selected_dir_var),
            ],
        )
        button_dir.pack(pady=10)

        """adding labels and entries to the window to get app of the note and checkboxes for sending to server and frequency of comparison"""
        label_app = ttk.Label(new_window, text="Choose app", font=("Arial", 9))
        label_app.pack(pady=10)
        self.existing_record_drop_menu_app(new_window)

        label_seconds = ttk.Label(
            new_window, text="Enter frequency of comparison", font=("Arial", 9)
        )
        label_seconds.pack(pady=10)

        mb_sec = ttk.Menubutton(new_window, width=16, text="Seconds")
        mb_sec.pack(padx=5, pady=10)
        options_sec = ["5", "6", "7", "9", "10"]
        inside_menu_sec = ttk.Menu(mb_sec, tearoff=0)

        """on click element in frequency of comparison menu"""
        def on_click_sec(option):
            self.existing_record_frequency_comparison_sec = option
            print(option)

        for option in options_sec:
            inside_menu_sec.add_radiobutton(
                label=option, command=lambda x=option: on_click_sec(x)
            )
        mb_sec["menu"] = inside_menu_sec

        checkbox_label = ttk.Label(new_window, text="Send to server", font=("Arial", 9))
        checkbox_label.pack(pady=10)
        self.existing_record_send_to_server_from_new_window_var.set(True)
        checkbox = ttk.Checkbutton(new_window, variable=self.existing_record_send_to_server_from_new_window_var)
        checkbox.pack(pady=10)

        """Start processing files button"""
        start_process_button = ttk.Button(
            new_window,
            text="Start processing",
        )
        start_process_button.bind(
            "<Button-1>",
            lambda e: [
                validate_title() and self.save_name_dir_in_variables_existing_record(),
                self.placeholder() if validate_title() else None,
                new_window.destroy() if validate_title() else None,
            ],
        )
        start_process_button.pack(pady=10)

    """function to run in thread combine audio and video files"""
    def combining_recordings(self):
        self.executor.submit(self._combining_recordings)

    """function to combine audio and video files by using ffmpeg"""
    def _combining_recordings(self):
        try:
            cmd = f"ffmpeg -i ../tmp/{self.record_dir}/audio_output.wav -i ../tmp/{self.record_dir}/video_output.avi -c:v libx264 -c:a aac -strict experimental ../tmp/{self.record_dir}/combined.mp4"
            with open(f"../tmp/{self.record_dir}/ffmpeg_log", "w") as log_file:
                subprocess.call(
                    cmd, shell=True, stdout=log_file, stderr=subprocess.STDOUT
                )
            print("Muxing Done")
            self.existing_mp4_file_to_process = f"../tmp/{self.record_dir}/combined.mp4"
        except Exception as e:
            print(f"Muxing Error {e}")

    """function to create new directory for notes"""
    def new_directory(self):
        self.date_var = datetime.now()
        date_current = self.date_var.strftime("%Y-%m-%d_%H-%M-%S")
        self.record_dir = f"files_for_notes_{date_current}"
        nested_dir = Path(f"../tmp/{self.record_dir}")
        nested_dir.mkdir(parents=True, exist_ok=True)

    """function to create new directory for notes from analysis window"""
    def new_directory_for_analyze(self):
        self.date_var_analyze = datetime.now()
        date_current = self.date_var_analyze.strftime("%Y-%m-%d_%H-%M-%S")
        self.analyze_dir = f"files_for_notes_{date_current}"
        nested_dir = Path(f"../tmp/{self.analyze_dir}")
        nested_dir.mkdir(parents=True, exist_ok=True)

    """function to start recording"""
    def start_recordings(self):
        self.recording_video = True
        self.recording_audio = True
        print("Starting recordings...")

        self.executor.submit(self.start_audio_recording)
        self.executor.submit(self.start_video_recording)

    """function to stop recording"""
    def stop_recordings(self):
        self.recording_video = False
        self.recording_audio = False
        print("Stopping recordings...")

        self.stop_video_recording()
        self.stop_audio_recording()

    """function to run methods for recording video"""
    def start_video_recording(self):
        print("Video recording thread started")
        self.screen_recorder = rec_vid.ScreenRecorder(self.record_dir)
        print("Initializing screen recorder...")
        self.screen_recorder.start_record()
        print("Video recording started")

    """function to run methods to stop recording video and release resources"""
    def stop_video_recording(self):
        if hasattr(self, "screen_recorder"):
            print("Stopping video recording...")
            self.screen_recorder.stop_record()
            del self.screen_recorder
            print("Video recording stopped and resources released.")

    """function to run methods for recording audio"""
    def start_audio_recording(self):
        print("Audio recording thread started")
        self.audio_recorder = rec_aud.AudioRecorder(
            f"../tmp/{self.record_dir}/audio_output.wav"
        )
        self.audio_recorder.start_recording()
        print("Audio recording started")

    """function to run methods to stop recording audio and release resources"""
    def stop_audio_recording(self):
        if hasattr(self, "audio_recorder"):
            print("Stopping audio recording...")
            self.existing_wav_file_to_process = self.audio_recorder.stop_recording()
            print("Audio recording stopped")
            # video_filename = f"../tmp/{self.record_dir}/video_output.avi"  # Zakładając, że to nazwa pliku wideo

    """function to run data analysis"""
    def start_data_analyze(self, temp_dir_name, note_datetime):
        try:
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
            self.master.after(
                0, lambda: print("Transcription finished")
            )  # Update UI safely
        except Exception as e:
            print(f"Error in data_analyze: {e}")

    """function to retry sending files from server"""
    def send_failed_files(self):
        retry_logic.send_failed_files()

    """function to open directory picker in analysis window"""
    def open_directory_picker(self):
        selected_directory = filedialog.askdirectory(title="Choose directory")
        if selected_directory:
            self.existing_record_selected_dir_var = selected_directory

    """function to open download directory picker in existing recording analysis window"""
    def existing_record_open_directory_picker(self):
        selected_directory = filedialog.askdirectory(title="Choose directory")
        if selected_directory:
            self.existing_record_selected_dir_var = selected_directory

    """function to open directory picker in download window"""
    def open_download_directory_picker(self):
        selected_directory = filedialog.askdirectory(title="Choose directory")
        if selected_directory:
            self.selected_download_dir_var = selected_directory

    """function to get values from different variables"""
    def save_name_dir_in_variables_existing_record(self):
        # if(self.existing_record_entered_name.get()==""):
        #     self.existing_record_entered_name.set(f"New_Note_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
        self.existing_record_file_name = self.existing_record_entered_name.get()
        self.existing_record_send_to_server_from_new_window = self.existing_record_send_to_server_from_new_window_var.get()
        self.existing_wav_file_to_process = self.existing_wav_file_to_process_var.get()
        self.existing_mp4_file_to_process = self.existing_mp4_file_to_process_var.get()
        print([self.existing_wav_file_to_process, self.existing_mp4_file_to_process, self.existing_record_file_name, self.existing_record_selected_dir_var, self.existing_record_app_name, self.existing_record_frequency_comparison_sec, self.existing_record_send_to_server_from_new_window])

    """function to save audio and video files to user directory"""
    def save_audio_and_video_files(self):
        sf.save_audio_and_video_files_to_user_directory(
            self.selected_download_dir_var,
            self.record_dir,
            self.existing_wav_file_to_process,
            self.existing_mp4_file_to_process
        )

    """function to run analysis in thread and create new directory for analysis"""
    def placeholder(self):
        self.new_directory_for_analyze()
        self.executor.submit(self.start_data_analyze, self.analyze_dir, self.date_var_analyze)


    """function to close application with threads"""
    def on_closing(self):
        """Zamyka aplikację i kończy wszystkie zadania w ThreadPoolExecutor."""
        print("Shutting down executor...")
        self.stop_video_recording()
        self.stop_audio_recording()
        self.executor.shutdown(wait=False)  # Czeka na zakończenie wszystkich zadań
        print("Executor shut down. Closing application.")
        self.master.destroy()  # Zamyka główne okno aplikacji
        sys.exit()

"""create main app window"""
if __name__ == "__main__":
    app = ttk.Window("io_app", "superhero", resizable=(True, True))
    app.geometry("880x550")
    app.iconphoto(True, ttk.PhotoImage(file="assets/icon.png"))
    IoFront(app)
    app.mainloop()
