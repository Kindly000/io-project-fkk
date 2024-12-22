import functools
import logging
import math
from pyannote.audio import Pipeline
from faster_whisper import WhisperModel
from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor

model_size = "small"


# 1. Transkrypcja pliku audio za pomocą Whisper
def transcribe_audio(file_path):
    try:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(
            file_path,
            task="transcribe",
            beam_size=2,
            temperature=0.0,
            no_speech_threshold=0.1,
            word_timestamps=True,
        )
        result_segments = []
        for segment in segments:
            print(segment)
            result_segments.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                }
            )
        return result_segments
    except Exception as e:
        print(f"Transcription Error: {e}")


# 2. Rozpoznawanie rozmówców audio za pomocą pyannote.audio
def diarize_audio(file_path, hf_token):
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", use_auth_token=hf_token
        )
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


def notes_summary(tekst):
    summarizer = pipeline(
        "summarization",
        model="facebook/bart-large-cnn",
        tokenizer="facebook/bart-large-cnn",
    )

    summary = summarizer(tekst, max_length=130, min_length=30, do_sample=False)

    return summary[0]["summary_text"]


# 4. Główna funkcja
def main(filename="./testowe_pliki/test_wyklad.wav"):
    audio_file = f"{filename}"
    hf_token = "..."
    tekst = ""

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

        try:
            filename = filename[0 : -(len(filename.split("/").pop()))]
            note_content_text = []
            note_content_speaker = []
            summary = ""
            # Wyświetlenie wyników
            for entry in combined:
                if len(note_content_text) == 0 or note_content_speaker[-1]["name"] != entry["speaker"]:
                    speaker = {
                        "type": "speaker",
                        "timestamp": math.floor(float(entry["start"])),
                        "name": f"{entry["speaker"]}",
                    }
                    note_content_speaker.append(speaker)

                text = {
                    "type": "text",
                    "timestamp": math.floor(float(entry["start"])),
                    "value": f"{entry["text"]}",
                }
                note_content_text.append(text)
                
                tekst = (
                    tekst
                    + f"[{entry['start']:.2f}s - {entry['end']:.2f}s] {entry['speaker']}: {entry['text']}\n"
                )

            summary = notes_summary(tekst)
            # docx_file.close()
        except Exception as e:
            print(f"Error generating docx file: {e}")
    

if __name__ == "__main__":
    main()
