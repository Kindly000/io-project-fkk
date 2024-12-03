import datetime
from concurrent.futures import ThreadPoolExecutor
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
import subprocess

import class_record as rec_vid
import class_audio as rec_aud

class IoFront(ttk.Frame):
    def __init__(self, master_window):
        super().__init__(master_window, padding=(20, 10))
        self.grid(row=0, column=0)

        self.executor = ThreadPoolExecutor(max_workers=2)  # Zarządza wątkami
        self.recording_video = False
        self.recording_audio = False
        self.record_dir = ""

        self.left_container = ttk.LabelFrame(self, text="Recordings")
        self.left_container.pack(padx=5, pady=10, side=LEFT, fill=Y)
        # dodanie listy spotkań
        self.tree = self.create_treeview()

        self.right_container = ttk.Frame(self)

        # GUI setup
        self.new_record_container = ttk.LabelFrame(self.right_container, text="New recording")
        self.start_recording_button()
        self.stop_recording_button()
        self.new_record_container.pack(padx=5, pady=10)

        self.action_container = ttk.LabelFrame(self.right_container, text="Manage recording")
        self.open_in_browser_button()
        self.delete_recording_button()
        self.action_container.pack(padx=5, pady=10)

        self.right_container.pack(side=LEFT, padx=20, pady=10, fill=Y)

    def create_treeview(self):
        columns = ["id", "date", "name"]
        tree = ttk.Treeview(master=self.left_container, bootstyle="secondary", columns=columns, show='headings', height=20)
        tree.grid_configure(row=0, column=0, columnspan=4, rowspan=5, padx=20, pady=10)

        tree.column("id", width=50, anchor=CENTER)
        tree.column("date", anchor=CENTER)
        tree.column("name", anchor=CENTER)

        tree.heading("id", text="id")
        tree.heading("date", text="date")
        tree.heading("name", text="name")

        tree.tag_configure('change_bg', background="#20374C")

        # data = get_data_locally()  # importowanie danych z pliku

        return tree

    def open_in_browser_button(self):
        button = ttk.Button(master=self.action_container, width=20, text="Open in browser")
        button.grid(row=3, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        return button

    def delete_recording_button(self):
        button = ttk.Button(master=self.action_container, width=20, text="Delete recording")
        button.grid(row=5, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        return button

    def start_recording_button(self):
        button = ttk.Button(master=self.new_record_container, width=20, text="Start recording")
        button.bind("<Button-1>", lambda e: [
            self.new_directory(),
            self.start_recordings()
        ])
        button.grid(row=1, column=1, padx=5, pady=10)
        return button

    def stop_recording_button(self):
        button = ttk.Button(master=self.new_record_container, width=20, text="Stop recording")
        button.bind("<Button-1>", lambda e: [
            self.stop_recordings(),
            self.combining_recordings()
        ])
        button.grid(row=2, column=1, padx=5, pady=10)
        return button

    def combining_recordings(self):
        cmd = f"ffmpeg -i ../tmp/{self.record_dir}/audio_output.wav -i ../tmp/{self.record_dir}/video_output.avi -c:v libx264 -c:a aac -strict experimental ../tmp/{self.record_dir}/combined.mp4"
        subprocess.call(cmd, shell=True)  # "Muxing Done
        print('Muxing Done')

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
        if hasattr(self, 'screen_recorder'):
            print("Stopping video recording...")
            self.screen_recorder.stop_record()
            print(f"Video recording saved")

    def start_audio_recording(self):
        print("Audio recording thread started")
        self.audio_recorder = rec_aud.AudioRecorder(f"../tmp/{self.record_dir}/audio_output.wav")  # Utwórz obiekt nagrywania audio
        self.audio_recorder.start_recording()  # Rozpocznij nagrywanie
        print("Audio recording started")

    def stop_audio_recording(self):
        if hasattr(self, 'audio_recorder'):
            print("Stopping audio recording...")
            self.audio_recorder.stop_recording()
            print("Audio recording stopped")




if __name__ == "__main__":
    app = ttk.Window("io_app", "superhero", resizable=(True, True))
    app.geometry("900x500")
    IoFront(app)
    app.mainloop()
