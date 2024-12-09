import whisper
import functools
from pyannote.audio import Pipeline
from concurrent.futures import ThreadPoolExecutor


# 1. Transkrypcja pliku audio za pomocą Whisper
def transcribe_audio(file_path):
    whisper.torch.load = functools.partial(whisper.torch.load, weights_only=True)
    model = whisper.load_model("small")
    result = model.transcribe(file_path, task="transcribe", fp16=False)
    return result["segments"]


# 2. Diarizacja pliku audio za pomocą pyannote.audio
def diarize_audio(file_path, hf_token):
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token=hf_token
    )
    diarization = pipeline(file_path)
    return diarization


# 3. Łączenie transkrypcji i diarizacji
def combine_transcription_and_diarization(segments, diarization):
    combined_results = []

    for segment in segments:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"]

        # Iteruj po wszystkich wynikach diarization
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            # Sprawdź, czy przedziały czasowe się pokrywają
            if turn.start < end and turn.end > start:
                combined_results.append(
                    {
                        "start": max(turn.start, start),
                        "end": min(turn.end, end),
                        "speaker": speaker,
                        "text": text,
                    }
                )

    return combined_results


# 4. Główna funkcja
def main(filename="../tmp/recording_2024-12-09_15-44-41/audio_output.wav"):
    audio_file = f"{filename}"
    hf_token = "..."

    with ThreadPoolExecutor(max_workers=2) as executor:
        # Wysyłanie obu zadań do executor w tym samym czasie
        future_transcription_segments = executor.submit(transcribe_audio, audio_file)
        future_diarization_result = executor.submit(diarize_audio, audio_file, hf_token)

        # Oczekiwanie na zakończenie zadań i pobranie wyników
        transcription_segments = future_transcription_segments.result()
        diarization_result = future_diarization_result.result()

        # Połączenie wyników
        combined = combine_transcription_and_diarization(
            transcription_segments, diarization_result
        )

        filename = filename[0 : -(len(filename.split("/").pop()))]
        docx_file = open(f'{filename}transcription.doc', "w+")

        # Wyświetlenie wyników
        for entry in combined:
            print(
                f"[{entry['start']:.2f}s - {entry['end']:.2f}s] {entry['speaker']}: {entry['text']}"
            )
            docx_file.write(
                f"[{entry['start']:.2f}s - {entry['end']:.2f}s] {entry['speaker']}: {entry['text']}\n"
            )
        docx_file.close()

    """
    # Transkrypcja
    transcription_segments = transcribe_audio(audio_file)

    # Diarizacja
    diarization_result = diarize_audio(audio_file, hf_token)

    # Połączenie wyników
    combined = combine_transcription_and_diarization(
        transcription_segments, diarization_result
    )

    # Wyświetlenie wyników
    for entry in combined:
        print(
            f"[{entry['start']:.2f}s - {entry['end']:.2f}s] {entry['speaker']}: {entry['text']}"
        )
    """

main()
