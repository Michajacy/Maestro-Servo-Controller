# Dokumentacja Techniczna - Sterownik Serwonapędów Maestro

## 1. Wprowadzenie i Cel Projektu
Projekt to profesjonalna aplikacja desktopowa stworzona w języku Python, przeznaczona do sterowania i konfiguracji serwonapędów z użyciem kontrolera Pololu Maestro. Została zaprojektowana zgodnie z dobrymi praktykami inżynierii oprogramowania (Clean Code, PEP8, Separation of Concerns) na potrzeby procesu rekrutacyjnego dla firmy EG EXTENSA.

Aplikacja umożliwia:
- Dynamiczne dodawanie, usuwanie i edycję konfiguracji maksymalnie do 24 kanałów serwonapędów.
- Konfigurację parametrów dla każdego serwa z osobna (Nazwa, Jog Step, Limity Min/Max).
- Precyzyjne sterowanie za pomocą interaktywnych okienek suwakowych z automatycznym przeliczaniem pozycji na kwadratemilisekundy (quarter-microseconds) zgodnie z protokołem Pololu Maestro.
- Trwałość danych realizowaną poprzez lokalną bazę konfiguracyjną w formacie JSON (`servos_config.json`).
- Bezpieczne testowanie interfejsu bez podłączonego sprzętu dzięki architekturze opartej na wzorcu **Mock (Zaślepka)**.

---

## 2. Architektura Systemu (Separacja Warstw)
Aplikacja została podzielona na trzy niezależne warstwy w celu zapewnienia wysokiej skalowalności, łatwości testowania oraz elastyczności:

### A. Warstwa Sprzętowa (`hardware.py`)
- **Interfejs bazowy (`MaestroInterface`)**: Definiuje jednolity kontrakt dla wszystkich kontrolerów (metody `set_target` oraz `close`).
- **Implementacja Rzeczywista (`SerialMaestroController`)**: Odpowiada za fizyczną komunikację przez port szeregowy COM z wykorzystaniem biblioteki `pyserial`. Formatuje polecenia według standardu *Compact Protocol* (ramka 4-bajtowa: komenda `0x84`, kanał, młodsze i starsze bity pozycji).
- **Implementacja Wirtualna (`MockMaestroController`)**: Zaślepka programistyczna logująca operacje do standardowego wyjścia (konsoli) w formacie szesnastkowym (Hex), co umożliwia weryfikację poprawności ramek bez fizycznego sprzętu.

### B. Warstwa Domenowa (`domain.py`)
- **Model `Servo`**: Reprezentuje stan i konfigurację pojedynczego serwonapędu (kanał, nazwa, aktualna pozycja, krok, limity).
- **Menedżer `ServoManager`**: Zarządza alokacją wolnych kanałów, obsługą stanu kolekcji serw oraz trwałością danych (`_save_config` / `_load_config`).

### C. Warstwa Widoku / Interfejs Użytkownika (`maestro_app.py`)
- **`MainWindow`**: Okno główne pełniące funkcję menedżera właściwości (Property Manager). Obsługuje listę przewijalną (Canvas + Scrollbar) aktywnych serw, dodawanie, edycję szablonów oraz podświetlanie wybranego elementu.
- **`ServoWindow`**: Niezależne, podrzędne okienka (`tk.Toplevel`) dla każdego serwa. Odpowiadają za płynną regulację pozycji suwakiem oraz przyciskami krokowymi (`<-`, `->`), zachowując cykl życia polegający na ukrywaniu (`withdraw`) zamiast niszczenia obiektu przy zamykaniu systemowym.

---

## 3. Instrukcja Uruchomienia i Kompilacji

### Wymagania wstępne:
- Python w wersji 3.10 lub nowszej.

### 1. Uruchomienie ze źródła:
```bash
# Sklonuj/otwórz folder projektu i aktywuj środowisko wirtualne
python -m venv venv
# Windows:
.\venv\Scripts\activate

# Zainstaluj wymagane zależności
pip install -r requirements.txt

# Uruchom aplikację
python maestro_app.py
```

### 2. Generowanie samodzielnego pliku `.exe`:
```bash
# W aktywnym środowisku wirtualnym wykonaj:
pyinstaller --onefile maestro_app.py
```
Plik wykonywalny zostanie wygenerowany w katalogu `dist/maestro_app.exe`. Konsola systemowa pozostaje widoczna celowo, aby umożliwić monitorowanie przechwytywanych ramek sprzętowych.

---

## 4. Standardy Jakości i Analiza Statyczna
Kod projektu został w pełni dostosowany do rygorystycznych reguł analizatora **Pylint** oraz **Pylance**:
- Posiada pełne odeklarowanie typów (`type hints`).
- Zawiera kompletne dokumentacje modułów i metod (`docstrings`).
- Przestrzega konwencji PEP8 (stałe konfiguracyjne zdefiniowane wielkimi literami na górze modułów, pełna eksternalizacja tekstów UI).