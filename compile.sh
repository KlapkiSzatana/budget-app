#!/bin/bash

# Zatrzymanie skryptu natychmiast, jeśli wystąpi jakikolwiek błąd
set -e

echo "🚀 Rozpoczynam automatyczny proces kompilacji..."

# 1. Tworzenie wirtualnego środowiska (jeśli nie istnieje)
if [ ! -d "venv" ]; then
    echo "📦 Tworzenie wirtualnego środowiska (venv)..."
    python3 -m venv venv
else
    echo "✅ Wirtualne środowisko (venv) już istnieje."
fi

# 2. Aktywacja wirtualnego środowiska
echo "🔌 Aktywacja venv..."
source venv/bin/activate

# 3. Aktualizacja pip i instalacja zależności z requirements.txt
if [ -f "requirements.txt" ]; then
    echo "⬇️  Instalowanie/Aktualizowanie bibliotek z requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "⚠️  OSTRZEŻENIE: Nie znaleziono pliku requirements.txt!"
fi

# 4. Instalacja Nuitka (oraz zstandard dla lepszej kompresji)
echo "🔨 Instalowanie/Sprawdzanie Nuitka..."
pip install nuitka zstandard

# 5. Uruchomienie skryptu budującego
if [ -f "build.sh" ]; then
    echo "⚙️  Uruchamianie build.sh..."
    # Nadanie uprawnień wykonywania dla pewności
    chmod +x build.sh
    ./build.sh
else
    echo "❌ BŁĄD: Nie znaleziono pliku build.sh w tym katalogu!"
    exit 1
fi

echo "✨ Proces zakończony! Twoja aplikacja jest gotowa."
