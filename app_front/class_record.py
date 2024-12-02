import cv2
import numpy as np
from PIL import ImageGrab
from screeninfo import get_monitors
import datetime
import os

#https://www.youtube.com/watch?v=fEdbtmrpFGw

class ScreenRecorder:
    def __init__(self):
        # Detect the primary monitor's dimensions
        for m in get_monitors():
            self.x = m.x
            self.y = m.y
            self.width = m.width
            self.height = m.height

        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"recording_{current_time}.avi"

        # Set up video writer with the specified codec
        self.fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        self.captured_video = cv2.VideoWriter(file_name, self.fourcc, 10.0, (self.width, self.height))
        self.record_status = False

    def _screen_record(self):
        while self.record_status:
            # Grab the screen image and convert to numpy array
            img = ImageGrab.grab(bbox=(self.x, self.y, self.width, self.height))
            np_img = np.array(img)

            # Convert the image color space from BGR to RGB (for correct display)
            cvt_img = cv2.cvtColor(np_img, cv2.COLOR_BGR2RGB)

            # Write the image frame to the video file
            self.captured_video.write(cvt_img)
            print("recording...")

            # Optional: Show the video feed (this is commented out)
            # cv2.imshow('Screen Recording', cvt_img)

            # Wait for a small moment (this could be adjusted for performance)
            cv2.waitKey(1)

        # Close the window and release resources when done
        cv2.destroyAllWindows()

    def start_record(self):
        """Start the screen recording."""
        if not self.record_status:
            self.record_status = True
            self._screen_record()

    def stop_record(self):
        """Stop the screen recording."""
        if self.record_status:
            self.record_status = False

    def __del__(self):
        """Ensure proper cleanup when the object is destroyed."""
        if self.record_status:
            self.stop_record()
        self.captured_video.release()


# Example usage
if __name__ == "__main__":
    recorder = ScreenRecorder()
    # recorder.start_record()  # Start recording
    # To stop recording, call:
    # recorder.stop_record()
