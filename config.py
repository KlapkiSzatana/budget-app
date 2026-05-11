import sys
import os
import gettext

# --- STAŁE APLIKACJI ---
WERSJA = "1.6.3"
PRODUCENT = "KlapkiSzatana"
CASH_SAVINGS_NAME = "Oszczędności"
APP_ID = "budget-app"


# --- KONFIGURACJA ŚCIEŻEK ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOCALEDIR = os.path.join(BASE_DIR, 'locales')
USER_HOME = os.path.expanduser("~")
APP_DIR = os.path.join(USER_HOME, ".BudgetApp")

# Tworzenie katalogu aplikacji
if not os.path.exists(APP_DIR):
    try:
        os.makedirs(APP_DIR)
    except OSError:
        APP_DIR = USER_HOME  # Fallback

ERROR_LOG_PATH = os.path.join(APP_DIR, "error_log.txt")
CRASH_LOG_PATH = os.path.join(APP_DIR, "crash_log.txt")

# --- KONFIGURACJA TŁUMACZEŃ (i18n) ---
try:
    # Inicjalizacja gettext - globalnie dla całej aplikacji
    translator = gettext.translation('base', LOCALEDIR, fallback=True)
    _ = translator.gettext
except Exception:
    def _(s): return s

APPNAME = _("Budżet Domowy")

# Stałe tekstowe wymagające tłumaczeń (muszą być po definicji _)
MONTH_NAME = [
    _("Styczeń"), _("Luty"), _("Marzec"), _("Kwiecień"), _("Maj"), _("Czerwiec"),
    _("Lipiec"), _("Sierpień"), _("Wrzesień"), _("Październik"), _("Listopad"), _("Grudzień")
]

DAYS_PL = [
    _("Poniedziałek"), _("Wtorek"), _("Środa"), _("Czwartek"),
    _("Piątek"), _("Sobota"), _("Niedziela")
]

# --- SYSTEM OBSŁUGI BŁĘDÓW ---

