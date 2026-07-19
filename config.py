import sys
import os
import gettext
import json
import atexit
import tempfile
import time

WERSJA = "3.4"
PRODUCENT = "KlapkiSzatana"
CASH_SAVINGS_NAME = "Oszczędności"
APP_ID = "budget-app"


if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)

    INTERNAL_DIR = os.path.join(BASE_DIR, "_internal")

    if os.path.exists(os.path.join(INTERNAL_DIR, "locales")):
        LOCALEDIR = os.path.join(INTERNAL_DIR, "locales")
    else:
        LOCALEDIR = os.path.join(BASE_DIR, "locales")

else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOCALEDIR = os.path.join(BASE_DIR, "locales")

USER_HOME = os.path.expanduser("~")
APP_DIR = os.path.join(USER_HOME, ".BudgetApp")

if not os.path.exists(APP_DIR):
    try:
        os.makedirs(APP_DIR)
    except OSError:
        APP_DIR = USER_HOME

ERROR_LOG_PATH = os.path.join(APP_DIR, "error_log.txt")
CRASH_LOG_PATH = os.path.join(APP_DIR, "crash_log.txt")
APP_SETTINGS_PATH = os.path.join(APP_DIR, "app_settings.json")
APP_TEMP_OWNER = str(os.getuid()) if hasattr(os, "getuid") else os.environ.get("USERNAME", "user")
APP_TEMP_DIR = os.path.join(tempfile.gettempdir(), f"{APP_ID}-{APP_TEMP_OWNER}")

_TEMP_FILES_TO_CLEAN = []


def _ensure_private_temp_dir():
    os.makedirs(APP_TEMP_DIR, exist_ok=True)
    if os.name != "nt":
        try:
            os.chmod(APP_TEMP_DIR, 0o700)
        except OSError:
            pass


def cleanup_temp_files(include_stale=False):
    targets = list(_TEMP_FILES_TO_CLEAN)
    if include_stale and os.path.isdir(APP_TEMP_DIR):
        cutoff = time.time() - 24 * 60 * 60
        for name in os.listdir(APP_TEMP_DIR):
            if not name.startswith("budgetapp_"):
                continue
            path = os.path.join(APP_TEMP_DIR, name)
            try:
                if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                    targets.append(path)
            except OSError:
                pass

    for file_path in targets:
        try:
            abs_path = os.path.abspath(file_path)
            if os.path.commonpath([os.path.abspath(APP_TEMP_DIR), abs_path]) == os.path.abspath(APP_TEMP_DIR):
                if os.path.exists(abs_path):
                    os.remove(abs_path)
        except (OSError, ValueError):
            pass


def create_private_temp_file(data, suffix=".bin"):
    _ensure_private_temp_dir()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="budgetapp_", dir=APP_TEMP_DIR) as tmp_file:
        tmp_file.write(data)
        tmp_path = tmp_file.name
    if os.name != "nt":
        try:
            os.chmod(tmp_path, 0o600)
        except OSError:
            pass
    _TEMP_FILES_TO_CLEAN.append(tmp_path)
    return tmp_path


cleanup_temp_files(include_stale=True)
atexit.register(cleanup_temp_files)

DEFAULT_LANGUAGE = "pl"

LANGUAGE_NAMES = {
    "pl": "Polski",
    "en": "English",
}

LANGUAGE_FLAGS = {
    "pl": "🇵🇱",
    "en": "🇬🇧",
}

_json_translations = {}
_gettext_translator = gettext.NullTranslations()
_current_language = DEFAULT_LANGUAGE


