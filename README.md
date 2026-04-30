# Budżet Domowy (budget-app) 💰

Zaawansowany menedżer budżetu domowego z modułami do analizy wydatków, generowania raportów oraz zarządzania listami zakupów.

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

## 🐧 Instalacja (Arch Linux i pochodne)

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

## 🚀 Uruchamianie

Po instalacji aplikację możesz uruchomić:
```bash
budget-app
```

Lub znaleźć ją w menu aplikacji jako Budżet Domowy.

## 🗑️ Odinstalowanie

Jeśli instalacja odbyła się przez pacmana:

```bash
sudo pacman -Rs budget-app
```

## Dostępne również na Windows i MacOS

### Pobierz najnowszą wersję:

- [Pobierz dla Windows (Instalator)](https://github.com/KlapkiSzatana/budget-app/releases/latest/download/BudgetApp_Setup.exe)
- [Pobierz dla macOS](https://github.com/KlapkiSzatana/budget-app/releases/latest/download/BudgetApp_macos)

## 📝 Licencja
Projekt udostępniany na licencji GPL-3.0.

Autor: KlapkiSzatana


