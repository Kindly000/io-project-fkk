import functools
import logging
import math
import subprocess
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

# 4. Generowanie podsumowań notatek
def notes_summary(tekst: str):
    summarizer = pipeline(
        "summarization",
        model="facebook/bart-large-cnn",
        tokenizer="facebook/bart-large-cnn",
    )

    summary = summarizer(tekst, max_length=130, min_length=30, do_sample=False)

    return summary[0]["summary_text"]

# 5. Wydobywanie ramek z wideo do dalszej analizy
def get_video_frames(file_path: str):
    file_name_match = re.search(r"/([\w]+)(\.[a-zA-Z0-9]+)", file_path)
    file_name = file_name_match.group(1)

    output_dir = f"./testowe/{file_name}/"
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Directory {output_dir} is ready.")
    except Exception as e:
        print(f"Failed to create directory {output_dir}: {e}")
        return

    output_pattern = f"{output_dir}%d.png"
    ffmpeg_command = [
        "ffmpeg",
        "-i",
        file_path,
        "-vf",
        "fps=1",
        "-frame_pts",
        "1",  # Use frame presentation timestamps
        output_pattern,
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Frames successfully extracted to {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg execution failed: {e}")
    except FileNotFoundError:
        print("FFmpeg not found. Make sure it is installed and in your PATH.")
        
"""
def teams_screen_analyze(img_nr_1: int = None, img_nr_2: int = None):
    image1 = cv2.imread(
        f"./testowe/nagranie_testowe_teams/{img_nr_1}.png", cv2.IMREAD_GRAYSCALE
    )
    image2 = cv2.imread(f"./testowe/teams_screen_template.png", cv2.IMREAD_GRAYSCALE)

    sift = cv2.SIFT_create()

    kp, des = sift.detectAndCompute(image1, None)
    kp1, des1 = sift.detectAndCompute(image2, None)

    bf = cv2.BFMatcher()

    matches = bf.knnMatch(des, des1, k=2)
    best = []
    for match1, match2 in matches:
        if match1.distance < 0.85 * match2.distance:
            best.append([match1])

    # print(best)

    sift_matches = cv2.drawMatchesKnn(image1, kp, image2, kp1, best, None, flags=2)
    plt.imshow(sift_matches)
    plt.show()

    print(
        f"Liczba dopasowanych punktów obraz nr {img_nr_1} do obrazu nr {img_nr_2}: {len(best)}"
    )
"""


# 6. Główna funkcja
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
