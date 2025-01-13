from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tkinter import filedialog, BooleanVar
from tkinter import Toplevel
import re

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
import subprocess
import webbrowser
import os

import app_front.class_record as rec_vid
import app_front.class_audio as rec_aud
from data_analyze import data_analyze
import app_backend.communication_with_www_server as com_www_server

import app_front.quickstart as google_cal

import app_backend.retry_logic as retry_logic


os.chdir(os.path.dirname(os.path.abspath(__file__)))


class IoFront(ttk.Frame):
    def __init__(self, master_window):
        """Iinitialation of main window"""
        super().__init__(master_window, padding=(20, 10))
        self.grid(row=0, column=0)

        """threading"""
        self.executor = ThreadPoolExecutor(max_workers=3)  # Zarządza wątkami
        self.recording_video = False
        self.recording_audio = False

        """directory to tmp files"""
        self.record_dir = ""

        """logowanie do google"""
        self.google_ = google_cal.Calendar()

        """pobieranie danych z serwera"""
        self.import_from_server = com_www_server.get_info_of_notes_from_server()
        if self.import_from_server is not None:
            self.imported_notes = self.import_from_server["notes"]
        else:
            self.imported_notes = []
        # print(self.imported_notes[0]["note_id"])
        self.clicked_note = ""

        """date variable"""
        self.date_var = None
        # dodanie listy spotkań

        """variables for stop recording windows"""
        self.frequency_comparison_sec = "5"
        self.selected_download_dir_var = "../default_save_folder"
        self.selected_dir_var = "../default_save_folder"
        self.entered_dir = ttk.StringVar()
        self.file_name = "notatka_testowa"
        self.entered_name = ttk.StringVar()
        self.application_name = "MSTeams"  # nazwa wybranej aplikacji do nagrania
        self.send_to_server_from_new_window_var = BooleanVar()
        self.send_to_server_from_new_window = True


        """variables for processing recording windows from main"""



        """GUI setup"""
        self.left_container = ttk.LabelFrame(self, text="Recordings")
        self.left_container.pack(padx=5, pady=10, side=LEFT, fill=Y)
        self.tree = self.create_treeview()
        self.create_scrollbar_for_treeview()
        self.right_container = ttk.Frame(self)
        self.new_record_container = ttk.LabelFrame(
            self.right_container, text="New recording"
        )
        self.start_recording_button()
        self.stop_recording_button()
        self.new_record_container.pack(padx=5, pady=10)

        self.action_container = ttk.LabelFrame(
            self.right_container, text="Manage recording"
        )
        self.open_in_browser_button()
        self.refresh_button()
        self.action_container.pack(padx=5, pady=10)

        self.search_container = ttk.LabelFrame(self.right_container, text="Search")
        self.search_entry = self.create_entry()
        self.create_search_button()
        self.search_container.pack(padx=5, pady=10)

        self.right_container.pack(side=LEFT, padx=20, pady=10, fill=Y)

        """resend failed files function"""
        self.send_failed_files()

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
            # tree.bind("<Button-3>", self.identify_item)

            index += 1

        return tree

    def tree_on_click_element(self, event):
        clickedItem = self.tree.focus()
        print(self.tree.item(clickedItem)["values"])
        self.clicked_note = self.tree.item(clickedItem)["values"][0]
        return

    def create_scrollbar_for_treeview(self):
        scrollbar = ttk.Scrollbar(
            master=self.left_container, orient="vertical", command=self.tree.yview
        )
        scrollbar.grid(row=0,rowspan=5, column=4, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def process_files_main_app_button(self):
        button = ttk.Button(
            master=self.action_container, width=20, text="Process files"
        )
        button.grid(row=1, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        button.bind(
            "<Button-1>",
            lambda x: [
                self.start_processing_button_new_window()
            ]
        )

    def create_entry(self):
        entry = ttk.Entry(master=self.search_container, width=20)
        entry.pack(padx=5, pady=10)
        return entry

    def create_search_button(self):
        button = ttk.Button(master=self.search_container, width=20, text="Search")
        button.bind("<Button-1>", lambda x: self.on_click_search())
        button.pack(padx=5, pady=10)
        return button

    def drop_menu_app(self, master):
        mb = ttk.Menubutton(master=master, width=16, text="Application")
        mb.pack(padx=5, pady=10)
        options = ["MSTeams", "Zoom", "Google Meet"]
        inside_menu = ttk.Menu(mb, tearoff=0)

        def on_click(option):
            self.application_name = option
            mb.config(text=option)
            print(option)

        for option in options:
            inside_menu.add_radiobutton(
                label=option, command=lambda x=option: on_click(x)
            )
        mb["menu"] = inside_menu

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

    def refresh_button(self):
        button = ttk.Button(master=self.action_container, width=20, text="Refresh")
        button.grid(row=5, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        button.bind(
            "<Button-1>", lambda x: [self.on_click_refresh(), self.send_failed_files()]
        )
        return button

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
            # tree.bind("<Button-3>", self.identify_item)

            index += 1

        return

    def on_click_search(self):
        get_text = self.search_entry.get()
        data = com_www_server.get_info_of_notes_from_server_if_note_contain_search_word(
            get_text
        )["notes"]
        # print(data)
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
            # tree.bind("<Button-3>", self.identify_item)

            index += 1

        return

    def start_recording_button(self):
        button = ttk.Button(
            master=self.new_record_container, width=20, text="Start recording"
        )
        button.bind(
            "<Button-1>", lambda e: [
                self.new_directory(),
                self.start_recordings()
            ]
        )
        button.grid(row=1, column=1, padx=5, pady=10)
        return button

    def stop_recording_button(self):
        button = ttk.Button(
            master=self.new_record_container, width=20, text="Stop recording"
        )
        button.bind(
            "<Button-1>",
            lambda e: [
                self.stop_recordings(),
                self.combining_recordings(),
                self.stop_recording_button_new_window(),
            ],
        )
        button.grid(row=2, column=1, padx=5, pady=10)
        return button

    def stop_recording_button_new_window(self):
        new_window = Toplevel(self.new_record_container)
        new_window.title("Choose action")
        new_window.geometry("400x300")

        download_label = ttk.Label(new_window, text="Select dir to local download", font=("Arial", 9))
        download_label.pack(pady=10)
        button_dir = ttk.Button(new_window, text="Choose directory")
        button_dir.bind("<Button-1>", lambda e: [self.open_download_directory_picker(),button_dir.config(text=self.selected_download_dir_var)])
        button_dir.pack(pady=10)
        download_button = ttk.Button(new_window, text="Download")
        download_button.bind("<Button-1>", lambda e: [print(self.selected_download_dir_var),new_window.destroy()])
        download_button.pack(pady=10)
        info_label = ttk.Label(new_window,text="Download files locally, later still you can make notes from them",font=("Arial", 9), bootstyle="secondary")
        info_label.pack(pady=10)

        process_recording_label = ttk.Label(new_window, text="Process recording", font=("Arial", 9))
        process_recording_label.pack(pady=10)
        process_recording_button = ttk.Button(new_window, text="Process recording")
        process_recording_button.pack(pady=10)
        process_recording_button.bind(
            "<Button-1>",
            lambda e: [
                self.start_processing_button_new_window(),
                new_window.destroy()
            ]
        )

    def start_processing_button_new_window(self):
        def validate_title():
            """Sprawdza, czy tytuł spełnia wymagania."""
            title = entry_title.get()
            # Definicja regex dla poprawnych nazw (np. tylko litery, cyfry, myślniki, podkreślenia)
            if not re.match(r"^[\w\-. ]+$", title):
                validation_label.config( text="Nazwa może zawierać tylko litery, cyfry, spacje, myślniki i podkreślenia!", bootstyle="danger",)
                return False
            validation_label.config(text="Nazwa poprawna!", bootstyle="success")
            return True

        new_window = Toplevel(self.new_record_container)
        new_window.title("Details")
        new_window.geometry("300x700")

        # Dodanie treści do nowego okna
        label_paths = ttk.Label(new_window, text="Paths to files", font=("Arial", 9))
        label_paths.pack(pady=10)

        entry_path_wav = ttk.Entry(new_window, width=30, state="normal")
        entry_path_wav.insert(0, f"../tmp/{self.record_dir}/audio_output.wav")
        entry_path_wav.config(state="readonly")
        entry_path_wav.pack(pady=10)

        entry_path_avi = ttk.Entry(new_window, width=30, state="normal")
        entry_path_avi.insert(0, f"../tmp/{self.record_dir}/video_output.avi")
        entry_path_avi.config(state="readonly")
        entry_path_avi.pack(pady=10)

        label_title = ttk.Label(new_window, text="Enter note title", font=("Arial", 9))
        label_title.pack(pady=10)

        entry_title = ttk.Entry(new_window, width=30, textvariable=self.entered_name)
        entry_title.insert(0, f"New_Note_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
        entry_title.pack(pady=10)

        # Etykieta do wyświetlania wyników walidacji
        validation_label = ttk.Label(new_window, text="", font=("Arial", 9))
        validation_label.pack(pady=5)

        label_dir = ttk.Label(new_window, text="Choose directory for note", font=("Arial", 9))
        label_dir.pack(pady=10)

        button_dir = ttk.Button(new_window, text="Choose directory")
        button_dir.bind(
            "<Button-1>",
            lambda e: [
                self.open_directory_picker(),
                button_dir.config(text=self.selected_dir_var),
            ],
        )
        button_dir.pack(pady=10)

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

        def on_click_sec(option):
            self.frequency_comparison_sec = option
            mb_sec.config(text=option)
            print(option)

        for option in options_sec:
            inside_menu_sec.add_radiobutton(
                label=option, command=lambda x=option: on_click_sec(x)
            )
        mb_sec["menu"] = inside_menu_sec

        checkbox_label = ttk.Label(new_window, text="Send to server", font=("Arial", 9))
        checkbox_label.pack(pady=10)
        self.send_to_server_from_new_window_var.set(True)
        checkbox = ttk.Checkbutton(new_window, variable=self.send_to_server_from_new_window_var)
        checkbox.pack(pady=10)

        """Start processing files button"""
        start_process_button = ttk.Button(
            new_window,
            text="Start processing",
        )
        start_process_button.bind(
            "<Button-1>",
            lambda e: [
                validate_title() and self.save_name_dir_in_variables(),
                new_window.destroy() if validate_title() else None,
            ],
        )
        start_process_button.pack(pady=10)

    def start_processing_button_main_app(self):
        def validate_title():
            """Sprawdza, czy tytuł spełnia wymagania."""
            title = entry_title.get()
            # Definicja regex dla poprawnych nazw (np. tylko litery, cyfry, myślniki, podkreślenia)
            if not re.match(r"^[\w\-. ]+$", title):
                validation_label.config( text="Nazwa może zawierać tylko litery, cyfry, spacje, myślniki i podkreślenia!", bootstyle="danger",)
                return False
            validation_label.config(text="Nazwa poprawna!", bootstyle="success")
            return True

        new_window = Toplevel(self.new_record_container)
        new_window.title("Details")
        new_window.geometry("300x700")

        # Dodanie treści do nowego okna
        label_paths = ttk.Label(new_window, text="Paths to files", font=("Arial", 9))
        label_paths.pack(pady=10)

        entry_path_wav = ttk.Entry(new_window, width=30, state="normal")
        entry_path_wav.insert(0, f"../tmp/{self.record_dir}/audio_output.wav")
        entry_path_wav.pack(pady=10)

        entry_path_avi = ttk.Entry(new_window, width=30, state="normal")
        entry_path_avi.insert(0, f"../tmp/{self.record_dir}/video_output.avi")
        entry_path_avi.pack(pady=10)

        label_title = ttk.Label(new_window, text="Enter note title", font=("Arial", 9))
        label_title.pack(pady=10)

        entry_title = ttk.Entry(new_window, width=30, textvariable=self.entered_name)
        entry_title.insert(0, f"New_Note_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
        entry_title.pack(pady=10)

        # Etykieta do wyświetlania wyników walidacji
        validation_label = ttk.Label(new_window, text="", font=("Arial", 9))
        validation_label.pack(pady=5)

        label_dir = ttk.Label(new_window, text="Choose directory for note", font=("Arial", 9))
        label_dir.pack(pady=10)

        button_dir = ttk.Button(new_window, text="Choose directory")
        button_dir.bind(
            "<Button-1>",
            lambda e: [
                self.open_directory_picker(),
                button_dir.config(text=self.selected_dir_var),
            ],
        )
        button_dir.pack(pady=10)

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

        def on_click_sec(option):
            self.frequency_comparison_sec = option
            print(option)

        for option in options_sec:
            inside_menu_sec.add_radiobutton(
                label=option, command=lambda x=option: on_click_sec(x)
            )
        mb_sec["menu"] = inside_menu_sec

        checkbox_label = ttk.Label(new_window, text="Send to server", font=("Arial", 9))
        checkbox_label.pack(pady=10)
        self.send_to_server_from_new_window_var.set(True)
        checkbox = ttk.Checkbutton(new_window, variable=self.send_to_server_from_new_window_var)
        checkbox.pack(pady=10)

        # JKV for start_data_analization
        # temp_dir_name = self.record_dir
        # audio_filename = entry_path_wav.get()
        # print()
        # filename_video = f"../tmp/{self.record_dir}/combined.mp4"
        # application_name = self.application_name
        # user_dir = self.selected_dir_var
        # title = self.file_name
        # n_frame = int(self.frequency_comparison_sec)
        # send_to_server = self.send_to_server_from_new_window_var.get()

        """Start processing files button"""
        start_process_button = ttk.Button(
            new_window,
            text="Start processing",
        )
        start_process_button.bind(
            "<Button-1>",
            lambda e: [
                validate_title() and self.save_name_dir_in_variables(),
                self.executor.submit(
                    self.start_data_analization,
                    self.record_dir,
                    entry_path_wav.get(),
                    f"../tmp/{self.record_dir}/combined.mp4",
                    self.application_name,
                    self.selected_dir_var,
                    self.file_name,
                    int(self.frequency_comparison_sec),
                    self.send_to_server_from_new_window
                ) if validate_title() else None,
                new_window.destroy() if validate_title() else None,
            ],
        )
        start_process_button.pack(pady=10)

    def combining_recordings(self):
        self.executor.submit(self._combining_recordings)

    def _combining_recordings(self):
        try:
            cmd = f"ffmpeg -i ../tmp/{self.record_dir}/audio_output.wav -i ../tmp/{self.record_dir}/video_output.avi -c:v libx264 -c:a aac -strict experimental ../tmp/{self.record_dir}/combined.mp4"
            with open(f"../tmp/{self.record_dir}/ffmpeg_log", "w") as log_file:
                subprocess.call(
                    cmd, shell=True, stdout=log_file, stderr=subprocess.STDOUT
                )
            print("Muxing Done")
        except Exception as e:
            print(f"Muxing Error {e}")

    def new_directory(self):
        self.date_var = datetime.now()
        date_current = self.date_var.strftime("%Y-%m-%d_%H-%M-%S")
        self.record_dir = f"recording_{date_current}"
        nested_dir = Path(f"../tmp/{self.record_dir}")
        nested_dir.mkdir(parents=True, exist_ok=True)

    def start_recordings(self):
        # Ustaw flagi na True, aby rozpocząć nagrywanie
        self.recording_video = True
        self.recording_audio = True
        print("Starting recordings...")

        # Przekaż funkcje do executor
        self.executor.submit(self.start_audio_recording)
        self.executor.submit(self.start_video_recording)

    def stop_recordings(self):
        # Ustaw flagi na False, aby zatrzymać nagrywanie
        self.recording_video = False
        self.recording_audio = False
        print("Stopping recordings...")

        # Wywołaj metody zatrzymania nagrywania
        self.stop_video_recording()
        self.stop_audio_recording()

    # Twoje istniejące metody
    def start_video_recording(self):
        print("Video recording thread started")
        self.screen_recorder = rec_vid.ScreenRecorder(self.record_dir)
        print("Initializing screen recorder...")
        self.screen_recorder.start_record()
        print("Video recording started")

    def stop_video_recording(self):
        if hasattr(self, "screen_recorder"):
            print("Stopping video recording...")
            self.screen_recorder.stop_record()  # Zatrzymanie nagrywania i zwolnienie pliku
            del self.screen_recorder  # Usuń obiekt, aby upewnić się, że zasoby są zwolnione
            print("Video recording stopped and resources released.")

    def start_audio_recording(self):
        print("Audio recording thread started")
        self.audio_recorder = rec_aud.AudioRecorder(
            f"../tmp/{self.record_dir}/audio_output.wav"
        )  # Utwórz obiekt nagrywania audio
        self.audio_recorder.start_recording()  # Rozpocznij nagrywanie
        print("Audio recording started")

    def stop_audio_recording(self):
        if hasattr(self, "audio_recorder"):
            print("Stopping audio recording...")
            audio_filename = self.audio_recorder.stop_recording()
            print("Audio recording stopped")
            # video_filename = f"../tmp/{self.record_dir}/video_output.avi"  # Zakładając, że to nazwa pliku wideo

    def start_data_analization(self, temp_dir_name, audio_filename, filename_video, application_name, user_dir, title,
                               n_frame, send_to_server):
        print("XD")
        try:
            print("S")
            data_analyze.main(
                temp_dir_name=temp_dir_name,
                filename_audio=audio_filename,
                filename_video=filename_video,
                application_name=application_name,
                user_dir=user_dir,
                title=title,
                datetime=self.date_var,
                n_frame=n_frame,
                send_to_server=send_to_server
            )
            print("K")
            self.master.after(
                0, lambda: print("Transcription finished")
            )  # Update UI safely
        except Exception as e:
            print(f"Error in data_analyze: {e}")

    def send_failed_files(self):
        retry_logic.send_failed_files()

    def open_directory_picker(self):
        """Funkcja otwierająca okienko do wyboru katalogu."""
        selected_directory = filedialog.askdirectory(title="Choose directory")
        if selected_directory:
            self.selected_dir_var = selected_directory

    def open_download_directory_picker(self):
        """Funkcja otwierająca okienko do wyboru katalogu."""
        selected_directory = filedialog.askdirectory(title="Choose directory")
        if selected_directory:
            self.selected_download_dir_var = selected_directory

    def save_name_dir_in_variables(self):
        self.file_name = self.entered_name.get()
        self.send_to_server_from_new_window = self.send_to_server_from_new_window_var.get()
        print([self.file_name, self.selected_dir_var, self.application_name, self.frequency_comparison_sec, self.send_to_server_from_new_window])

    def funkcja_do_zapisu_plikow_jkv(self, chosen_dir, tmp_dir):
        print("sigma")


if __name__ == "__main__":
    app = ttk.Window("io_app", "superhero", resizable=(True, True))
    app.geometry("900x500")
    app.iconphoto(True, ttk.PhotoImage(file="assets/icon.png"))
    IoFront(app)
    app.mainloop()
