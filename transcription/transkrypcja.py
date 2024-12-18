import whisper
import functools
import logging
from pyannote.audio import Pipeline
from concurrent.futures import ThreadPoolExecutor


# 1. Transkrypcja pliku audio za pomocą Whisper
def transcribe_audio(file_path):
    try:
        whisper.torch.load = functools.partial(whisper.torch.load, weights_only=True)
        model = whisper.load_model("large")
        result = model.transcribe(
            file_path,
            task="transcribe",
            fp16=False,
            logprob_threshold=-1.0,
            suppress_tokens="",
        )
        return result["segments"]
    except Exception as e:
        print(f"Transciption Error: {e}")


# 2. Diarizacja pliku audio za pomocą pyannote.audio
def diarize_audio(file_path, hf_token):
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", use_auth_token=hf_token
        )
        logging.getLogger("speechbrain.utils.quirks").setLevel(logging.WARNING)
        diarization = pipeline(file_path)
        return diarization
    except Exception as e:
        print(f"Diarization Error: {e}")


# 3. Łączenie transkrypcji i diarizacji
def combine_transcription_and_diarization(segments, diarization):
    combined_results = []
    previous_segment = None

    for segment in segments:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"]
        speaker = None

        # Iteruj po wszystkich wynikach diarization
        for turn, _, spk in diarization.itertracks(yield_label=True):
            # Sprawdź, czy przedziały czasowe się pokrywają
            if turn.start < end and turn.end > start:
                speaker = spk
                break

        # Jeśli segment i poprzedni segment mają tego samego mówiącego i ten sam tekst
        if (
            previous_segment
            and previous_segment["speaker"] == speaker
            and previous_segment["text"] == text
        ):
            # Połącz segmenty: połącz czas końcowy poprzedniego segmentu z obecnym
            previous_segment["end"] = end
        else:
            if previous_segment:
                # Zakończ poprzedni segment
                combined_results.append(previous_segment)
            # Rozpocznij nowy segment
            previous_segment = {
                "start": start,
                "end": end,
                "speaker": speaker,
                "text": text,
            }

    # Dodaj ostatni segment, jeśli istnieje
    if previous_segment:
        combined_results.append(previous_segment)

    return combined_results


def notes_summary(filename):
    None

# 4. Główna funkcja
def main(filename="./audio_output_2.wav"):
    audio_file = f"{filename}"
    hf_token = "..."

    with ThreadPoolExecutor(max_workers=2) as executor:
        # Wysyłanie obu zadań do executor w tym samym czasie
        future_transcription_segments = executor.submit(transcribe_audio, audio_file)
        future_diarization_result = executor.submit(diarize_audio, audio_file, hf_token)

        # Oczekiwanie na zakończenie zadań i pobranie wyników
        transcription_segments = future_transcription_segments.result()
        diarization_result = future_diarization_result.result()

        print(transcription_segments)
        print(diarization_result)

        # Połączenie wyników
        combined = combine_transcription_and_diarization(
            transcription_segments, diarization_result
        )

        try:
            filename = filename[0 : -(len(filename.split("/").pop()))]
            docx_file = open(f"{filename}transcription.doc", "w+")

            # Wyświetlenie wyników
            for entry in combined:
                print(
                    f"[{entry['start']:.2f}s - {entry['end']:.2f}s] {entry['speaker']}: {entry['text']}"
                )
                docx_file.write(
                    f"[{entry['start']:.2f}s - {entry['end']:.2f}s] {entry['speaker']}: {entry['text']}\n"
                )

            docx_file.close()
        except Exception as e:
            print(f"Error generating docx file: {e}")


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


# main()
