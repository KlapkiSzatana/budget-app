## Budżet Domowy (budget-app) 💰
Zaawansowany menedżer budżetu domowego z modułami do analizy wydatków, generowania raportów oraz zarządzania listami zakupów.

### Spis treści
- [Funkcje](#funkcje)
- [Wymagania (Zależności)](#wymagania-zależności)
- [Budowa ze źródeł](#budowa-ze-źródeł)
- [Instalacja (Arch Linux i pochodne)](#instalacja-arch-linux-i-pochodne)
- [Instalacja (Arch z AUR)](#instalacja-arch-z-aur)
- [Uruchamianie](#uruchamianie)
- [Odinstalowanie](#odinstalowanie)
- [Wersja gotowa dla Linux](#dostępna-również-gotowa-wersja-bin-dla-linux)
- [Dostępne również na Windows i MacOS](#dostępne-również-na-windows-i-macos)
- [Licencja](#licencja)

## Funkcje
*   **Zarządzanie wydatkami:** Podział na kategorie i moduły tematyczne.
*   **Raporty:** Wizualizacja danych.
*   **Eksport PDF:** Generowanie zestawień do plików PDF.

## Wymagania (Zależności)

Aby aplikacja działała poprawnie na Arch Linux, wymagane są następujące pakiety:
* `python`
* `pyside6` (GUI)
* `python-matplotlib` (wykresy i statystyki)
* `python-pypdf` (obsługa plików PDF)
* `python-pillow` (przetwarzanie grafiki)

## Budowa ze źródeł

Pełna instrukcja budowy lokalnej wersji developerskiej, binarki Linux oraz paczek `.deb` i `.rpm` znajduje się w [BUILD_FROM_SOURCE.md](BUILD_FROM_SOURCE.md).

## Znane Błędy!
Lista znanych błędów znajduje się w [ZNANE_BŁĘDY.md](ZNANE_BŁĘDY.md).

## Instalacja (Arch Linux i pochodne)

Najprostszym sposobem instalacji jest użycie dołączonego pliku `PKGBUILD`.

### 1. Sklonuj repozytorium i przejdź do katalogu

```bash
git clone https://github.com/KlapkiSzatana/budget-app.git
cd budget-app
```

### 2. Zbuduj i zainstaluj pakiet
```bash
makepkg -si
```

lub

## Instalacja (Arch z AUR)

Aplikację można łatwo zainstalować z repozytorium **AUR (Arch User Repository)**.

### Szybka instalacja (zalecana)

Jeśli używasz pomocnika AUR (np. `yay` lub `paru`), wpisz w terminalu:

```bash
yay -S budget-app
```
lub
```bash
paru -S budget-app
```

## Uruchamianie

Po instalacji aplikację możesz uruchomić:
```bash
budget-app
```

Lub znaleźć ją w menu aplikacji jako Budżet Domowy.

## Odinstalowanie

Jeśli instalacja odbyła się przez pacmana:

```bash
sudo pacman -Rs budget-app
```

## Dostępna również gotowa wersja bin dla Linux

Wersja aplikacji automatycznie kompilowana i publikowana przy użyciu GitHub Actions. Dzięki temu proces budowania pozostaje spójny i w pełni zautomatyzowany.

Poniżej link do pobrania gotowej aplikacji.

### Pobierz najnowszą wersję:

- [Pobierz dla Linux](https://github.com/KlapkiSzatana/budget-app/releases/latest/download/BudgetApp_linux.tar.gz)

## Instalacja i Deinstalacja (Linux)

Paczka zawiera gotowe skrypty, które automatycznie instalują aplikację w katalogu `/opt/BudgetApp` oraz dodają skrót do systemowego menu aplikacji (dzięki czemu program jest dostępny dla wszystkich użytkowników systemu).

### Wymagania
Instalacja i deinstalacja wymagają uprawnień administratora (`sudo`). Skrypty same poproszą o podanie hasła w terminalu.

---

### Instrukcja Instalacji

1. Pobierz i rozpakuj archiwum `BudgetApp_linux.tar.gz`.
2. Otwórz terminal w rozpakowanym katalogu `linux-package` i uruchom skrypt instalacyjny:

```bash
./install.run
```

3. Po zakończeniu instalacji ikona Budżet Domowy pojawi się w Twoim menu aplikacji.

### Instrukcja Deinstalacji

Jeśli chcesz całkowicie usunąć aplikację wraz ze wszystkimi skrótami z systemu:

1. Otwórz terminal w katalogu linux-package.

2. Uruchom skrypt deinstalacyjny:

```bash
./uninstall.run
```

3. (Alternatywnie, możesz usunąć aplikację ręcznie, wpisując w terminalu: 

```bash
sudo rm -rf /opt/BudgetApp /usr/share/applications/BudgetApp.desktop && sudo update-desktop-database /usr/share/applications
```

## Dostępne również na Windows i MacOS

Wersje aplikacji na macOS oraz Windows są automatycznie kompilowane i publikowane przy użyciu GitHub Actions. Dzięki temu proces budowania pozostaje spójny i w pełni zautomatyzowany dla tych platform.

Głównym środowiskiem rozwoju oraz docelową platformą projektu pozostaje jednak **Arch Linux** — to na nim skupia się podstawowy nurt rozwoju i testowania.

### Pobierz najnowszą wersję:

- [Pobierz dla Windows (Instalator)](https://github.com/KlapkiSzatana/budget-app/releases/latest/download/BudgetApp_Setup.exe)
- [Pobierz dla macOS](https://github.com/KlapkiSzatana/budget-app/releases/latest/download/BudgetApp_macos.dmg)

## Licencja
Projekt udostępniany na licencji GPL-3.0.

**Enjoy!**

👤 Autor

KlapkiSzatana

