import functools
import logging
import math
import subprocess
import re
import os
import cv2
import time
import os
from openai import OpenAI
from pyannote.audio import Pipeline
from faster_whisper import WhisperModel
from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor
from app_backend.logging_f import log_data_analyze
import app_backend.save_files as sf
import data_analyze.image_files_analyze as image_analyzer
from datetime import datetime

model_size = "small"
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# 1. Transkrypcja pliku audio za pomocą Whisper
def transcribe_audio(file_path: str) -> list[dict]:
    """
    Transkrypcja pliku audio na tekst.

    Args:
        file_path (str): Ścieżka do pliku audio.

    Returns:
        list[dict]: Lista segmentów transkrypcji zawierająca czas rozpoczęcia, czas zakończenia i tekst.

    Notes:
        - Funkcja korzysta z modelu Whisper.
        - W przypadku wystąpienia błędu informacja jest logowana do pliku za pomocą `log_data_analyze`.
    """
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
            result_segments.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                }
            )
        log_data_analyze(f"Transcription completed successfully for {file_path}.")
        return result_segments
    except Exception as e:
        log_data_analyze(f"Transcription Error for {file_path}: {e}")
        return []


# 2. Rozpoznawanie rozmówców audio za pomocą pyannote.audio
def diarize_audio(file_path: str, hf_token: str) -> object:
    """
    Diarizacja audio - rozpoznawanie rozmówców w pliku audio.

    Args:
        file_path (str): Ścieżka do pliku audio.
        hf_token (str): Token do autentykacji w HuggingFace.

    Returns:
        object: Wynik diarizacji zawierający informacje o rozmówcach.

    Notes:
        - Funkcja używa modelu pyannote do diarizacji.
        - W przypadku wystąpienia błędu informacja jest logowana do pliku za pomocą `log_data_analyze`.
    """
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", use_auth_token=hf_token
        )
        diarization = pipeline(file_path)
        log_data_analyze(f"Diarization completed successfully for {file_path}.")
        return diarization
    except Exception as e:
        log_data_analyze(f"Diarization Error for {file_path}: {e}")
        return None


# 3. Łączenie transkrypcji i diarizacji
def combine_transcription_and_diarization(
    segments: list[dict], diarization: object
) -> list[dict]:
    """
    Łączenie wyników transkrypcji i diarizacji.

    Args:
        segments (list[dict]): Lista segmentów transkrypcji.
        diarization (object): Wyniki diarizacji rozmówców.

    Returns:
        list[dict]: Lista połączonych wyników zawierających informacje o czasie i mówiącym.

    Notes:
        - Funkcja łączy dane na podstawie nakładających się przedziałów czasowych.
        - Informacje o sukcesie lub błędach są logowane do pliku.
    """
    try:
        combined_results = []
        previous_segment = None

        for segment in segments:
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]
            speaker = None

            for turn, _, spk in diarization.itertracks(yield_label=True):
                if turn.start < end and turn.end > start:
                    speaker = spk
                    break

            if (
                previous_segment
                and previous_segment["speaker"] == speaker
                and previous_segment["text"] == text
            ):
                previous_segment["end"] = end
            else:
                if previous_segment:
                    combined_results.append(previous_segment)
                previous_segment = {
                    "start": start,
                    "end": end,
                    "speaker": speaker,
                    "text": text,
                }

        if previous_segment:
            combined_results.append(previous_segment)

        log_data_analyze("Transcription and diarization combined successfully.")
        return combined_results
    except Exception as e:
        log_data_analyze(f"Error combining transcription and diarization: {e}")
        return []


