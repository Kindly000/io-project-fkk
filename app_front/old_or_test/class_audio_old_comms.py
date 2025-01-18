import time
import wave
import pyaudio
import threading
import app_backend.logging_f as logg # Logging file


class AudioRecorder:
    def __init__(self, filename, channels=2, rate=44100, chunk=1024):
        """
        Constructor for the AudioRecorder class.

        Args:
            filename (str): The name of the file where the recorded audio will be saved.
            channels (int): The number of audio channels (default is 2, stereo).
            rate (int): The sample rate (default is 44100 Hz).
            chunk (int): The size of each audio chunk (default is 1024).

        Variables:
            self.p: The PyAudio object used to manage audio streams.
            self.stream: The stream object for audio input.
            self.device_index: The index of the input device for audio capture.
            self.frames: A list that holds chunks of recorded audio.
            self.is_recording: A flag indicating if recording is in progress.
        """

        self.filename = filename
        self.channels = channels
        self.rate = rate
        self.chunk = chunk

        # Inicjalizacja PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.device_index = self.find_input_device()
        self.frames = []
        self.is_recording = False

        if self.device_index is None:
            logg.app_logs(f"[INFO] Start saving files to user directory {self.selected_download_dir_var}")

    def find_input_device(self):
        """Znajduje urządzenie wejściowe 'Stereo Mix'."""
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if "stereo mix" or "miks stereo" in device_info.get("name", "").lower():
                return i
        return None

    def start_recording(self):
        """Rozpoczyna nagrywanie dźwięku."""
        print("Rozpoczynanie nagrywania dźwięku...")
        self.frames = []  # Wyczyszczenie wcześniejszych danych
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk,
        )
        self.is_recording = True
        # Rozpoczynamy nagrywanie w osobnym wątku
        self.recording_thread = threading.Thread(target=self.record_chunks)
        self.recording_thread.start()

    def record_chunks(self):
        """Nagrywa pojedyncze bloki danych w wątku."""
        while self.is_recording:
            data = self.stream.read(self.chunk)
            self.frames.append(data)

    def stop_recording(self):
        """Zatrzymuje nagrywanie i zapisuje dane do pliku."""
        print("Zatrzymywanie nagrywania...")
        self.is_recording = False  # Zatrzymujemy nagrywanie
        self.recording_thread.join()  # Czekamy na zakończenie wątku nagrywania

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

            # Zapisz nagrany dźwięk do pliku WAV
            with wave.open(self.filename, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.rate)
                wf.writeframes(b"".join(self.frames))

            print(f"Nagrywanie zakończone. Plik zapisany jako '{self.filename}'.")
            return self.filename

    def terminate(self):
        """Zamyka PyAudio."""
        self.p.terminate()


# Przykład użycia
if __name__ == "__main__":
    try:
        recorder = AudioRecorder("aiduoasdh.wav")

        # Rozpocznij nagrywanie
        recorder.start_recording()

        # Symulacja czasu nagrywania (6 sekund)
        time.sleep(6)

        # Zatrzymaj nagrywanie
        recorder.stop_recording()

    except ValueError as e:
        print(e)

    finally:
        # Zwolnij zasoby
        if "recorder" in locals():
            recorder.terminate()
