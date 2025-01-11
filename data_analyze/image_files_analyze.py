import os
import cv2
import numpy as np


def template_analyze(template: str, img2_path: str, i: int) -> bool:
    """
    Analizuje podobieństwo histogramów dwóch obrazów w odcieniach szarości, aby sprawdzić,
    czy dany obraz zawiera określony slajd lub inne informacje.

    Args:
        template (str): Ścieżka do obrazu szablonu (template), z którym porównywane są inne obrazy.
        img2_path (str): Ścieżka do drugiego obrazu, który ma być porównany z szablonem.
        i (int): Numer obrazu, używany do debugowania lub dalszej analizy.

    Returns:
        bool: True, jeśli obrazy są różne (tj. obraz zawiera slajd lub informacje), False w przeciwnym razie.
    """
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


def preprocess_image(image):
    """
    Przetwarza obraz, przygotowując go do analizy za pomocą OCR.
    Proces obejmuje:
    - Konwersję obrazu na odcienie szarości.
    - Usunięcie szumu za pomocą techniki denoising.
    - Binarizację obrazu (przekształcenie w obraz czarno-biały).

    Args:
        image (np.ndarray): Obraz wejściowy w formacie NumPy array.

    Returns:
        np.ndarray: Przetworzony obraz binarny.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
    _, binary = cv2.threshold(denoised, 150, 255, cv2.THRESH_BINARY)
    return binary


def screen_change_analyze(
    img_nr_1: int, img_nr_2: int, folder_path: str, threshold: float = 0.70
) -> bool:
    """
    Analizuje zmiany pomiędzy dwoma obrazami poprzez porównanie ich tekstu i wyglądu.
    Wykorzystuje Mean Squared Error (MSE) jako miarę różnicy między obrazami.

    Args:
        img_nr_1 (int): Numer pierwszego obrazu do analizy.
        img_nr_2 (int): Numer drugiego obrazu do analizy.
        folder_path (str): Ścieżka do folderu, w którym znajdują się obrazy.
        threshold (float): Minimalna wartość podobieństwa, aby uznać obrazy za podobne (domyślnie 0.70).

    Returns:
        bool: True, jeśli obrazy są różne, False w przeciwnym razie.
    """
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


def main(video_length: int, folder_path: str, application_name: str) -> list[str]:
    """
    Główna funkcja analizująca zmiany w obrazach wyodrębnionych z wideo.
    Usuwa obrazy, które nie zawierają istotnych danych lub są zduplikowane.

    Args:
        video_length (int): Liczba klatek (obrazów) do analizy.
        folder_path (str): Ścieżka do folderu z klatkami wideo (obrazy w formacie PNG).
        application_name (str): Nazwa aplikacji, używana do odczytu szablonu.

    Returns:
        list[str]: Lista nazw plików zawierających istotne dane.
    """
    final_data = []
    screen_with_data = []

    # Analiza obecności danych na obrazach za pomocą szablonu
    for i in range(video_length):
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
    for img_name in screen_with_data[1:]:
        img_number = int(img_name.split(".")[0])
        if screen_change_analyze(img_number - 1, img_number, folder_path):
            final_data.append(f"{img_number}.png")

    # Usuwanie niepotrzebnych obrazów z folderu
    for filename in os.listdir(folder_path):
        if filename.endswith(".png") and filename not in final_data:
            file_path = os.path.join(folder_path, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Nie udało się usunąć {filename}: {e}")

    return final_data


if __name__ == "__main__":
    # Przykład wywołania funkcji głównej
    main(22, "./tmp/testowe_pliki", "MSTeams")
