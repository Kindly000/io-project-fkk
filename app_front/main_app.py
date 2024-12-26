import datetime
from concurrent.futures import ThreadPoolExecutor
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


os.chdir(os.path.dirname(os.path.abspath(__file__)))


class IoFront(ttk.Frame):
    def __init__(self, master_window):
        super().__init__(master_window, padding=(20, 10))
        self.grid(row=0, column=0)

        self.executor = ThreadPoolExecutor(max_workers=3)  # Zarządza wątkami
        self.recording_video = False
        self.recording_audio = False
        self.record_dir = ""

        self.left_container = ttk.LabelFrame(self, text="Recordings")
        self.left_container.pack(padx=5, pady=10, side=LEFT, fill=Y)

        self.application_name = ""  # nazwa wybranej aplikacji do nagrania

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

        # dodanie listy spotkań
        self.tree = self.create_treeview()

        self.right_container = ttk.Frame(self)

        self.drop_menu_app()

        # GUI setup
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

        self.right_container.pack(side=LEFT, padx=20, pady=10, fill=Y)

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
                tree.insert("", "end", values=i, tags="change_bg", iid=index)
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

    def drop_menu_app(self):
        mb = ttk.Menubutton(master=self.right_container, width=16, text="Application")
        mb.pack(padx=5, pady=10)
        options = ["MSTeams", "Zoom", "Google Meet"]
        inside_menu = ttk.Menu(mb, tearoff=0)

        def on_click(option):
            self.application_name = option
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
        button.bind("<Button-1>", lambda x: self.on_click_refresh())
        return button

    def on_click_refresh(self):
        data = com_www_server.get_info_of_notes_from_server()["notes"]
        print(data)
        index = 0
        for i in self.tree.get_children():
            self.tree.delete(i)

        for i in data:
            print(i)
            if int(index) % 2 == 1:
                self.tree.insert("", "end", values=i, tags="change_bg", iid=index)
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
            "<Button-1>", lambda e: [self.new_directory(), self.start_recordings()]
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
                self.google_.add_event("test", "date", "url"),
            ],
        )
        button.grid(row=2, column=1, padx=5, pady=10)
        return button

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
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.record_dir = f"recording_{current_time}"
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
            self.screen_recorder.stop_record()
            print(f"Video recording saved")

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
            self.executor.submit(self.start_data_analization, audio_filename)

    def start_data_analization(self, audio_filename):
        try:
            data_analyze.main(audio_filename, None)
            self.master.after(
                0, lambda: print("Transcription finished")
            )  # Update UI safely
        except Exception as e:
            print(f"Error in transcription: {e}")


if __name__ == "__main__":
    app = ttk.Window("io_app", "superhero", resizable=(True, True))
    app.geometry("900x500")
    app.iconphoto(True, ttk.PhotoImage(file="assets/icon.png"))
    IoFront(app)
    app.mainloop()
