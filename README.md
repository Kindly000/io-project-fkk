# Wymagania
* Automatyczna transkrypcja mowy na tekst: Angielski/Polski ( mogą występować pewne błędy - klient powinien o tym wiedzieć )  
Co w przypadku natłoku rozmowy ? - brak pełnej identyfikacji rozmówcy. Identyfikujemy ile się da
* Zapis udostępnionego ekranu oraz wykonywania zrzutów ekranu
* Działanie na różnych narzędziach do telekonferencji: Zoom, Google Meet, MS Teams ( ogranczenie do przeglądarki )
* Zapis w formacie DOCS, TXT  
* UI  
  * Mechanizm Start/Stop
  * Przeglądanie danych ( Wideo, Notatki, ETC )
  * Ustawienia: Max Miejsce - maksymalna ilość miejsca jaką aplikacja może zajmować na dysku ( ze wszystkimi plikami spotkań ), Jakość Nagrań, Język Spotkania
  
* Integracja z kalendarzem - rozwiązanie z podstronami WWW do przeglądania spotkań z konkretnych dni
* Generowanie podsumowania notatek -> kilka zdań
* Wyszukiwanie w notatkach - wyświetlanie wszystkich plików, które zawierają dane słowa kluczowe
* Identyfikacja mówcy w notatkach - opcjonalnie

# Uruchamianie programu
Należy pobrać ffmpeg.exe (ze strony https://www.ffmpeg.org/download.html) i zainstalować globalnie (tak jak jest pokazane tutaj: https://www.youtube.com/watch?v=JR36oH35Fgg)
Należy kliknąć PPM na ikonę głośnika -> Dźwięki -> przejść do zakładki Nagrywanie -> włączyć Miks Stereo (ang. Mix Stereo) i ustawić na domyślne

Z poziomu głównego folderu wykonać komendy: 
pip install requirements.txt
python -m app_front.main_app

