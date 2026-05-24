# Budowa ze źródeł

Ta instrukcja opisuje trzy scenariusze budowy projektu `budget-app`:

1. uruchomienie aplikacji bezpośrednio ze źródeł,
2. zbudowanie binarki Linux przez `PyInstaller`,
3. spakowanie gotowej binarki do paczek `.deb` i `.rpm`.

Instrukcja jest zgodna z aktualnym układem repozytorium oraz z buildem Windows/macOS zdefiniowanym w `.github/workflows/build.yml`.

## 1. Wymagania

Do pełnej budowy potrzebujesz:

- `git`
- `python` 3.12 lub nowszy
- `python -m venv`
- `pip`
- `ruby` + `rubygems`
- narzędzia systemowe potrzebne przez `PyInstaller` i `fpm`

Przykładowy zestaw zależności systemowych:

- Arch Linux: `sudo pacman -S --needed git python python-pip ruby base-devel`
- Debian/Ubuntu: `sudo apt install git python3 python3-venv python3-pip ruby ruby-dev build-essential`
- Fedora: `sudo dnf install git python3 python3-pip ruby ruby-devel gcc make`

## 2. Pobranie repozytorium

```bash
git clone https://github.com/KlapkiSzatana/budget-app.git
cd budget-app
```

## 3. Uruchomienie bezpośrednio ze źródeł

Utwórz lokalne środowisko i zainstaluj zależności:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install PySide6 matplotlib pypdf pillow reportlab pyinstaller
```

Uruchom aplikację:

```bash
python budget-app.py
```

## 4. Budowa binarki Linux

To buduje katalog `dist/budget-app/` z gotową binarką i zależnościami.

```bash
source .venv/bin/activate
rm -rf build dist budget-app.spec

python -m PyInstaller --noconfirm --clean --onedir --windowed \
  --name budget-app \
  --add-data "locales:locales"
  --add-data "budget.png:." \
  budget-app.py
```

Po zakończeniu możesz uruchomić wynik lokalnie:

```bash
./dist/budget-app/budget-app
```

## 5. Przygotowanie narzędzia `fpm`

Paczki `.deb` i `.rpm` najprościej zbudować z tej samej binarki przez `fpm`.

Instalacja:

```bash
gem install --user-install fpm
```

Jeżeli po instalacji `fpm` nie jest w `PATH`, dodaj katalog gemów użytkownika do ścieżki i otwórz nową sesję terminala.

Szybka kontrola:

```bash
fpm --version
```

## 6. Budowa paczki `.deb`

Najpierw przygotuj strukturę paczki:

```bash
VERSION=$(python - <<'PY'
from pathlib import Path
import re

text = Path("config.py").read_text(encoding="utf-8")
match = re.search(r'^WERSJA = "([^"]+)"', text, re.MULTILINE)
print(match.group(1))
PY
)

rm -rf build/package-root build/packages
mkdir -p build/package-root/usr/lib/budget-app
mkdir -p build/package-root/usr/bin
mkdir -p build/package-root/usr/share/applications
mkdir -p build/package-root/usr/share/pixmaps
mkdir -p build/packages

cp -a dist/budget-app/. build/package-root/usr/lib/budget-app/
install -m 644 budget.png build/package-root/usr/share/pixmaps/budget-app.png

cat > build/package-root/usr/bin/budget-app <<'EOF'
#!/bin/sh
exec /usr/lib/budget-app/budget-app "$@"
EOF
chmod 755 build/package-root/usr/bin/budget-app

cat > build/package-root/usr/share/applications/budget-app.desktop <<'EOF'
[Desktop Entry]
Name=Home Budget
Name[pl]=Budżet Domowy
Comment=Home Budget Management
Comment[pl]=Zarządzanie Budżetem Domowym
Exec=budget-app
Icon=budget-app
Terminal=false
Type=Application
Categories=Office;Finance;
EOF
```

Zbuduj paczkę:

```bash
fpm -s dir -t deb \
  -n budget-app \
  -v "$VERSION" \
  --iteration 1 \
  --architecture native \
  --license "GPL-3.0" \
  --url "https://github.com/KlapkiSzatana/budget-app" \
  --maintainer "KlapkiSzatana" \
  --description "Zarządzanie Budżetem Domowym" \
  --prefix / \
  -C build/package-root \
  -p build/packages \
  .
```

Gotowa paczka pojawi się w katalogu `build/packages/`.

## 7. Budowa paczki `.rpm`

Zakładając, że katalog `build/package-root/` nadal istnieje po poprzednim kroku:

```bash
fpm -s dir -t rpm \
  -n budget-app \
  -v "$VERSION" \
  --iteration 1 \
  --architecture native \
  --license "GPL-3.0" \
  --url "https://github.com/KlapkiSzatana/budget-app" \
  --maintainer "KlapkiSzatana" \
  --description "Zarządzanie Budżetem Domowym" \
  --prefix / \
  -C build/package-root \
  -p build/packages \
  .
```

Gotowa paczka pojawi się w katalogu `build/packages/`.

## 8. Artefakty wynikowe

Po pełnej budowie otrzymasz:

- binarkę Linux: `dist/budget-app/`
- paczkę Debian: `build/packages/*.deb`
- paczkę RPM: `build/packages/*.rpm`

## 9. Uwagi

- Build Windows i macOS jest utrzymywany osobno w GitHub Actions: `.github/workflows/build.yml`.
- Paczki `.deb` i `.rpm` są budowane z lokalnej binarki `PyInstaller`, więc przed pakowaniem zawsze wykonaj krok z sekcji 4.
- Na bardzo minimalnych systemach może być potrzebne doinstalowanie podstawowych bibliotek desktopowych Qt/GL dostępnych w dystrybucji.