# 4. Generowanie podsumowań notatek
def notes_summary(tekst: str) -> str:
    """
    Generowanie podsumowań notatek.

    Args:
        tekst (str): Tekst, który ma zostać podsumowany.

    Returns:
        str: Streszczenie tekstu.

    Notes:
        - Funkcja korzysta z API CHatGPT-4o do generowania podsumowań.
        - Loguje sukces lub błędy za pomocą `log_data_analyze`.
    """
    try:
        # summarizer = pipeline(
        #     "summarization",
        #     model="facebook/bart-large-cnn",
        #     tokenizer="facebook/bart-large-cnn",
        # )

        # summary = summarizer(tekst, max_length=130, min_length=30, do_sample=False)
        # log_data_analyze("Notes summary generated successfully.")
        # return summary[0]["summary_text"]

        print(tekst)

        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key="...",
        )

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Podsumuj transkrypcje nagrania wideo którą ci przekaże poniżej ( jeżeli nie będzie tekstu do podsumowania zwróć odpowiedź: \"Brak tekstu do podsumowania\"):",
                },
                {
                    "role": "user",
                    "content": tekst,
                },
            ],
            model="gpt-4o",
            temperature=0.5,
            max_tokens=4096,
            top_p=1,
        )

        return response.choices[0].message.content
    except Exception as e:
        log_data_analyze(f"Error generating notes summary: {e}")
        return "Wystąpił błąd przy generowaniu podsumowania"


