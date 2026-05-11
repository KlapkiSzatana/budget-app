## Budżet Domowy (budget-app) 💰
Zaawansowany menedżer budżetu domowego z modułami do analizy wydatków, generowania raportów oraz zarządzania listami zakupów.

### Spis treści
- [Funkcje](#funkcje)
- [Wymagania (Zależności)](#wymagania-zależności)
- [Budowa ze źródeł](#budowa-ze-źródeł)
- [Podpis Cyfrowy](#instancje-bez-podpisu-cyfrowego)
- [Instalacja (Arch Linux i pochodne)](#instalacja-arch-linux-i-pochodne)
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

## Instancje bez podpisu cyfrowego

Gotowe instalatory udostępniane w sekcji **Releases** nie są podpisane komercyjnym certyfikatem deweloperskim (ze względu na wysokie koszty takich certyfikatów). 

Jeśli Twój system (Windows Defender / SmartScreen lub macOS Gatekeeper) zablokuje uruchomienie programu, wybierz opcję zezwalającą na uruchomienie aplikacji (np. "Uruchom mimo to"). Jeśli wolisz uniknąć tych komunikatów, możesz zawsze pobrać kod źródłowy i uruchomić aplikację bezpośrednio przez Pythona: `python budget-app.py`.

## Instalacja (Arch Linux i pochodne)

Aplikacja jest dostępna w AUR w dwóch wersjach.  
Wybierz jedną z poniższych metod:

---

### OPCJA A: Szybka instalacja – Gotowa binarka

Instalujesz gotowy program.  
Nie potrzebujesz Pythona, bibliotek ani kompilacji.

Pobiera się i działa natychmiast.

Jeśli używasz pomocnika AUR (`yay` lub `paru`), wpisz:

```bash
yay -S budget-app-bin
```

lub

```bash
paru -S budget-app-bin
```

---

### OPCJA B: Instalacja ze źródeł

Program buduje się bezpośrednio z kodu źródłowego.

System automatycznie pobierze:
- środowisko Python,
- PySide6,
- Pillow,
- oraz wszystkie wymagane zależności.

Jeśli używasz pomocnika AUR (`yay` lub `paru`), wpisz:

```bash
yay -S budget-app
```

lub

```bash
paru -S budget-app
```

---

### OPCJA C: Ręczna instalacja przez PKGBUILD (Bez pomocników AUR)

Jeśli nie używasz `yay` ani `paru`, możesz pobrać paczkę ręcznie i zbudować ją przez `makepkg`.

### Wersja binarna

```bash
git clone https://aur.archlinux.org/budget-app-bin.git
cd budget-app-bin
makepkg -si
```

### Wersja ze źródła

```bash
git clone https://aur.archlinux.org/budget-app.git
cd budget-app
makepkg -si
```

---

## Uruchamianie

Po instalacji (niezależnie od wybranej opcji) aplikację uruchamiasz wpisując:

```bash
budget-app
```

Możesz także uruchomić ją z menu aplikacji swojego środowiska graficznego.

---

## Odinstalowanie

Aby całkowicie usunąć aplikację z systemu:

### Wersja binarna (`-bin`)

```bash
sudo pacman -Rs budget-app-bin
```

### Wersja ze źródła

```bash
sudo pacman -Rs budget-app
```

---

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

