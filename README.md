# Notes Generator for Teleconference meetings
Notes Generator jest to aplikacja, której celem jest umożliwienie użytkownikowi nagrywanie interesujących go spotkań, analizowanie ich oraz ostatecznie generowanie z nich notatek. Aplikacja posiada integrację z Google Calendar oraz posiada dedykowaną stronę internetową, na której przechowywane będą notatki.

### Struktura aplikacji


- **/app_backend/**
  - `communication_with_www_server.py`: Zawiera funkcje odpowiedzialne za interakcję z serwerem w celu pobierania i przesyłania danych dotyczących notatek. 
  - `create_files.py`: Zawiera w sobie funkcjonalności umożliwiające tworzenie plików zawierające wyniki analizy nagrań.
  - `find_notes.py`: Służy do przeszukiwania notatek w poszukiwaniu danego ciągu znaków.
  - `logging_f.py`: Zawiera w sobie funkcje obsługujące logowanie zdarzeń w obrębie całej aplikacji.
  - `retry_logic.py`: Zarządza procesem ponownego przesyłania plików w przypadku wystąpienia jakiegoś błędu.
  - `save_files.py`: Zarządza zapisem plików na lokalnej maszynie jak i na dedykowanej stronie internetowej.

- **/app_front/**
  - `class_audio.py`: Zawiera funkcje odpowiedzialne za nagrywanie dźwięku przy użyciu urządzenia *Stereo Mix*. 
  - `class_record.py`: Zawiera funkcje za nagrywanie ekranu użytkownika. 
  - `main.py`: Jest to główny plik uruchomieniowy aplikacji.
  - `notification_window.py`: Zawiera funkcje odpowiedzialne za tworzenie okna z komunikatami.
  - `quickstart.py`: Zawiera funkcje odpowiedzialne za komunikacje z API Google Calendar.
  - `token.json`: Jest to token tworzony podczas logowania przez użytkownika do swojego konta Google. Umożliwia on uwierzytelnianie i autoryzację z API Google Calendar.

- **/data_analyze/**
  - `data_analyze.py`: Zawiera funkcje odpowiedzialne za wykonywanie transkrypcji, diaryzacji oraz podsumowań na podstawie przekazanych do niej plików audio (.wav) oraz wideo (.mp4). 
  - `image_files_analyze.py`: Zawiera funkcje odpowiedzialne za analize ramek z pliku wideo, wykrywanie zmian treści na ekranie oraz wykrywania prezentowanych multimediów podczas telekonferencji. 

- **/default_save_folder/**
  - W tym folderze zapisywane są docelowo wyniki analizy plików z nagranych spotkań, jeżeli nie została wskazana przez użytkownika inna lokalizacja zapisu.

- **/docs/**
  - `Dokumentacja_wymagan.docx`: Tak jak wskazuje nazwa pliku
  - `json_file_doc.json`: Plik przedstawiający schemat JSON wykorzystywany do komunikacji z API Google Calendar 

- **/error_logs/**
  - `communication_with_www_server.log`: Wyświetla wszystkie błędy, do których doszło podczas komunikacji aplikacji z serwerem WWW, na którym zapisywane są pliki. 
  - `data_analyze.log`: Wyświetla wszystkie błędy, do których doszło podczas dokonywania analizy plików audio oraz wideo. 
  - `operations_on_file.log`: Wyświetla wszystkie błędy, do których doszło podczas wykonywania operacji na plikach.

- **/secrets/**
  - `secrets.json`: Plik, który zapewnia możliwość korzystania z API Google Calendar. Wskazuje on, że aplikacja jest przypisana do kalendarza jako projekt.

- **/tmp/**
  - W tym folderze zapisywane są pliki tymczasowe wykorzystywane podczas wykonywania analizy plików wideo oraz audio. Po przesłaniu danych na serwerem lub zapisaniu ich lokalnie, pliki z tego folderu są usuwane.

- **/unsuccessful_uploads/**
  - W tym folderze zapisywane są pliki, których z jakiegoś powodu nie udało się przesłać na serwer WWW.

- **/logs.log**
  - W tym pliku zapisywane są informacje dotyczące działania aplikacji i operacji jakie w obecnej chwili są wykonywane.

- **/requirements.txt**

### Główne rozwiązania wykorzystane w aplikacji
- ***Transkrypcja***: https://github.com/SYSTRAN/faster-whisper
- ***Diaryzacja***: https://huggingface.co/pyannote/speaker-diarization
- ***Podsumowania notatek***: API ChatGPT-4o
- ***Kalendarz***: Google Calendar API
- ***GUI***: Tkinter ( Python )
- ***Web Server***: PHP

### Uruchamianie projektu ( aplikacji )

Instrukcja jak uruchomić projekt lokalnie:

   ```cmd
   git clone https://github.com/Kindly000/io-project-fkk.git
   cd io-projekt-fkk
   python -m venv venv
   \venv\Scripts\activate
   mkdir secrets -> dodać plik credentials.json ( uzyskany od twórców aplikacji )
   pip install -r requirements.txt
   python -m app_front.main
   ```

### Dokumentacja Wymagań - docs\Dokumentacja_wymagan.docx

### Dokumentacja Kodu - docs\Dokumentacja_kodu