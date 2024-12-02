import wave
import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2  # Stereo
RATE = 44100
RECORD_SECONDS = 5
OUTPUT_FILENAME = 'output.wav'

# Inicjalizacja PyAudio
p = pyaudio.PyAudio()

# Wyszukiwanie odpowiedniego urządzenia wejściowego (np. "Stereo Mix")
def find_input_device():
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if "stereo mix" in device_info.get("name", "").lower():
            return i
    return None

device_index = find_input_device()
if device_index is None:
    print("Nie znaleziono urządzenia 'Stereo Mix'. Upewnij się, że jest włączone.")
    exit()

# Ustawienia pliku WAV
with wave.open(OUTPUT_FILENAME, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)

    # Otwórz strumień
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,  # Użyj wybranego urządzenia
                    frames_per_buffer=CHUNK)

    print("Recording...")

    # Nagrywanie dźwięku
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        wf.writeframes(data)

    print("Recording finished.")

    # Zamknięcie strumienia
    stream.stop_stream()
    stream.close()

# Zamknięcie PyAudio
p.terminate()