def setup_crash_handlers():
    """Inicjalizuje obsługę twardych crashy (C++) oraz wyjątków Pythona."""
    import faulthandler

    # 1. Obsługa twardych crashy (SIGSEGV)
    try:
        crash_file = open(CRASH_LOG_PATH, "w")
        faulthandler.enable(file=crash_file)
    except Exception:
        pass

    # 2. Globalny hook na wyjątki Pythona
    sys.excepthook = global_exception_handler

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Przechwytuje nieobsłużone wyjątki i wyświetla okno błędu."""
    import traceback
    from datetime import datetime
    from PySide6.QtWidgets import QMessageBox, QApplication

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    full_log = f"--- CRITICAL ERROR {error_time} ---\n{error_msg}\n"

    # Zapis do pliku
    try:
        with open(ERROR_LOG_PATH, "a") as f:
            f.write(full_log)
    except Exception:
        pass

    # Wyświetlenie GUI (jeśli możliwe)
    try:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(_("Błąd Krytyczny"))
        msg_box.setText(_("Wystąpił nieoczekiwany błąd aplikacji."))
        msg_box.setInformativeText(
            _("Log został zapisany w:\n{}\n\nMożesz skopiować błąd poniżej:").format(ERROR_LOG_PATH)
        )
        msg_box.setDetailedText(error_msg)
        msg_box.setStandardButtons(QMessageBox.Close)
        msg_box.exec()
    except Exception:
        # Fallback na stderr jeśli GUI zawiedzie
        print("CRITICAL ERROR (GUI FAILED):", file=sys.stderr)
        print(error_msg, file=sys.stderr)

import json
from pathlib import Path

# Ścieżka do pliku konfiguracyjnego tabeli
TABLE_CONFIG_PATH = Path.home() / ".config" / "BudgetApp" / "table.conf"

def save_table_widths(widths_dict):
    """Zapisuje słownik szerokości kolumn do pliku JSON."""
    try:
        TABLE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TABLE_CONFIG_PATH, 'w') as f:
            json.dump(widths_dict, f)
    except Exception as e:
        print(f"Błąd zapisu szerokości kolumn: {e}")

def load_table_widths():
    """Wczytuje szerokości kolumn. Zwraca słownik lub None."""
    if TABLE_CONFIG_PATH.exists():
        try:
            with open(TABLE_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Błąd odczytu szerokości kolumn: {e}")
    return None

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import QObject, Qt

class AppMenuConfig(QObject):
    """Zarządza paskiem menu i skrótami klawiszowymi aplikacji."""

    # --- SEKCJA EDYCJI SKRÓTÓW (Łatwa modyfikacja) ---
    is_mac = sys.platform == "darwin"
    # Na Macu 'Ctrl' w QKeySequence to klawisz Command,
    # na Windows/Linux to po prostu Ctrl.
    cmd = "Ctrl"

    SHORTCUTS = {
        "file_backup": QKeySequence(f"{cmd}+B"),
        "file_exit": QKeySequence(f"{cmd}+Q"),
        "edit_income": QKeySequence(f"{cmd}+Shift+I"),
        "edit_expense": QKeySequence(f"{cmd}+Shift+E"),
        "edit_savings": QKeySequence(f"{cmd}+Shift+S"),
        "tools_bills": QKeySequence(f"{cmd}+L"),
        "tools_pdf": QKeySequence(f"{cmd}+P"),
        "tools_search": QKeySequence(f"{cmd}+F"),
        "options_settings": QKeySequence(f"{cmd}+," if is_mac else f"{cmd}+Alt+S"),
        "help_guide": QKeySequence("F1"),
    }
    # ------------------------------------------------

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def setup_all_menus(self):
        """Główna metoda budująca pasek menu."""
        menu_bar = self.window.menuBar()
        menu_bar.clear()

        self._build_file_menu(menu_bar)
        self._build_edit_menu(menu_bar)
        self._build_tools_menu(menu_bar)
        self._build_options_menu(menu_bar)
        self._build_help_menu(menu_bar)

    def _build_file_menu(self, menu_bar):
        file_menu = menu_bar.addMenu(_("Plik"))

        act_backup = QAction(_("Kopia zapasowa"), self.window)
        act_backup.setShortcut(self.SHORTCUTS["file_backup"])
        act_backup.triggered.connect(self.window.btn_back.click)
        file_menu.addAction(act_backup)

        file_menu.addSeparator()

        act_exit = QAction(_("Zakończ"), self.window)
        act_exit.setShortcut(self.SHORTCUTS["file_exit"])
        act_exit.triggered.connect(self.window.close)
        file_menu.addAction(act_exit)

    def _build_edit_menu(self, menu_bar):
        edit_menu = menu_bar.addMenu(_("Transakcje"))

        act_inc = QAction(_("Dodaj przychód"), self.window)
        act_inc.setShortcut(self.SHORTCUTS["edit_income"])
        act_inc.triggered.connect(self.window.open_income_dialog)
        edit_menu.addAction(act_inc)

        act_exp = QAction(_("Dodaj wydatek"), self.window)
        act_exp.setShortcut(self.SHORTCUTS["edit_expense"])
        act_exp.triggered.connect(self.window.open_expense_dialog)
        edit_menu.addAction(act_exp)

        act_sav = QAction(_("Zarządzaj oszczędnościami"), self.window)
        act_sav.setShortcut(self.SHORTCUTS["edit_savings"])
        act_sav.triggered.connect(self.window.open_savings_dialog)
        edit_menu.addAction(act_sav)

    def _build_tools_menu(self, menu_bar):
        tools_menu = menu_bar.addMenu(_("Narzędzia"))

        act_search = QAction(_("Skocz do wyszukiwarki"), self.window)
        act_search.setShortcut(self.SHORTCUTS["tools_search"])
        act_search.triggered.connect(self.window.search_bar.setFocus)
        tools_menu.addAction(act_search)

        act_bills = QAction(_("Rachunki i opłaty"), self.window)
        act_bills.setShortcut(self.SHORTCUTS["tools_bills"])
        act_bills.triggered.connect(self.window.open_bills_manager)
        tools_menu.addAction(act_bills)

        act_pdf = QAction(_("Generuj raport PDF"), self.window)
        act_pdf.setShortcut(self.SHORTCUTS["tools_pdf"])
        act_pdf.triggered.connect(self.window.open_report_dialog)
        tools_menu.addAction(act_pdf)

    def _build_options_menu(self, menu_bar):
        options_menu = menu_bar.addMenu(_("Opcje"))

        act_settings = QAction(_("Ustawienia aplikacji"), self.window)
        act_settings.setShortcut(self.SHORTCUTS["options_settings"])
        act_settings.triggered.connect(self.window.open_settings_dialog)
        options_menu.addAction(act_settings)

    def _build_help_menu(self, menu_bar):
        from PySide6.QtWidgets import QMessageBox
        help_menu = menu_bar.addMenu(_("Pomoc"))

        act_guide = QAction(_("Uruchom przewodnik"), self.window)
        act_guide.setShortcut(self.SHORTCUTS["help_guide"])
        act_guide.triggered.connect(self.window.run_guide)
        help_menu.addAction(act_guide)

        act_about = QAction(_("O programie"), self.window)
        act_about.triggered.connect(lambda: QMessageBox.about(
            self.window, _("O programie"),
            f"<b>{APPNAME}</b><br>{_('Wersja')}: {WERSJA}<br>© {PRODUCENT}"
        ))
        help_menu.addAction(act_about)
