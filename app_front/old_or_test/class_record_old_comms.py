import cv2
import numpy as np
from PIL import ImageGrab
import datetime
from threading import Thread


class ScreenRecorder:
    def __init__(self, directory):
        # Zmienne ekranu
        self.width, self.height = ImageGrab.grab().size  # Pobiera wymiary ekranu

        # Nazwa pliku wideo
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"../tmp/{directory}/video_output.avi"

        # Inicjalizacja VideoWriter
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.captured_video = cv2.VideoWriter(
            file_name, self.fourcc, 10.0, (self.width, self.height)
        )
        self.record_status = False

    def _screen_record(self):
        """Wątek odpowiedzialny za nagrywanie wideo."""
        while self.record_status:
            # Pobranie klatki ekranu
            img = ImageGrab.grab(bbox=(0, 0, self.width, self.height))
            np_img = np.array(img)
            cvt_img = cv2.cvtColor(np_img, cv2.COLOR_BGR2RGB)  # Konwersja kolorów

            # Zapis klatki do pliku wideo
            self.captured_video.write(cvt_img)
            cv2.waitKey(1)  # Krótka pauza dla stabilności

    def start_record(self):
        """Uruchom nagrywanie w osobnym wątku."""
        if not self.record_status:
            self.record_status = True
            self.thread = Thread(target=self._screen_record)
            self.thread.start()

    def stop_record(self):
        """Zatrzymaj nagrywanie i zwolnij zasoby."""
        if self.record_status:
            self.record_status = False
            self.thread.join()  # Poczekaj na zakończenie wątku
            self.captured_video.release()  # Zakończ zapis wideo
            print("Recording stopped and file is released.")

    def __del__(self):
        """Zwalnia zasoby podczas niszczenia obiektu."""
        if self.record_status:
            self.stop_record()
        self.captured_video.release()
