import wave
import pyaudio
import datetime


class AudioRecorder:
    def __init__(self, filename='output.wav', channels=2, rate=44100, chunk=1024):
        self.filename = filename
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        # self.record_seconds = record_seconds

        # Inicjalizacja PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.device_index = self.find_input_device()
        self.frames = []

        if self.device_index is None:
            raise ValueError("Nie znaleziono urządzenia 'Stereo Mix'. Upewnij się, że jest włączone.")

    def find_input_device(self):
        """Znajduje urządzenie wejściowe 'Stereo Mix'."""
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if "stereo mix"or "miks stereo" in device_info.get("name", "").lower():
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
        print("Nagrywanie rozpoczęte dźwięku.")

    def record_chunk(self):
        """Nagrywa pojedynczy blok danych."""
        if self.stream:
            data = self.stream.read(self.chunk)
            self.frames.append(data)

    def stop_recording(self):
        """Zatrzymuje nagrywanie i zapisuje dane do pliku."""
        if self.stream:
            print("Zatrzymywanie nagrywania...")
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

            # Zapisz nagrany dźwięk do pliku WAV
            with wave.open(self.filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))

            print(f"Nagrywanie zakończone. Plik zapisany jako '{self.filename}'.")

    def terminate(self):
        """Zamyka PyAudio."""
        self.p.terminate()


# Przykład użycia
# if __name__ == "__main__":
#     try:
#         recorder = AudioRecorder(record_seconds=5)
#
#         # Rozpocznij nagrywanie
#         recorder.start_recording()
#
#         # Nagrywaj przez ustalony czas
#         for _ in range(0, int(recorder.rate / recorder.chunk * recorder.record_seconds)):
#             recorder.record_chunk()
#
#         # Zatrzymaj nagrywanie
#         recorder.stop_recording()
#
#     except ValueError as e:
#         print(e)
#
#     finally:
#         # Zwolnij zasoby
#         if 'recorder' in locals():
#             recorder.terminate()
