import cv2  # Library for image and video processing
import numpy as np  # Library for numerical computations
from PIL import ImageGrab  # Module for screen capture
import datetime  # Module for handling date and time
from threading import Thread  # Module for threading
import app_backend.logging_f as logg # Logging file


class ScreenRecorder:
    def __init__(self, directory):
        """
        Constructor for the ScreenRecorder class.

        Args:
            directory (str): The name of the directory where the video file will be saved.

        Variables:
            self.width, self.height: The dimensions of the screen obtained via ImageGrab.
            file_name: The path where the video file will be saved (in AVI format).
            self.fourcc: A four-character code for video compression (XVID).
            self.captured_video: The VideoWriter object used for saving video frames.
            self.record_status: A flag indicating whether recording is in progress.
        """
        # Get the screen dimensions
        self.width, self.height = ImageGrab.grab().size

        # Generate a unique video file name based on the current date and time
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"../tmp/{directory}/video_output.avi"  # Video file path

        # Initialize VideoWriter with XVID codec, 10 fps, and screen dimensions
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.captured_video = cv2.VideoWriter(
            file_name, self.fourcc, 10.0, (self.width, self.height)
        )
        self.record_status = False  # Flag to track if recording is in progress

    def _screen_record(self):
        """
        Thread function responsible for recording the screen.

        This function continuously captures the screen and saves frames to the video file.
        """
        while self.record_status:
            # Capture a screenshot of the entire screen
            img = ImageGrab.grab(bbox=(0, 0, self.width, self.height))
            np_img = np.array(img)  # Convert the image to a NumPy array
            cvt_img = cv2.cvtColor(np_img, cv2.COLOR_BGR2RGB)  # Convert from BGR to RGB

            # Write the frame to the video file
            self.captured_video.write(cvt_img)
            cv2.waitKey(1)  # Short pause to ensure smooth frame capture

    def start_record(self):
        """
        Starts recording in a separate thread.

        If recording is not already active, this method will initiate the process.
        """
        if not self.record_status:
            self.record_status = True  # Set the recording status to active
            self.thread = Thread(target=self._screen_record)  # Create a new thread for screen recording
            self.thread.start()  # Start the thread

    def stop_record(self):
        """
        Stops the recording and releases the resources.

        This method sets the recording status to False, waits for the recording thread to finish,
        and releases the video file.
        """
        if self.record_status:
            self.record_status = False  # Stop the recording
            self.thread.join()  # Wait for the recording thread to finish
            self.captured_video.release()  # Release the video file resources
            logg.app_logs(f"[SUCCESS] Recording stopped and file is released.")


    def __del__(self):
        """
        Destructor to clean up resources when the object is destroyed.

        If the recording is still ongoing, it stops the recording and releases the video resources.
        """
        if self.record_status:
            self.stop_record()  # Ensure the recording is stopped
        self.captured_video.release()  # Release the video writer resources
