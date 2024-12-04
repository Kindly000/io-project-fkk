import soundcard as sc
import soundfile as sf
import threading
import numpy as np


class AudioRecorder:
    def __init__(self, filename):
        self.filename = filename
        self.sample_rate = 48000
        self.is_recording = False
        self.thread = None
        self.buffer = []

    def start_recording(self):
        """Start recording audio in a separate thread."""
        if self.is_recording:
            print("Recording is already in progress.")
            return
        self.is_recording = True
        self.buffer = []
        self.thread = threading.Thread(target=self._record)
        self.thread.start()

    def stop_recording(self):
        """Stop the recording and save the audio to a file."""
        if not self.is_recording:
            print("No recording in progress to stop.")
            return
        self.is_recording = False
        self.thread.join()  # Wait for the recording thread to finish
        # Save the audio to file
        if self.buffer:
            data = np.concatenate(self.buffer, axis=0)
            sf.write(file=self.filename, data=data, samplerate=self.sample_rate)
            print(f"Recording saved to {self.filename}")
        else:
            print("No data recorded.")

    def _record(self):
        """Internal method to handle audio recording."""
        try:
            with sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True).recorder(
                    samplerate=self.sample_rate) as mic:
                while self.is_recording:
                    # Mniejszy bufor (np. 0.05 sekundy)
                    data = mic.record(numframes=int(self.sample_rate * 0.05))
                    self.buffer.append(data[:, 0])  # Użyj jednego kanału
        except Exception as e:
            print(f"Error during recording: {e}")
            self.is_recording = False


if __name__ == "__main__":
    recorder = AudioRecorder("test.wav")
    try:
        print("Starting recording...")
        recorder.start_recording()
        input("Press Enter to stop recording...\n")  # Wait for user input to stop
        recorder.stop_recording()
    except KeyboardInterrupt:
        print("Recording interrupted.")
        recorder.stop_recording()