def _load_app_settings():
    try:
        if os.path.exists(APP_SETTINGS_PATH):
            with open(APP_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save_app_settings(settings):
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        with open(APP_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def normalize_language_code(language):
    return str(language or DEFAULT_LANGUAGE).strip().lower().replace("-", "_").split("_")[0] or DEFAULT_LANGUAGE


def discover_languages():
    languages = {DEFAULT_LANGUAGE}
    if os.path.isdir(LOCALEDIR):
        for name in os.listdir(LOCALEDIR):
            path = os.path.join(LOCALEDIR, name)
            if os.path.isfile(path) and name.lower().endswith(".json"):
                languages.add(normalize_language_code(os.path.splitext(name)[0]))
    return sorted(languages)


def get_language_code():
    settings = _load_app_settings()
    return normalize_language_code(settings.get("language", DEFAULT_LANGUAGE))


def set_language_code(language):
    settings = _load_app_settings()
    settings["language"] = normalize_language_code(language)
    _save_app_settings(settings)


def display_language_name(language):
    code = normalize_language_code(language)
    flag = LANGUAGE_FLAGS.get(code, "🏳")
    name = LANGUAGE_NAMES.get(code, code.upper())
    return f"{flag} {name} ({code})"


def _load_json_translations(language):
    path = os.path.join(LOCALEDIR, f"{language}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def install_language(language=None, persist=False):
    global _current_language, _json_translations, _gettext_translator
    selected = normalize_language_code(language or get_language_code())
    _current_language = selected
    _json_translations = {} if selected == DEFAULT_LANGUAGE else _load_json_translations(selected)
    _gettext_translator = gettext.translation('base', LOCALEDIR, languages=[selected], fallback=True)
    if persist:
        set_language_code(selected)
    refresh_language_constants()
    return selected


def _(s):
    source = str(s)
    if _current_language != DEFAULT_LANGUAGE:
        translated = _json_translations.get(source)
        if translated:
            return str(translated)
        gettext_value = _gettext_translator.gettext(source)
        if gettext_value != source:
            return gettext_value
    return source


def get_database_dir():
    settings = _load_app_settings()
    directory = settings.get("database_dir") or APP_DIR
    directory = os.path.abspath(os.path.expanduser(str(directory)))
    return directory


def set_database_dir(directory):
    settings = _load_app_settings()
    settings["database_dir"] = os.path.abspath(os.path.expanduser(str(directory or APP_DIR)))
    _save_app_settings(settings)


def get_database_path(db_name="budzet.db"):
    directory = get_database_dir()
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, db_name)


def get_attachments_dir():
    directory = os.path.join(get_database_dir(), "attachments")
    os.makedirs(directory, exist_ok=True)
    return directory

APPNAME = _("Budżet Domowy")

MONTH_NAME = [
    _("Styczeń"), _("Luty"), _("Marzec"), _("Kwiecień"), _("Maj"), _("Czerwiec"),
    _("Lipiec"), _("Sierpień"), _("Wrzesień"), _("Październik"), _("Listopad"), _("Grudzień")
]

DAYS_PL = [
    _("Poniedziałek"), _("Wtorek"), _("Środa"), _("Czwartek"),
    _("Piątek"), _("Sobota"), _("Niedziela")
]


def refresh_language_constants():
    global APPNAME
    APPNAME = _("Budżet Domowy")
    MONTH_NAME[:] = [
        _("Styczeń"), _("Luty"), _("Marzec"), _("Kwiecień"), _("Maj"), _("Czerwiec"),
        _("Lipiec"), _("Sierpień"), _("Wrzesień"), _("Październik"), _("Listopad"), _("Grudzień")
    ]
    DAYS_PL[:] = [
        _("Poniedziałek"), _("Wtorek"), _("Środa"), _("Czwartek"),
        _("Piątek"), _("Sobota"), _("Niedziela")
    ]


install_language(get_language_code())

def setup_crash_handlers():
    import faulthandler
    try:
        crash_file = open(CRASH_LOG_PATH, "w")
        faulthandler.enable(file=crash_file)
    except Exception:
        pass
    sys.excepthook = global_exception_handler

def global_exception_handler(exc_type, exc_value, exc_traceback):
    import traceback
    from datetime import datetime
    from PySide6.QtWidgets import QMessageBox, QApplication

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    full_log = f"--- CRITICAL ERROR {error_time} ---\n{error_msg}\n"

    try:
        with open(ERROR_LOG_PATH, "a") as f:
            f.write(full_log)
    except Exception:
        pass

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
        print("CRITICAL ERROR (GUI FAILED):", file=sys.stderr)
        print(error_msg, file=sys.stderr)

import json
from pathlib import Path

TABLE_CONFIG_PATH = Path.home() / ".config" / "BudgetApp" / "table.conf"

def save_table_widths(widths_dict):
    try:
        TABLE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TABLE_CONFIG_PATH, 'w') as f:
            json.dump(widths_dict, f)
    except Exception as e:
        print(f"Błąd zapisu szerokości kolumn: {e}")

def load_table_widths():
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
    is_mac = sys.platform == "darwin"
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

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def get_shortcut(self, name):
        from PySide6.QtGui import QKeySequence
        return QKeySequence(self.SHORTCUTS[name])

    def setup_all_menus(self):
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

        act_cash_transfer = QAction(_("Migracja kasy między kontami"), self.window)
        act_cash_transfer.triggered.connect(self.window.open_account_transfer_dialog)
        edit_menu.addAction(act_cash_transfer)

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
        from datetime import datetime
        help_menu = menu_bar.addMenu(_("Pomoc"))

        act_guide = QAction(_("Uruchom przewodnik"), self.window)
        act_guide.setShortcut(self.get_shortcut("help_guide"))
        act_guide.triggered.connect(self.window.run_guide)
        help_menu.addAction(act_guide)

        def show_custom_about():
            msg = QMessageBox(self.window)
            msg.setWindowTitle(_("O programie"))
            msg.setIcon(QMessageBox.Information)

            start_year = 2025
            current_year = datetime.now().year
            if current_year > start_year:
                years_range = f"{start_year}-{current_year}"
            else:
                years_range = f"{start_year}"

            about_text = (
                f"<div style='font-size: 13px; line-height: 150%;'>"
                f"<b style='font-size: 16px;'>{APPNAME}</b><br>"
                f"<b>{_('Wersja')}:</b> {WERSJA}<br>"
                f"<b>{_('Wydawca')}:</b> {PRODUCENT}<br>"
                f"<b>© {years_range}</b> {PRODUCENT}<br><br>"
                f"<b>Strona projektu:</b><br>"
                f"<a href='https://github.com/KlapkiSzatana/budget-app' style='color: #3498db; text-decoration: none;'>"
                f"github.com/KlapkiSzatana/budget-app</a>"
                f"</div>"
            )
            msg.setText(about_text)

            msg.setStyleSheet("""
                QMessageBox {
                    min-width: 350px;
                }
                QLabel {
                    padding-left: 10px;
                    padding-right: 15px;
                    padding-bottom: 5px;
                }
                QPushButton {
                    min-width: 80px;
                    padding: 5px;
                }
            """)

            msg.exec()

        act_bug = QAction(_("Zgłoś błąd / sugestię"), self.window)
        act_bug.triggered.connect(self.window.open_bug_report_dialog)
        help_menu.addAction(act_bug)

        act_about = QAction(_("O programie"), self.window)
        act_about.triggered.connect(show_custom_about)
        help_menu.addAction(act_about)
