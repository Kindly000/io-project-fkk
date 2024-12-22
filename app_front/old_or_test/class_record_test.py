import cv2
import numpy as np
from PIL import ImageGrab
from screeninfo import get_monitors
import datetime
import threading

class ScreenRecorder:
    def __init__(self):
        # Detect the primary monitor's dimensions
        for m in get_monitors():
            self.x = m.x
            self.y = m.y
            self.width = m.width
            self.height = m.height

        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.file_name = f"recording_{current_time}.avi"

        # Set up video writer with the specified codec
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.captured_video = cv2.VideoWriter(self.file_name, self.fourcc, 10.0, (self.width, self.height))
        self.record_status = False
        self.recording_thread = None

    def _screen_record(self):
        try:
            while self.record_status:
                # Grab the screen image and convert to numpy array
                img = ImageGrab.grab(bbox=(self.x, self.y, self.width, self.height))
                np_img = np.array(img)

                # Convert the image color space from BGR to RGB (for correct display)
                cvt_img = cv2.cvtColor(np_img, cv2.COLOR_BGR2RGB)
                print("recording...")
                # Write the image frame to the video file
                self.captured_video.write(cvt_img)

                # Add a small delay for performance
                cv2.waitKey(1)
        finally:
            # Ensure resources are released
            self.captured_video.release()
            print(f"Recording saved to {self.file_name}")

    def start_record(self):
        """Start the screen recording."""
        if not self.record_status:
            self.record_status = True
            self.recording_thread = threading.Thread(target=self._screen_record)
            self.recording_thread.start()

    def stop_record(self):
        """Stop the screen recording."""
        if self.record_status:
            self.record_status = False
            if self.recording_thread is not None:
                self.recording_thread.join()  # Ensure thread finishes before proceeding
            if self.captured_video.isOpened():
                self.captured_video.release()  # Ensure final resources are released
            print("Screen recording stopped and file closed.")

    def __del__(self):
        """Ensure proper cleanup when the object is destroyed."""
        self.stop_record()