# 5. Wydobywanie ramek z wideo do dalszej analizy
def get_video_frames(
    file_path: str, file_name: str, file_extension: str, temp_dir_name: str
) -> int:
    """
    Wydobywanie ramek z pliku wideo do dalszej analizy.

    Args:
        file_path (str): Ścieżka do folderu, w którym znajduje się plik wideo.
        file_name (str): Nazwa pliku wideo.
        file_extension (str): Rozszerzenie pliku wideo.
        temp_dir_name (str): folder w tmp, w którym mają zapisać się zdjęcia

    Returns:
        int: Liczba plików zawierających ramki.

    Notes:
        - Funkcja wykorzystuje FFmpeg do ekstrakcji ramek z wideo.
        - Informacje o sukcesie lub błędach są logowane za pomocą `log_data_analyze`.
    """
    output_dir = f"../tmp/{temp_dir_name}/"
    try:
        os.makedirs(output_dir, exist_ok=True)
        log_data_analyze(f"Directory {output_dir} is ready.")
    except Exception as e:
        log_data_analyze(f"Failed to create directory {output_dir}: {e}")
        return 0

    output_pattern = f"{output_dir}%d.png"
    ffmpeg_command = [
        "ffmpeg",
        "-i",
        f"{file_path}/{file_name}{file_extension}",
        "-vf",
        "fps=1",
        "-frame_pts",
        "1",
        output_pattern,
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)
        log_data_analyze(f"Frames successfully extracted to {output_dir}")
    except subprocess.CalledProcessError as e:
        log_data_analyze(f"FFmpeg execution failed: {e}")
    except FileNotFoundError:
        log_data_analyze(
            "FFmpeg not found. Make sure it is installed and in your PATH."
        )
    except Exception as e:
        log_data_analyze(f"Error generating video frames: {e}")

    return (
        len(os.listdir(f"{output_dir}")) - 4
    )  # odjęcie 4 plików, które zawsze znajdują się w folderze


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
def main(
    temp_dir_name: str = "testowe_pliki",
    filename_audio: str = "../tmp/testowe_pliki/test_wyklad.wav",
    filename_video: str = "../tmp/testowe_pliki/nagranie_testowe_teams.mp4",
    application_name: str = "MSTeams",
    user_dir: str = "../default_sava_folder",
    title: str = "test_main_data_analyze",
    datetime: datetime = datetime(2025, 1, 11, 18, 50, 49, 859943),
    n_frame: int = 5,
    send_to_server: bool = True,
):
    """
    Główna funkcja odpowiedzialna za przetwarzanie danych multimedialnych: audio, wideo oraz generowanie podsumowań.

    Args:
        temp_dir_name (str): Nazwa katalogu tymczasowego na wyniki przetwarzania.
        filename_audio (str): Ścieżka do pliku audio.
        filename_video (str): Ścieżka do pliku wideo.
        application_name (str): Nazwa aplikacji źródłowej (np. "MSTeams", "Zoom").
        user_dir (str): Katalog użytkownika do zapisania wyników. Domyślnie None.
        title (str): Tytuł notatki. Domyślnie None.
        datetime (datetime): Data i czas generacji notatki. Domyślnie None.
        n_frame (int): Określa co która ramka ( z pliku wideo ) ma pozostać w folderze

    Returns:
        None: Wyniki są zapisywane w wyznaczonym katalogu.
    """
    try:
        log_data_analyze("Starting main function.")

        hf_token = "..."
        tekst = ""  # Wykorzystywany podczas generowania podsumowań
        filepath = ""
        number_of_screens = 0

        with ThreadPoolExecutor(max_workers=2) as executor:
            log_data_analyze("Submitting transcription and diarization tasks.")
            future_transcription_segments = executor.submit(
                transcribe_audio, filename_audio
            )
            future_diarization_result = executor.submit(
                diarize_audio, filename_audio, hf_token
            )

            # Pobranie wyników zadań równoległych
            transcription_segments = future_transcription_segments.result()
            diarization_result = future_diarization_result.result()
            log_data_analyze("Transcription and diarization completed.")

        # Połączenie wyników
        combined = combine_transcription_and_diarization(
            transcription_segments, diarization_result
        )
        log_data_analyze("Transcription and diarization successfully combined.")

        try:
            # Parsowanie informacji o plikach wideo
            file_name_match = re.search(r"(.+)/([\w]+)(\.[a-zA-Z0-9]+)", filename_video)
            filepath = file_name_match.group(1)
            filename = file_name_match.group(2)
            fileextension = file_name_match.group(3)
            log_data_analyze(f"Video file parsed: {filename_video}.")

            note_content_text = []
            note_content_speaker = []
            note_content_img = []
            summary = ""

            for entry in combined:
                if (
                    len(note_content_text) == 0
                    or note_content_speaker[-1]["name"] != entry["speaker"]
                ):
                    speaker = {
                        "type": "speaker",
                        "timestamp": math.floor(float(entry["start"])),
                        "name": f"{entry['speaker']}",
                    }
                    note_content_speaker.append(speaker)

                text = {
                    "type": "text",
                    "timestamp": math.floor(float(entry["start"])),
                    "value": f"{entry['text']}",
                }
                note_content_text.append(text)

                tekst += (
                    f"[{entry['start']:.2f}s - {entry['end']:.2f}s] "
                    f"{entry['speaker']}: {entry['text']}\n"
                )

            log_data_analyze("Notes content successfully created.")

            # Generowanie podsumowania notatek
            summary = notes_summary(tekst)
            log_data_analyze("Summary generated.")

            # Analiza ramek wideo
            number_of_screens = get_video_frames(
                filepath, filename, fileextension, temp_dir_name
            )
            screen_data = image_analyzer.main(
                number_of_screens, f"../tmp/{temp_dir_name}", application_name, n_frame
            )
            log_data_analyze(f"Extracted {number_of_screens} screens for analysis.")

            for entry in screen_data:
                img_info = {
                    "type": "img",
                    "timestamp": int(entry.split(".")[0]),
                    "file_path": f"../tmp/{temp_dir_name}/{entry}",
                }
                note_content_img.append(img_info)

            log_data_analyze("Screen data processed successfully.")

        except Exception as e:
            log_data_analyze(f"Error processing video and generating notes: {e}")

        # Zapis wyników
        sf.save_files(
            title,
            note_summary=summary,
            note_datetime=datetime,
            note_content_img=note_content_img,
            note_content_text=note_content_text,
            note_content_speaker=note_content_speaker,
            video_file_path=filename_video,
            tmp_dir_name=temp_dir_name,
            directory_path=user_dir,
            send_to_server=send_to_server,
        )
        log_data_analyze("Files saved successfully. \n")

    except Exception as e:
        log_data_analyze(f"An error occurred in the main function: {e} \n")


if __name__ == "__main__":
    main()
