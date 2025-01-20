import os
import cv2
import numpy as np
from app_backend.logging_f import log_data_analyze


def template_analyze(template: str, img2_path: str, i: int) -> bool:
    """
        Analyzes the similarity of the grayscale histograms of two images to see if the image contains a specific slide or other information.

        Args:
        template (str): Path to the template image against which other images are compared.
        img2_path (str): Path to the second image to be compared to the template.
        i (int): Image number, used for debugging or further analysis.

        Returns:
        bool: True if the images are different (i.e. the image contains a slide or information), False otherwise.
    """
    try:
        img1 = cv2.imread(template, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)

        # Oblicz histogramy
        hist1 = cv2.calcHist([img1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([img2], [0], None, [256], [0, 256])

        # Normalizacja histogramów
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()

        # Porównaj histogramy za pomocą współczynnika korelacji
        similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

        return similarity < 0.51
    except Exception as e:
        log_data_analyze(f"[ERROR] template_analyze failed for image {i}: {e}")
        return False


def preprocess_image(image):
    """
        Processes an image, preparing it for analysis using OCR.

        The process includes:
        - Converting the image to grayscale.
        - Removing noise using denoising.
        - Binarizing the image (converting it to black and white).

        Args:
        image (np.ndarray): The input image in NumPy array format.

        Returns:
        np.ndarray: The processed binary image.
    """
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
        _, binary = cv2.threshold(denoised, 150, 255, cv2.THRESH_BINARY)
        return binary
    except Exception as e:
        log_data_analyze(f"[ERROR] preprocess_image failed: {e}")
        return None


def screen_change_analyze(
    img_nr_1: int, img_nr_2: int, folder_path: str, threshold: float = 0.70
) -> bool:
    """
       Analyzes the changes between two images by comparing their text and appearance.

        Uses Mean Squared Error (MSE) as a measure of the difference between the images.

        Args:
        img_nr_1 (int): The number of the first image to analyze.
        img_nr_2 (int): The number of the second image to analyze.
        folder_path (str): The path to the folder where the images are located.
        threshold (float): The minimum similarity value to consider the images as similar (default 0.70).

        Returns:
        bool: True if the images are different, False otherwise.
    """
    try:
        image1 = cv2.imread(f"{folder_path}/{img_nr_1}.png")
        image2 = cv2.imread(f"{folder_path}/{img_nr_2}.png")

        img1_processed = preprocess_image(image1)
        img2_processed = preprocess_image(image2)

        def mse(img1, img2):
            h, w = img1.shape
            diff = cv2.subtract(img1, img2)
            err = np.sum(diff**2)
            mse_value = err / float(h * w)
            return mse_value, diff

        error, _ = mse(img1_processed, img2_processed)

        return error > 0.005
    except Exception as e:
        log_data_analyze(
            f"[ERROR] screen_change_analyze failed for images {img_nr_1} and {img_nr_2}: {e}"
        )
        return False


def main(
    video_length: int, folder_path: str, application_name: str, n_frame: int
) -> list[str]:
    """
       Main function that analyzes changes in images extracted from a video.
        Removes images that do not contain relevant data or are duplicates.

        Args:
        video_length (int): Number of frames (images) to analyze.
        folder_path (str): Path to the folder with video frames (PNG images).
        application_name (str): Application name, used to read the template.
        n_frame (int): Specifies which frames (from the video file) to leave in the folder.

        Returns:
        list[str]: List of filenames containing relevant data.
    """
    final_data = []
    screen_with_data = []

    try:
        # Analiza obecności danych na obrazach za pomocą szablonu
        for i in range(video_length):
            log_data_analyze(f"[INFO] Processing frame {i}")
            if i % n_frame == 0 or i == video_length - 1:
                if template_analyze(
                    f"../data_analyze/templates/{application_name}_no_screen_template.png",
                    f"{folder_path}/{i}.png",
                    i,
                ):
                    screen_with_data.append(f"{i}.png")

        # Zawsze dodaj pierwszą klatkę, jeśli zawiera dane
        if "0.png" in screen_with_data:
            final_data.append("0.png")

        # Analiza zmian między kolejnymi obrazami
        for i in range(1, len(screen_with_data)):
            if screen_change_analyze(
                int(screen_with_data[i - 1].split(".")[0]),
                int(screen_with_data[i].split(".")[0]),
                folder_path,
            ):
                final_data.append(f"{int(screen_with_data[i].split(".")[0])}.png")

        # Usuwanie niepotrzebnych obrazów z folderu
        for filename in os.listdir(folder_path):
            if filename.endswith(".png") and filename not in final_data:
                file_path = os.path.join(folder_path, filename)
                try:
                    os.remove(file_path)
                except Exception as e:
                    log_data_analyze(f"[ERROR] Failed to remove file {filename}: {e}")

        return final_data

    except Exception as e:
        log_data_analyze(f"[ERROR] Main function failed: {e}")
        return []


if __name__ == "__main__":
    # Przykład wywołania funkcji głównej
    main(23, "./tmp/testowe_pliki", "MSTeams", 5)
