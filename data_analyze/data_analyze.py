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
from app_backend.logging_f import log_data_analyze, app_logs
from app_front.notification_window import create_notification_window
import app_backend.save_files as sf
import data_analyze.image_files_analyze as image_analyzer
from datetime import datetime

model_size = "small"
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# 1. Transkrypcja pliku audio za pomocą Whisper
def transcribe_audio(file_path: str) -> list[dict]:
    """
        Transcribes an audio file to text.

        Args:
        file_path (str): Path to the audio file.

        Returns:
        list[dict]: List of transcription segments including start time, end time, and text.

        Notes:
        - This function uses the Whisper model.
        - If an error occurs, the information is logged to a file using `log_data_analyze`.
    """
    try:
        app_logs("[INFO] Audio transcription started.")

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
        app_logs("[SUCCESS] Audio transcription completed successfully.")
        return result_segments
    except Exception as e:
        log_data_analyze(f"Transcription Error for {file_path}: {e}")
        return []


# 2. Rozpoznawanie rozmówców audio za pomocą pyannote.audio
def diarize_audio(file_path: str, hf_token: str) -> object:
    """
        Audio diarization - recognizes interlocutors in an audio file.

        Args:
        file_path (str): Path to the audio file.
        hf_token (str): Token for authentication in HuggingFace.

        Returns:
        object: The diarization result containing information about interlocutors.

        Notes:
        - The function uses the pyannote model for diarization.
        - In case of an error, the information is logged to a file using `log_data_analyze`.
    """
    try:
        app_logs("[INFO] Audio diarization started.")

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", use_auth_token=hf_token
        )
        diarization = pipeline(file_path)
        log_data_analyze(f"Diarization completed successfully for {file_path}.")
        app_logs("[SUCCESS] Audio diarization completed successfully.")
        return diarization
    except Exception as e:
        log_data_analyze(f"Diarization Error for {file_path}: {e}")
        return None


# 3. Łączenie transkrypcji i diarizacji
def combine_transcription_and_diarization(
    segments: list[dict], diarization: object
) -> list[dict]:
    """
        Merging transcription and diarization results.

        Args:

        segments (list[dict]): List of transcription segments.

        diarization (object): Results of speaker diarization.

        Returns:
        list[dict]: List of merged results containing time and speaker information.

        Notes:
        - The function merges data based on overlapping time intervals.
        - Success or failure information is logged to a file.
    """
    try:
        app_logs("[INFO] Transcription and diarization merging has begun.")

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
        app_logs("[SUCCESS] Transcription and diarization merge completed successfully")
        return combined_results
    except Exception as e:
        log_data_analyze(f"Error combining transcription and diarization: {e}")
        return []


# 4. Generowanie podsumowań notatek
def notes_summary(tekst: str) -> str:
    """
        Generating notes summaries.

        Args:
        text (str): Text to summarize.

        Returns:
        str: A summary of the text.

        Notes:
        - This function uses the CHatGPT-4o API to generate summaries.
        - Logs success or errors using `log_data_analyze`.
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

        # print(tekst)
        app_logs("[INFO] Note summaries have started generating.")

        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key="...",
        )

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": 'Podsumuj transkrypcje nagrania wideo którą ci przekaże poniżej ( jeżeli nie będzie tekstu do podsumowania zwróć odpowiedź: "Brak tekstu do podsumowania"):',
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

        app_logs("[SUCCESS] Note summary generation completed successfully.")
        return response.choices[0].message.content
    except Exception as e:
        log_data_analyze(f"Error generating notes summary: {e}")
        return "Wystąpił błąd przy generowaniu podsumowania"


# 5. Wydobywanie ramek z wideo do dalszej analizy
def get_video_frames(
    file_path: str, file_name: str, file_extension: str, temp_dir_name: str
) -> int:
    """
        Extract frames from a video file for further analysis.

        Args:
        file_path (str): Path to the folder where the video file is located.
        file_name (str): Name of the video file.
        file_extension (str): Extension of the video file.
        temp_dir_name (str): Folder in tmp where the images should be saved

        Returns:
        int: Number of files containing frames.

        Notes:
        - This function uses FFmpeg to extract frames from the video.
        - Information about success or failure is logged using `log_data_analyze`.
    """
    app_logs("[INFO] Started generating frames from video file.")
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
        app_logs("[SUCCESS] Successfully generated frames from video file.")
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
        Main function responsible for processing multimedia data: audio, video and generating summaries.

        Args:
        temp_dir_name (str): Temporary directory name for processing results.
        filename_audio (str): Path to audio file.
        filename_video (str): Path to video file.
        application_name (str): Source application name (e.g. "MSTeams", "Zoom").
        user_dir (str): User directory to save results. Default is None.
        title (str): Note title. Default is None.
        datetime (datetime): Date and time of note generation. Default is None.
        n_frame (int): Specifies every frame (from video file) to remain in the folder.

        Returns:
        None: Results are saved in the designated directory.
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

        info_message = "Processing finished.\n"
        # Zapis wyników
        info_message += sf.save_files(
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
        create_notification_window(info_message)
        log_data_analyze("Files saved successfully. \n")

    except Exception as e:
        log_data_analyze(f"An error occurred in the main function: {e} \n")


if __name__ == "__main__":
    main()
