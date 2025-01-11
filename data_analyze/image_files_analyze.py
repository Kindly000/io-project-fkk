import os
import subprocess
import pytesseract
import numpy as np
import cv2
from matplotlib import pyplot as plt
from difflib import SequenceMatcher

def template_analyze(template: str, img2_path: str, i: int) -> bool:
    """
    Oblicza podobieństwo histogramów dwóch obrazów.

    Args:
        img1_path (str): Ścieżka do pierwszego obrazu.
        img2_path (str): Ścieżka do drugiego obrazu.

    Returns:
        bool: Czy dana ramka z nagrania wideo zawiera slajd lub inne informacje
    """
    img1 = cv2.imread(template, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)

    # Oblicz histogramy
    hist1 = cv2.calcHist([img1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([img2], [0], None, [256], [0, 256])

    # Normalizacja histogramów
    hist1 = cv2.normalize(hist1, hist1).flatten()
    hist2 = cv2.normalize(hist2, hist2).flatten()

    # Porównaj histogramy (np. korelacja, chi-kwadrat, itp.)
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    if similarity < 0.51:
        return True
        # return f"Obraz nr {i} zawiera slajd prezentacji -> {similarity}"
    else:
        return False
        # return f"Obraz nr {i} nie zawiera slajdu prezentacji -> {similarity}"


def preprocess_image(image):
    """
    Funkcja do przetwarzania obrazu przed przetworzeniem go przez Tesseract OCR:
    - Przekształcanie obrazu na odcienie szarości.
    - Zastosowanie binarizacji (thresholding).
    - Wygładzanie obrazu (denoising).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)

    _, binary = cv2.threshold(denoised, 150, 255, cv2.THRESH_BINARY)

    return binary


def screen_change_analyze(
    img_nr_1: int = None, img_nr_2: int = None, threshold: float = 0.70
):
    """
    Analizuje dwa obrazy pod kątem dopasowania tekstu za pomocą Tesseract OCR
    i określa, czy nastąpiła zmiana obrazu na podstawie zadanego progu podobieństwa tekstu.

    Args:
        img_nr_1 (int): Numer pierwszego obrazu.
        img_nr_2 (int): Numer drugiego obrazu.
        threshold (float): Minimalna wartość podobieństwa tekstu (od 0 do 1), aby uznać obrazy za podobne.

    Returns:
        bool: True, jeśli nastąpiła zmiana obrazu, False w przeciwnym razie.
    """
    image1 = cv2.imread(f"./testowe_pliki/film_testowy_ze_zmiana_2/{img_nr_1}.png")
    image2 = cv2.imread(f"./testowe_pliki/film_testowy_ze_zmiana_2/{img_nr_2}.png")

    img1_processed = preprocess_image(image1)
    img2_processed = preprocess_image(image2)

    def mse(img1, img2):
        h, w = img1.shape
        diff = cv2.subtract(img1, img2)
        err = np.sum(diff**2)
        mse_value = err / float(h * w)
        return mse_value, diff

    error, diff = mse(img1_processed, img2_processed)

    # print(f"Image matching Error (MSE) between the two images {img_nr_1} -> {img_nr_2}:", error)

    if error > 0.005:
        print(
            f"Image matching Error (MSE) between the two images {img_nr_1} -> {img_nr_2}:",
            error,
        )
        print("Obrazy są różne.")
    else:
        print("Obrazy są podobne.")

    # cv2.imshow("Difference", diff)
    # cv2.waitKey(0)
    cv2.destroyAllWindows()

def main():
    final_data = []
    screen_with_data = []
    for i in range(0, 49):
        if template_analyze(
            "./data_analyze/templates/teams_no_screen_template.png",
            f"./testowe_pliki/film_testowy_ze_zmiana_2/{i}.png",
            i,
        ):
            screen_with_data.append(f"{i}.png") 

    if "0.png" in screen_with_data:
        final_data.append("0.png")

    for img_name in screen_with_data:
        img_number = int(img_name.split(".")[0])
        if screen_change_analyze(
            f"{i}",
            f"{i+1}",
        ):
            final_data.append(f"{i+1}.png")

    # print(final_data)

main()
