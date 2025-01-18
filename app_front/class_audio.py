import time  # Library for time-related functions
import wave  # Library for working with WAV audio files
import pyaudio  # Library for audio streaming
import threading  # Library for handling threads
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

        # Initialize PyAudio instance
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.device_index = self.find_input_device()  # Find the input device
        self.frames = []  # Initialize the frames list to store audio chunks
        self.is_recording = False  # Flag to track recording status

        # Raise an error if 'Stereo Mix' device is not found
        if self.device_index is None:
            # raise ValueError(
            #     "No 'Stereo Mix' device found. Please ensure it's enabled."
            # )
            logg.app_logs(f"No 'Stereo Mix' device found. Please ensure it's enabled.")

    def find_input_device(self):
        """
        Finds the 'Stereo Mix' input device.

        This method searches through all available devices and returns the index
        of the device whose name contains 'stereo mix' or 'miks stereo'.
        """
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if "stereo mix" or "miks stereo" in device_info.get("name", "").lower():
                return i
        return None

    def start_recording(self):
        """
        Starts recording audio.

        This method initializes the audio stream and starts recording in a separate thread.
        """
        self.frames = []  # Clear previous frames
        self.stream = self.p.open(
            format=pyaudio.paInt16,  # Set audio format to 16-bit PCM
            channels=self.channels,  # Set number of channels
            rate=self.rate,  # Set sample rate
            input=True,  # Open the stream for input (recording)
            input_device_index=self.device_index,  # Use the found 'Stereo Mix' device
            frames_per_buffer=self.chunk,  # Set buffer size (number of frames per chunk)
        )
        self.is_recording = True  # Set the recording flag to True
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(target=self.record_chunks)
        self.recording_thread.start()

    def record_chunks(self):
        """
        Records audio chunks in a separate thread.

        This method reads chunks of audio data from the input stream and appends them to the frames list.
        """
        while self.is_recording:
            data = self.stream.read(self.chunk)  # Read a chunk of audio data
            self.frames.append(data)  # Store the chunk in the frames list

    def stop_recording(self):
        """
        Stops the recording and saves the audio to a file.

        This method stops the recording, waits for the recording thread to finish,
        and writes the recorded frames to a WAV file.
        """
        logg.app_logs(f"[INFO] class_audio Stopping recording")
        self.is_recording = False  # Stop recording
        self.recording_thread.join()  # Wait for the recording thread to finish

        if self.stream:
            self.stream.stop_stream()  # Stop the audio stream
            self.stream.close()  # Close the stream
            self.stream = None

            # Save the recorded audio as a WAV file
            with wave.open(self.filename, "wb") as wf:
                wf.setnchannels(self.channels)  # Set the number of channels
                wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))  # Set sample width
                wf.setframerate(self.rate)  # Set the sample rate
                wf.writeframes(b"".join(self.frames))  # Write the frames to the file

            logg.app_logs(f"[SUCCESS] Recording finished. File saved as '{self.filename}'. ")
            return self.filename

    def terminate(self):
        """
        Terminates the PyAudio instance.

        This method releases resources used by PyAudio.
        """
        self.p.terminate()


# Example usage
if __name__ == "__main__":
    try:
        recorder = AudioRecorder("audio_output.wav")  # Create an AudioRecorder instance

        # Start recording
        recorder.start_recording()

        # Simulate recording for 6 seconds
        time.sleep(6)

        # Stop recording
        recorder.stop_recording()

    except ValueError as e:
        logg.app_logs(f"[ERROR] {e}")  # Print error if no Stereo Mix device is found

    finally:
        # Clean up resources
        if "recorder" in locals():
            recorder.terminate()
