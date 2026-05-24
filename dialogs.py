import os
import sys
import platform
import urllib.parse
import subprocess
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QPushButton, QDateEdit, QGroupBox, QFormLayout,
                               QDialogButtonBox, QRadioButton, QButtonGroup,
                               QProgressBar, QTextEdit, QSpinBox, QFrame, QWidget,
                               QCheckBox, QListWidget, QListWidgetItem, QAbstractItemView, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QDate
from config import _, CASH_SAVINGS_NAME, MONTH_NAME
try:
    import shiboken
except ImportError:
    shiboken = None

class ProcessingDialog(QDialog):
    def __init__(self, parent=None, title=None, label_text=None):
        super().__init__(parent)
        self.setWindowTitle(title if title else _("Przetwarzanie..."))
        self.setFixedSize(300, 120)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setModal(True)
        layout = QVBoxLayout(self)
        self.lbl = QLabel(label_text if label_text else _("Proszę czekać..."))
        self.lbl.setAlignment(Qt.AlignCenter)
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 0)
        layout.addWidget(self.lbl)
        layout.addWidget(self.pbar)

class BackupDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QSizePolicy
        self.db = db_manager
        self.setWindowTitle(_("Kopia Zapasowa"))
        self.resize(500, 250)
        main_btn_base = """
            QPushButton {
                font-size: 12px; font-weight: bold; padding: 5px 15px; border-radius: 6px;
                border: 2px solid; background-color: transparent; min-height: 20px;
            }
        """
        blue_style = main_btn_base + """
            QPushButton { color: #2980b9; border-color: #3498db; }
            QPushButton:hover { background-color: #2980b9; color: #ffffff; }
        """
        orange_style = main_btn_base + """
            QPushButton { color: #d35400; border-color: #e67e22; }
            QPushButton:hover { background-color: #d35400; color: #ffffff; }
        """
        gray_style = main_btn_base + """
            QPushButton { color: #7f8c8d; border-color: #95a5a6; }
            QPushButton:hover { background-color: #7f8c8d; color: #ffffff; }
        """
        layout = QVBoxLayout(self)
        gb = QGroupBox(_("Ustawienia"))
        form = QFormLayout()
        self.cb_auto = QCheckBox(_("Rób automatycznie przy zamknięciu"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        h = QHBoxLayout()
        h.setSpacing(5)
        h.addWidget(self.path_edit)

        btn = QPushButton("...")
        btn.setFixedWidth(60)
        btn.setStyleSheet(gray_style)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.select_path)

        h.addWidget(btn)

        form.addRow(self.cb_auto)
        form.addRow(_("Lokalizacja:"), h)
        gb.setLayout(form)
        layout.addWidget(gb)

        h_act = QHBoxLayout()
        h_act.setSpacing(15)

        b1 = QPushButton(_("💾 Utwórz Kopię Teraz"))
        b1.setStyleSheet(blue_style)
        b1.setCursor(Qt.PointingHandCursor)
        b1.clicked.connect(self.create_now)

        b2 = QPushButton(_("🔄 Przywróć z Kopii"))
        b2.setStyleSheet(orange_style)
        b2.setCursor(Qt.PointingHandCursor)
        b2.clicked.connect(self.restore_now)

        h_act.addWidget(b1)
        h_act.addWidget(b2)
        layout.addLayout(h_act)

        self.load_config()

        btn_close = QPushButton(_("ZAMKNIJ"))
        btn_close.setStyleSheet(gray_style)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)

        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(btn_close)

        layout.addLayout(close_layout)

    def load_config(self):
        cfg = self.db.get_config("backup_config")
        if cfg:
            self.cb_auto.setChecked(cfg.get("auto_backup", False))
            self.path_edit.setText(cfg.get("backup_path", ""))

    def save_config(self):
        self.db.save_config("backup_config", {
            "auto_backup": self.cb_auto.isChecked(),
            "backup_path": self.path_edit.text()
        })

    def select_path(self):
        from PySide6.QtWidgets import QFileDialog
        d = QFileDialog.getExistingDirectory(self, _("Wybierz folder"))
        if d: self.path_edit.setText(d); self.save_config()

    def create_now(self):
        from PySide6.QtWidgets import QApplication, QMessageBox
        self.save_config()

        pd = ProcessingDialog(self, _("Kopia zapasowa"), _("Trwa tworzenie kopii..."))
        pd.pbar.setRange(0, 100)
        pd.pbar.setValue(0)
        pd.show()

        def update_pbar(val):
            pd.pbar.setValue(val)
            QApplication.processEvents()

        success, msg = self.db.perform_backup(progress_callback=update_pbar)
        pd.close()

        if success:
            QMessageBox.information(self, _("Sukces"), _("Utworzono kopię zapasową w:\n{}").format(msg))
        else:
            QMessageBox.warning(self, _("Błąd"), msg)

    def restore_now(self):
        import sys
        import os
        from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication

        path = self.path_edit.text()
        dialog = QFileDialog(self)
        dialog.setWindowTitle(_("Wybierz plik"))
        dialog.setDirectory(path)
        dialog.setNameFilters(["Backup (*.zip)"])
        dialog.setFileMode(QFileDialog.ExistingFile)

        # Wymuszamy użycie natywnego menedżera plików systemu (brak brzydkiego okna Qt)
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)

        f = ""
        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                f = selected_files[0]

        if f and QMessageBox.Yes == QMessageBox.question(
            self, _("Potwierdź"), _("Przywrócenie nadpisze obecne dane. Kontynuować?")
        ):
            pd = ProcessingDialog(self, _("Przywracanie"), _("Trwa przywracanie bazy danych..."))
            pd.pbar.setRange(0, 100)
            pd.pbar.setValue(0)
            pd.show()

            def update_pbar(val):
                pd.pbar.setValue(val)
                QApplication.processEvents()

            if self.db.restore_database(f, progress_callback=update_pbar):
                pd.close()
                QMessageBox.information(
                    self, _("Sukces"),
                    _("Baza danych została przywrócona.\nAplikacja zostanie teraz uruchomiona ponownie.")
                )
                python = sys.executable
                os.execl(python, python, *sys.argv)
            else:
                pd.close()
                QMessageBox.critical(self, _("Błąd"), _("Nie udało się przywrócić bazy danych."))

    def closeEvent(self, e):
        self.save_config()
        e.accept()

class WeeklyLimitDialog(QDialog):
    def __init__(self, parent=None, db_manager=None, target_monday_date=None):
        super().__init__(parent)
        self.db = db_manager
        self.target_date = target_monday_date
        if not self.target_date:
            from datetime import datetime, timedelta
            today = datetime.now().date()
            monday = today - timedelta(days=today.weekday())
            self.target_date = monday.strftime("%Y-%m-%d")

        self.setWindowTitle(_("Ustawienia Limitu Tygodniowego"))
        self.resize(420, 550)
        layout = QVBoxLayout(self)
        self.cb_enabled = QCheckBox(_("Włącz system budżetu tygodniowego"))
        self.cb_enabled.toggled.connect(self.toggle_inputs)
        layout.addWidget(self.cb_enabled)
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        self.settings_container = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_container)
        self.settings_layout.setContentsMargins(0,0,0,0)
        self.lbl_info = QLabel(_("Edycja dla tygodnia od: <b>{}</b>").format(self.target_date))
        self.lbl_info.setTextFormat(Qt.RichText)
        self.settings_layout.addWidget(self.lbl_info)
        form_layout = QFormLayout()
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("np. 500")

        # --- DODANY WALIDATOR (BLOKADA TEKSTU) ---
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator
        self.amount_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.,]*"), self))
        # ----------------------------------------

        form_layout.addRow(_("Kwota (PLN):"), self.amount_edit)
        self.settings_layout.addLayout(form_layout)
        self.settings_layout.addWidget(QLabel(_("Wybierz kategorie wliczane do limitu:")))
        self.cat_list = QListWidget()
        self.cat_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.settings_layout.addWidget(self.cat_list)
        h_btns = QHBoxLayout()
        btn_all = QPushButton(_("Zaznacz wszystkie"))
        btn_all.clicked.connect(self.select_all)
        btn_none = QPushButton(_("Odznacz wszystkie"))
        btn_none.clicked.connect(self.deselect_all)
        h_btns.addWidget(btn_all); h_btns.addWidget(btn_none)
        self.settings_layout.addLayout(h_btns)
        layout.addWidget(self.settings_container)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.save_and_close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.load_settings()

    def toggle_inputs(self, checked): self.settings_container.setEnabled(checked)

    def load_settings(self):
        is_system_enabled = self.db.is_weekly_system_enabled()
        self.cb_enabled.setChecked(is_system_enabled)
        found, amount, saved_cats = self.db.get_weekly_limit_for_week(self.target_date)
        global_cfg = self.db.get_config("weekly_limit_config")
        global_active_cats = global_cfg.get("categories", []) if global_cfg else []
        if not found:
            amount = 0.0
            saved_cats = global_active_cats
        self.amount_edit.setText(str(amount))
        all_cats = self.db.get_categories()
        self.cat_list.clear()
        for cat in all_cats:
            item = QListWidgetItem(cat)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if cat in saved_cats or cat in global_active_cats: item.setCheckState(Qt.Checked)
            else: item.setCheckState(Qt.Unchecked)
            self.cat_list.addItem(item)
        self.toggle_inputs(is_system_enabled)

    def select_all(self):
        for i in range(self.cat_list.count()): self.cat_list.item(i).setCheckState(Qt.Checked)

    def deselect_all(self):
        for i in range(self.cat_list.count()): self.cat_list.item(i).setCheckState(Qt.Unchecked)

    def save_and_close(self):
        enabled = self.cb_enabled.isChecked()
        self.db.set_weekly_system_enabled(enabled)
        if enabled:
            try: amt = float(self.amount_edit.text().replace(",", "."))
            except ValueError: amt = 0.0
            selected_cats = []
            for i in range(self.cat_list.count()):
                item = self.cat_list.item(i)
                if item.checkState() == Qt.Checked: selected_cats.append(item.text())
            self.db.set_weekly_limit_for_week(self.target_date, amt, selected_cats)
        self.accept()

class IncomeDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Dodaj Przychód"))
        self.resize(400, 350) # Lekko zwiększona wysokość na nowe pole

        l = QFormLayout(self)
        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)

        # --- NOWE: Wybór Konta ---
        self.account_combo = QComboBox()
        # Pobieramy konta z bazy: id jest danymi ukrytymi (UserData), nazwa widoczną
        for acc_id, name, bal, unused_color in self.db.get_accounts():
            self.account_combo.addItem(name, acc_id)
        # -------------------------

        self.person = QComboBox()
        self.person.setEditable(True)
        self.person.addItems(self.db.get_people())

        self.src = QLineEdit()
        self.src.setPlaceholderText(_("np. Wypłata, Sprzedaż, Zwrot..."))
        self.src.setText(_("Wpływ"))

        self.amt = QLineEdit()
        self.amt.setPlaceholderText("0.00")

        # --- DODANY WALIDATOR (BLOKADA TEKSTU) ---
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator
        self.amt.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.,]*"), self))
        # ----------------------------------------

        # --- NOWE: Pole Szczegóły ---
        from PySide6.QtWidgets import QTextEdit
        self.details = QTextEdit()
        self.details.setPlaceholderText(_("Dodatkowy opis (opcjonalnie)..."))
        self.details.setMaximumHeight(60)

        # --- Sekcja Załącznika ---
        self.attachment_data = None
        self.btn_attach = QPushButton(_("📎 Załącznik"))
        self.btn_attach.setStyleSheet("""
            QPushButton {
                border: 1px solid #95a5a6; border-radius: 6px; padding: 3px;
                font-size: 11px; min-height: 22px;
            }
            QPushButton[attached="true"] {
                background-color: #2ecc71; color: white; border-color: #27ae60;
            }
        """)
        self.btn_attach.clicked.connect(self.select_attachment)

        # --- STYLIZACJA PRZYCISKÓW GŁÓWNYCH ---
        from PySide6.QtWidgets import QDialogButtonBox
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_save = bb.button(QDialogButtonBox.Save)
        btn_cancel = bb.button(QDialogButtonBox.Cancel)

        base_style = """
            QPushButton {
                font-size: 12px; font-weight: bold; padding: 2px 15px; border-radius: 6px;
                border: 2px solid; background-color: transparent; min-height: 22px; max-height: 22px;
            }
        """

        btn_save.setText(_("Zapisz"))
        btn_save.setStyleSheet(base_style + """
            QPushButton { color: #27ae60; border-color: #2ecc71; }
            QPushButton:hover { background-color: #27ae60; color: #ffffff; }
        """)

        btn_cancel.setText(_("Anuluj"))
        btn_cancel.setStyleSheet(base_style + """
            QPushButton { color: #7f8c8d; border-color: #95a5a6; }
            QPushButton:hover { background-color: #7f8c8d; color: #ffffff; }
        """)

        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)

        # --- UKŁAD FORMULARZA ---
        l.addRow(_("Data:"), self.date)
        l.addRow(_("Wpływa na:"), self.account_combo) # <-- DODANE
        l.addRow(_("Osoba:"), self.person)
        l.addRow(_("Źródło:"), self.src)
        l.addRow(_("Kwota:"), self.amt)
        l.addRow(_("Szczegóły:"), self.details)
        l.addRow(_("Dokument:"), self.btn_attach)
        l.addRow(bb)

    def select_attachment(self):
        from PySide6.QtWidgets import QFileDialog
        from config import _

        dialog = QFileDialog(self)
        dialog.setWindowTitle(_("Wybierz potwierdzenie"))
        dialog.setDirectory("")
        dialog.setNameFilters(["Pliki (*.jpg *.png *.pdf)"])
        dialog.setFileMode(QFileDialog.ExistingFile)

        # Wymuszamy natywne okno systemowe (szybkie odświeżanie, miniatury i podgląd PDF)
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)

        path = ""
        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]

        if path:
            try:
                with open(path, "rb") as f:
                    self.attachment_data = f.read()

                self.btn_attach.setText(_("✅ Załączono"))
                self.btn_attach.setProperty("attached", True)
                self.btn_attach.style().unpolish(self.btn_attach)
                self.btn_attach.style().polish(self.btn_attach)
            except Exception as e:
                print(f"Błąd czytania pliku: {e}")

    def get_data(self):
        try:
            val = float(self.amt.text().replace(",", "."))
        except ValueError:
            val = 0.0

        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "type": "income",
            "cat": self.person.currentText(),
            "sub": self.src.text(),
            "amount": val,
            "details": self.details.toPlainText().strip(),
            "attachment": self.attachment_data,
            "account_id": self.account_combo.currentData() # <-- DODANE (ID konta)
        }

class AddExpenseDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Dodaj Wydatek"))
        self.resize(450, 460) # Lekko zwiększona wysokość pod nowe pole konta

        l = QFormLayout(self)

        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)

        # --- NOWE: Wybór Konta ---
        self.account_combo = QComboBox()
        for acc_id, name, bal, acc_color in self.db.get_accounts():
            self.account_combo.addItem(name, acc_id)
        # -------------------------

        h = QHBoxLayout()
        self.cat = QComboBox()
        self.cat.addItems(self.db.get_categories())

        small_btn_style = """
            QPushButton {
                font-size: 14px; font-weight: bold; border-radius: 4px;
                border: 1px solid palette(mid); background-color: transparent;
                color: palette(text); min-width: 26px; max-width: 26px;
                min-height: 26px; max-height: 26px;
            }
            QPushButton:hover { background-color: palette(mid); }
        """

        b1 = QPushButton("+"); b1.setStyleSheet(small_btn_style); b1.clicked.connect(self.add_c)
        b2 = QPushButton("-"); b2.setStyleSheet(small_btn_style); b2.clicked.connect(self.del_c)

        h.addWidget(self.cat); h.addWidget(b1); h.addWidget(b2)

        self.desc = QLineEdit()
        self.desc.setPlaceholderText(_("Gdzie? (np. Biedronka, Orlen)"))

        # --- ZMIANA: Pole Szczegóły jako QTextEdit ---
        self.details = QTextEdit()
        self.details.setPlaceholderText(_("Co kupiono? (każda rzecz w nowej linii...)"))
        self.details.setFixedHeight(80)
        self.details.setTabChangesFocus(True)
        # --------------------------------------------

        self.amt = QLineEdit()
        self.amt.setPlaceholderText("0.00")

        # --- DODANY WALIDATOR (BLOKADA TEKSTU) ---
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator
        self.amt.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.,]*"), self))
        # ----------------------------------------

        self.cb_exclude = QCheckBox(_("Pomiń w limicie tygodniowym"))

        self.attachment_data = None
        self.btn_attach = QPushButton(_("📎 Załącznik"))
        self.btn_attach.setStyleSheet("""
            QPushButton { border: 1px solid #95a5a6; border-radius: 6px; padding: 3px; font-size: 11px; min-height: 22px; }
            QPushButton[attached="true"] { background-color: #2ecc71; color: white; border-color: #27ae60; }
        """)
        self.btn_attach.clicked.connect(self.select_attachment)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_save = bb.button(QDialogButtonBox.Save)
        btn_cancel = bb.button(QDialogButtonBox.Cancel)

        main_btn_base = "QPushButton { font-size: 12px; font-weight: bold; padding: 2px 15px; border-radius: 6px; border: 2px solid; background-color: transparent; min-height: 22px; max-height: 22px; }"
        btn_save.setText(_("Zapisz Wydatek")); btn_save.setStyleSheet(main_btn_base + "QPushButton { color: #c0392b; border-color: #e74c3c; } QPushButton:hover { background-color: #c0392b; color: #ffffff; }")
        btn_cancel.setText(_("Anuluj")); btn_cancel.setStyleSheet(main_btn_base + "QPushButton { color: #7f8c8d; border-color: #95a5a6; } QPushButton:hover { background-color: #7f8c8d; color: #ffffff; }")

        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)

        l.addRow(_("Data:"), self.date)
        l.addRow(_("Płacę z:"), self.account_combo) # <-- DODANE
        l.addRow(_("Kategoria:"), h)
        l.addRow(_("Opis (Sklep):"), self.desc)
        l.addRow(_("Szczegóły:"), self.details)
        l.addRow(_("Dokument:"), self.btn_attach)
        l.addRow(_("Kwota:"), self.amt)
        l.addRow("", self.cb_exclude)
        l.addRow(bb)

    def select_attachment(self):
        from PySide6.QtWidgets import QFileDialog
        from config import _
        dialog = QFileDialog(self)
        dialog.setWindowTitle(_("Wybierz potwierdzenie"))
        dialog.setDirectory("")
        dialog.setNameFilters(["Pliki (*.jpg *.png *.pdf)"])
        dialog.setFileMode(QFileDialog.ExistingFile)

        # Wymuszamy natywne okno systemowe (szybkie odświeżanie, miniatury i podgląd PDF)
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)

        path = ""
        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]
        if path:
            try:
                with open(path, "rb") as f:
                    self.attachment_data = f.read()
                self.btn_attach.setText(_("✅ Załączono"))
                self.btn_attach.setProperty("attached", True)
                self.btn_attach.style().unpolish(self.btn_attach)
                self.btn_attach.style().polish(self.btn_attach)
            except Exception as e:
                print(f"Błąd czytania pliku: {e}")

    def add_c(self):
        from PySide6.QtWidgets import QInputDialog
        t, ok = QInputDialog.getText(self, _("Nowa Kategoria"), _("Nazwa:"))
        if ok and t:
            self.db.add_category(t)
            self.cat.clear(); self.cat.addItems(self.db.get_categories()); self.cat.setCurrentText(t)

    def del_c(self):
        from PySide6.QtWidgets import QMessageBox
        c = self.cat.currentText()
        if c and c != _("Inne") and QMessageBox.Yes == QMessageBox.question(self, _("Usuń"), _("Usunąć kategorię '{}'?").format(c)):
            self.db.delete_category_safe(c); self.cat.clear(); self.cat.addItems(self.db.get_categories()); self.cat.setCurrentText("Inne")

    def get_data(self):
        try: val = float(self.amt.text().replace(",", "."))
        except ValueError: val = 0.0
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "type": "expense",
            "cat": self.cat.currentText(),
            "sub": self.desc.text(),
            "details": self.details.toPlainText(),
            "amount": val,
            "exclude": 1 if self.cb_exclude.isChecked() else 0,
            "attachment": self.attachment_data,
            "account_id": self.account_combo.currentData() # <-- DODANE
        }

class AddGoalDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Nowy Cel"))
        self.resize(300, 200)
        l = QFormLayout(self)

        # --- DEFINICJA STYLI ---
        base_style = """
            QPushButton {
                font-size: 12px; font-weight: bold; padding: 6px 15px;
                border-radius: 6px; border: 2px solid; background-color: transparent;
            }
        """
        inc_style = base_style + """
            QPushButton { color: #27ae60; border-color: #2ecc71; }
            QPushButton:hover { background-color: #27ae60; color: #ffffff; }
        """
        exp_style = base_style + """
            QPushButton { color: #c0392b; border-color: #e74c3c; }
            QPushButton:hover { background-color: #c0392b; color: #ffffff; }
        """

        self.n = QLineEdit()
        self.n.setStyleSheet("padding: 4px;")

        # --- Wybór Konta ---
        self.account_combo = QComboBox()
        for acc_id, name, bal, acc_color in self.db.get_accounts():
            self.account_combo.addItem(name, acc_id)
        self.account_combo.hide()

        self.t = QLineEdit()
        self.t.setPlaceholderText("0.00")
        self.t.setStyleSheet("padding: 4px;")

        # Walidator kwoty
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator
        self.t.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.,]*"), self))

        # --- PRZYCISKI (Ręczna stylizacja ButtonBox) ---
        self.bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.bb.accepted.connect(self.accept)
        self.bb.rejected.connect(self.reject)

        # Wyciągamy przyciski i nadajemy style
        btn_save = self.bb.button(QDialogButtonBox.Save)
        if btn_save:
            btn_save.setText(_("ZAPISZ"))
            btn_save.setStyleSheet(inc_style)

        btn_cancel = self.bb.button(QDialogButtonBox.Cancel)
        if btn_cancel:
            btn_cancel.setText(_("ANULUJ"))
            btn_cancel.setStyleSheet(exp_style)

        # Układanie w formularzu
        l.addRow(_("Nazwa celu:"), self.n)
        #l.addRow(_("Domyślne konto:"), self.account_combo)
        l.addRow(_("Kwota celu (PLN):"), self.t)
        l.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)) # Odstęp
        l.addRow(self.bb)

    def accept(self):
        from PySide6.QtWidgets import QMessageBox
        name = self.n.text().strip()
        if not name:
            QMessageBox.warning(self, _("Błąd"), _("Proszę podać nazwę celu!"))
            return

        amount_raw = self.t.text().strip()
        if not amount_raw:
            QMessageBox.warning(self, _("Błąd"), _("Proszę podać kwotę celu!"))
            return

        try:
            amount = float(amount_raw.replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, _("Błąd"), _("Proszę podać poprawną kwotę celu!"))
            return

        super().accept()

    def get_data(self):
        try:
            val = float(self.t.text().replace(",", "."))
        except ValueError:
            val = 0.0
        return self.n.text().strip(), val, self.account_combo.currentData()

class SavingsTransferDialog(QDialog):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(_("Transfer oszczędności"))
        self.setFixedWidth(380)
        layout = QVBoxLayout(self)

        # --- DEFINICJA STYLI (Spójna z Ustawieniami) ---
        base_style = """
            QPushButton {
                font-size: 12px; font-weight: bold; padding: 6px 15px;
                border-radius: 6px; border: 2px solid; background-color: transparent;
            }
        """
        inc_style = base_style + """
            QPushButton { color: #27ae60; border-color: #2ecc71; }
            QPushButton:hover { background-color: #27ae60; color: #ffffff; }
        """
        exp_style = base_style + """
            QPushButton { color: #c0392b; border-color: #e74c3c; }
            QPushButton:hover { background-color: #c0392b; color: #ffffff; }
        """

        # --- UKŁAD FORMULARZA ---
        # Z KONTA
        layout.addWidget(QLabel(_("Transfer z konta:")))
        self.from_acc = QComboBox()
        layout.addWidget(self.from_acc)

        # NA KONTO
        layout.addWidget(QLabel(_("Transfer na konto:")))
        self.to_acc = QComboBox()
        layout.addWidget(self.to_acc)

        # Wypełnianie kont
        accounts = self.db.get_accounts()
        for acc_id, name, bal, acc_color in accounts:
            self.from_acc.addItem(name, acc_id)
            self.to_acc.addItem(name, acc_id)

        # CEL
        layout.addWidget(QLabel(_("Cel oszczędności:")))
        self.goal_input = QComboBox()

        # --- KLUCZOWA POPRAWKA ---
        # Zamiast brać wszystko z transakcji (gdzie są teraz opisy Wpłata/Wypłata),
        # bierzemy czystą listę z tabeli celów i dodajemy domyślne "Oszczędności"
        from config import CASH_SAVINGS_NAME

        # Pobieramy cele z bazy (używamy Twojej metody get_goals, która już to robi)
        goals = [CASH_SAVINGS_NAME] + self.db.get_goals()

        self.goal_input.addItems(goals)
        layout.addWidget(self.goal_input)

        # KWOTA
        layout.addWidget(QLabel(_("Kwota transferu:")))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        # Dodajmy styl dla LineEdit, żeby pasował do reszty
        self.amount_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 4px;")
        layout.addWidget(self.amount_input)

        layout.addSpacing(10) # Trochę oddechu przed przyciskami

        # --- PRZYCISKI ---
        btns = QHBoxLayout()

        btn_ok = QPushButton(_("PRZENIEŚ"))
        btn_ok.setStyleSheet(inc_style)
        btn_ok.clicked.connect(self.accept)

        btn_cancel = QPushButton(_("ANULUJ"))
        btn_cancel.setStyleSheet(exp_style)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def get_data(self):
        try:
            amt = float(self.amount_input.text().replace(',', '.'))
        except ValueError:
            amt = 0.0
        return {
            "from_id": self.from_acc.currentData(),
            "to_id": self.to_acc.currentData(),
            "goal": self.goal_input.currentText(),
            "amount": amt
        }

class AddSavingsDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Oszczędności"))
        self.resize(450, 380)

        l = QFormLayout(self)

        # Wybór kierunku
        self.rd = QRadioButton(_("Wpłacam na oszczędności"))
        self.rw = QRadioButton(_("Wypłacam z oszczędności"))
        self.rd.setChecked(True)
        h_dir = QHBoxLayout()
        h_dir.addWidget(self.rd)
        h_dir.addWidget(self.rw)

        # Podpięcie dynamicznej zmiany etykiet
        self.rd.toggled.connect(self.update_labels)

        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)

        # --- KONTA BANKOWE ---
        # Konto 1: Z którego schodzi kasa / Na które wraca
        self.lbl_wallet_acc = QLabel(_("Z konta (Portfel):"))
        self.wallet_account_combo = QComboBox()

        # Konto 2: Na którym "siedzą" oszczędności
        self.lbl_savings_acc = QLabel(_("Na konto (Oszczędności):"))
        self.savings_account_combo = QComboBox()

        accounts = self.db.get_accounts()
        for acc_id, name, bal, acc_color in accounts:
            self.wallet_account_combo.addItem(name, acc_id)
            self.savings_account_combo.addItem(name, acc_id)

        self.amt = QLineEdit()
        self.amt.setPlaceholderText("0.00")
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator
        self.amt.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.,]*"), self))

        self.details = QTextEdit()
        self.details.setPlaceholderText(_("Dodatkowy opis (opcjonalnie)..."))
        self.details.setMaximumHeight(60)

        self.attachment_data = None
        self.btn_attach = QPushButton(_("📎 Załącznik"))
        self.btn_attach.setStyleSheet("""
            QPushButton { border: 1px solid #95a5a6; border-radius: 6px; padding: 3px; font-size: 11px; min-height: 22px; }
            QPushButton[attached="true"] { background-color: #2ecc71; color: white; border-color: #27ae60; }
        """)
        self.btn_attach.clicked.connect(self.select_attachment)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_save = bb.button(QDialogButtonBox.Save)
        btn_cancel = bb.button(QDialogButtonBox.Cancel)

        main_btn_base = "QPushButton { font-size: 12px; font-weight: bold; padding: 2px 15px; border-radius: 6px; border: 2px solid; background-color: transparent; min-height: 22px; }"
        btn_save.setText(_("Zatwierdź"))
        btn_save.setStyleSheet(main_btn_base + "QPushButton { color: #2980b9; border-color: #3498db; } QPushButton:hover { background-color: #2980b9; color: white; }")
        btn_cancel.setText(_("Anuluj"))
        btn_cancel.setStyleSheet(main_btn_base + "QPushButton { color: #7f8c8d; border-color: #95a5a6; } QPushButton:hover { background-color: #7f8c8d; color: white; }")

        self.btn_add_goal = QPushButton(_("Dodaj cel"))
        self.btn_add_goal.setStyleSheet(main_btn_base + "QPushButton { color: #d35400; border-color: #e67e22; } QPushButton:hover { background-color: #d35400; color: white; }")
        self.btn_add_goal.clicked.connect(self.open_add_goal_dialog)

        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)

        bottom_buttons = QHBoxLayout()
        bottom_buttons.addWidget(self.btn_add_goal)
        bottom_buttons.addStretch()
        bottom_buttons.addWidget(bb)

        # Dodawanie wierszy do formularza
        l.addRow(_("Operacja:"), h_dir)
        l.addRow(_("Data:"), self.date)
        l.addRow(self.lbl_wallet_acc, self.wallet_account_combo)
        l.addRow(self.lbl_savings_acc, self.savings_account_combo)
        l.addRow(_("Kwota:"), self.amt)
        l.addRow(_("Szczegóły:"), self.details)
        l.addRow(_("Dokument:"), self.btn_attach)
        l.addRow("", bottom_buttons)

    def update_labels(self):
        """Aktualizuje etykiety, by było jasne co skąd wychodzi."""
        if self.rd.isChecked():
            self.lbl_wallet_acc.setText(_("Z konta (Portfel):"))
            self.lbl_savings_acc.setText(_("Na konto (Oszczędności):"))
        else:
            self.lbl_wallet_acc.setText(_("Na konto (Portfel):"))
            self.lbl_savings_acc.setText(_("Z konta (Oszczędności):"))

    def select_attachment(self):
        from PySide6.QtWidgets import QFileDialog
        dialog = QFileDialog(self)
        dialog.setWindowTitle(_("Wybierz potwierdzenie"))
        dialog.setDirectory("")
        dialog.setNameFilters(["Pliki (*.jpg *.png *.pdf)"])
        dialog.setFileMode(QFileDialog.ExistingFile)

        # Wymuszamy natywne okno systemowe
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)

        path = ""
        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]
        if path:
            try:
                with open(path, "rb") as f: self.attachment_data = f.read()
                self.btn_attach.setText(_("✅ Załączono"))
                self.btn_attach.setProperty("attached", True)
                self.btn_attach.style().unpolish(self.btn_attach)
                self.btn_attach.style().polish(self.btn_attach)
            except Exception as e: print(f"Błąd pliku: {e}")

    def open_add_goal_dialog(self):
        from PySide6.QtWidgets import QMessageBox
        d = AddGoalDialog(self, self.db)
        if d.exec():
            name, target, default_account_id = d.get_data()
            if self.db.add_goal(name, target, default_account_id):
                if self.parent() and hasattr(self.parent(), "schedule_update"):
                    self.parent().schedule_update()
            else:
                QMessageBox.warning(self, _("Błąd"), _("Taki cel już istnieje!"))

    def get_data(self):
        try:
            val = float(self.amt.text().replace(",", "."))
        except ValueError:
            val = 0.0

        wallet_name = self.wallet_account_combo.currentText()
        savings_name = self.savings_account_combo.currentText()
        user_details = self.details.toPlainText().strip()

        if self.rw.isChecked():  # WYPŁACAM
            val = -val
            prefix = _("Pobrano z oszczędności na {}. Przesłano na: {}").format(savings_name, wallet_name)
        else:  # WPŁACAM
            prefix = _("Wpłacono z konta: {}. Odłożono na: {}").format(wallet_name, savings_name)

        final_details = f"{prefix}. {user_details}".strip(". ")

        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "type": "savings",
            "cat": _("Oszczędności"),
            "sub": CASH_SAVINGS_NAME,
            "amount": val,
            "details": final_details,
            "attachment": self.attachment_data,
            "account_id": self.wallet_account_combo.currentData(),  # <-- Zwraca zawsze odpowiednie konto z salda
        }

    def accept(self):
        from PySide6.QtWidgets import QMessageBox
        try:
            val = float(self.amt.text().replace(",", "."))
        except ValueError:
            val = 0.0

        wallet_id = self.wallet_account_combo.currentData()
        savings_id = self.savings_account_combo.currentData()

        if wallet_id != savings_id:
            if val <= 0:
                QMessageBox.warning(self, _("Błąd"), _("Podaj poprawną kwotę"))
                return

            try:
                if self.rd.isChecked():  # Wpłata na oszczędności
                    from_id = wallet_id
                    to_id = savings_id
                else:  # Wypłata z oszczędności
                    from_id = savings_id
                    to_id = wallet_id

                if self.db.transfer_savings(from_id, to_id, val, CASH_SAVINGS_NAME):
                    super().accept()
                else:
                    raise Exception(_("Nie udało się przeprowadzić transferu"))
            except Exception as e:
                QMessageBox.critical(self, _("Błąd"), str(e))
        else:
            super().accept()

class GoalOperationDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Wpłata / Wypłata Celu"))
        self.resize(450, 410)

        layout = QFormLayout(self)

        self.rd = QRadioButton(_("Wpłacam na cel"))
        self.rw = QRadioButton(_("Wypłacam z celu"))
        self.rd.setChecked(True)
        h_dir = QHBoxLayout()
        h_dir.addWidget(self.rd)
        h_dir.addWidget(self.rw)

        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)

        self.goal_combo = QComboBox()
        for goal_id, name, target, default_account_id in self.db.get_goals_with_details():
            self.goal_combo.addItem(name, {
                "id": goal_id,
                "target": target,
                "default_account_id": default_account_id
            })

        self.goal_info = QLabel()
        self.goal_info.setStyleSheet("font-size: 10px; color: gray; font-style: italic;")

        self.lbl_account = QLabel(_("Z konta (Portfel):"))
        self.account_combo = QComboBox()
        for acc_id, name, bal, acc_color in self.db.get_accounts():
            self.account_combo.addItem(name, acc_id)

        self.amt = QLineEdit()
        self.amt.setPlaceholderText("0.00")
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator
        self.amt.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.,]*"), self))

        self.details = QTextEdit()
        self.details.setPlaceholderText(_("Dodatkowy opis (opcjonalnie)..."))
        self.details.setMaximumHeight(60)

        self.attachment_data = None
        self.btn_attach = QPushButton(_("📎 Załącznik"))
        self.btn_attach.setStyleSheet("""
            QPushButton { border: 1px solid #95a5a6; border-radius: 6px; padding: 3px; font-size: 11px; min-height: 22px; }
            QPushButton[attached="true"] { background-color: #2ecc71; color: white; border-color: #27ae60; }
        """)
        self.btn_attach.clicked.connect(self.select_attachment)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_save = bb.button(QDialogButtonBox.Save)
        btn_cancel = bb.button(QDialogButtonBox.Cancel)

        main_btn_base = "QPushButton { font-size: 12px; font-weight: bold; padding: 2px 15px; border-radius: 6px; border: 2px solid; background-color: transparent; min-height: 22px; }"
        btn_save.setText(_("Zatwierdź"))
        btn_save.setStyleSheet(main_btn_base + "QPushButton { color: #2980b9; border-color: #3498db; } QPushButton:hover { background-color: #2980b9; color: white; }")
        btn_cancel.setText(_("Anuluj"))
        btn_cancel.setStyleSheet(main_btn_base + "QPushButton { color: #7f8c8d; border-color: #95a5a6; } QPushButton:hover { background-color: #7f8c8d; color: white; }")

        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)

        layout.addRow(_("Operacja:"), h_dir)
        layout.addRow(_("Data:"), self.date)
        layout.addRow(_("Cel:"), self.goal_combo)
        layout.addRow("", self.goal_info)
        layout.addRow(self.lbl_account, self.account_combo)
        layout.addRow(_("Kwota:"), self.amt)
        layout.addRow(_("Szczegóły:"), self.details)
        layout.addRow(_("Dokument:"), self.btn_attach)
        layout.addRow(bb)

        self.rd.toggled.connect(self.update_labels)
        self.goal_combo.currentIndexChanged.connect(self.sync_default_account)
        self.goal_combo.currentIndexChanged.connect(self.update_goal_info)
        self.update_labels()
        self.sync_default_account()
        self.update_goal_info()

    def select_attachment(self):
        from PySide6.QtWidgets import QFileDialog
        dialog = QFileDialog(self)
        dialog.setWindowTitle(_("Wybierz potwierdzenie"))
        dialog.setDirectory("")
        dialog.setNameFilters(["Pliki (*.jpg *.png *.pdf)"])
        dialog.setFileMode(QFileDialog.ExistingFile)

        # Wymuszamy natywne okno systemowe
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)

        path = ""
        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]
        if path:
            try:
                with open(path, "rb") as f:
                    self.attachment_data = f.read()
                self.btn_attach.setText(_("✅ Załączono"))
                self.btn_attach.setProperty("attached", True)
                self.btn_attach.style().unpolish(self.btn_attach)
                self.btn_attach.style().polish(self.btn_attach)
            except Exception as e:
                print(f"Błąd pliku: {e}")

    def update_labels(self):
        if self.rd.isChecked():
            self.lbl_account.setText(_("Z konta (Portfel):"))
        else:
            self.lbl_account.setText(_("Na konto (Portfel):"))

    def sync_default_account(self):
        goal_data = self.goal_combo.currentData()
        if not goal_data:
            return

        default_account_id = goal_data.get("default_account_id")
        if default_account_id is None:
            return

        idx = self.account_combo.findData(default_account_id)
        if idx >= 0:
            self.account_combo.setCurrentIndex(idx)

    def update_goal_info(self):
        goal_data = self.goal_combo.currentData()
        if not goal_data:
            self.goal_info.clear()
            return

        goal_name = self.goal_combo.currentText()
        collected = self.db.get_goal_total(goal_name, goal_id=goal_data["id"])
        target = goal_data["target"] or 0.0
        self.goal_info.setText(_("Stan celu: {:.2f} / {:.2f} zł").format(collected, target))

    def accept(self):
        from PySide6.QtWidgets import QMessageBox
        try:
            val_str = self.amt.text().replace(",", ".").strip()
            if not val_str:
                raise ValueError
            val = float(val_str)
            if val <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, _("Błąd"), _("Podaj poprawną kwotę!"))
            return

        goal_data = self.goal_combo.currentData()
        if not goal_data:
            QMessageBox.warning(self, _("Błąd"), _("Najpierw dodaj cel."))
            return

        if self.rw.isChecked():
            goal_name = self.goal_combo.currentText()
            available = self.db.get_goal_total(goal_name, goal_id=goal_data["id"])
            if val > available:
                QMessageBox.warning(
                    self,
                    _("Błąd kwoty"),
                    _("Nie możesz wypłacić {:.2f} zł, ponieważ w celu '{}' masz tylko {:.2f} zł.").format(val, goal_name, available)
                )
                return

        super().accept()

    def get_data(self):
        val = float(self.amt.text().replace(",", "."))
        goal_name = self.goal_combo.currentText()
        goal_data = self.goal_combo.currentData()
        account_name = self.account_combo.currentText()
        user_details = self.details.toPlainText().strip()

        if self.rw.isChecked():
            signed_amount = -val
            prefix = _("Wypłacono z celu '{}' na konto: {}").format(goal_name, account_name)
        else:
            signed_amount = val
            prefix = _("Wpłacono na cel '{}' z konta: {}").format(goal_name, account_name)

        final_details = f"{prefix}. {user_details}".strip(". ")

        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "type": "goal_deposit",
            "cat": _("Cele"),
            "sub": goal_name,
            "amount": signed_amount,
            "details": final_details,
            "attachment": self.attachment_data,
            "ref_id": goal_data["id"] if goal_data else None,
            "account_id": self.account_combo.currentData()
        }

class TransferDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager # Zachowujemy db_manager
        self.setWindowTitle(_("Transfer"))
        self.resize(350, 250) # Zwiększona wysokość na pole konta
        l=QFormLayout(self)

        # --- NOWE: Wybór Konta (na którym koncie robimy przesunięcie celów) ---
        self.account_combo = QComboBox()
        for acc_id, name, bal, acc_color in self.db.get_accounts():
            self.account_combo.addItem(name, acc_id)
        # ---------------------------------------------------------------------

        self.cf=QComboBox()
        self.ct=QComboBox()
        from config import CASH_SAVINGS_NAME # Upewnij się, że masz import
        i=[CASH_SAVINGS_NAME] + self.db.get_goals()
        self.cf.addItems(i)
        self.ct.addItems(i)
        self.amt=QLineEdit()

        # --- DODANY WALIDATOR (BLOKADA TEKSTU) ---
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator
        self.amt.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.,]*"), self))
        # ----------------------------------------

        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)

        l.addRow(_("Konto bankowe:"), self.account_combo) # <-- DODANE
        l.addRow(_("Z (cel):"), self.cf)
        l.addRow(_("Do (cel):"), self.ct)
        l.addRow(_("Kwota:"), self.amt)
        l.addRow(bb)

    def get_data(self):
        # Pobieranie danych z wymianą separatora dla float()
        try:
            amt_val = float(self.amt.text().replace(",", "."))
        except ValueError:
            amt_val = 0.0

        # Zwracamy: Źródło, Cel, Kwota, ID Konta
        return self.cf.currentText(), self.ct.currentText(), amt_val, self.account_combo.currentData()

class LiabilitiesDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Zarządzaj Długami"))
        self.resize(450, 400) # Zwiększona wysokość na nowe pole
        self.layout = QVBoxLayout(self)

        # Selektor trybu (RadioButtons)
        self.tabs = QButtonGroup(self)
        self.rb_new = QRadioButton(_("Nowe Zobowiązanie"))
        self.rb_pay = QRadioButton(_("Spłata (Oddaję)"))
        self.rb_new.setChecked(True)
        self.tabs.addButton(self.rb_new)
        self.tabs.addButton(self.rb_pay)
        self.rb_new.toggled.connect(self.toggle_mode)

        h_tabs = QHBoxLayout()
        h_tabs.addWidget(self.rb_new)
        h_tabs.addWidget(self.rb_pay)
        self.layout.addLayout(h_tabs)

        # Formularz
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.layout.addWidget(self.form_widget)

        # --- NOWE: Wybór Konta ---
        self.lbl_acc = QLabel(_("Konto bankowe:"))
        self.account_combo = QComboBox()
        for acc_id, name, bal, acc_color in self.db.get_accounts():
            self.account_combo.addItem(name, acc_id)
        # -------------------------

        self.lbl_n = QLabel(_("Komu (Nazwa):"))
        self.n = QLineEdit()
        self.lbl_c = QLabel(_("Wybierz dług:"))
        self.c = QComboBox()
        self.a = QLineEdit()
        self.a.setPlaceholderText("0.00")

        # --- DODANY WALIDATOR (BLOKADA TEKSTU) ---
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator
        self.a.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.,]*"), self))
        # ----------------------------------------

        self.d = QDateEdit(QDate.currentDate())
        self.d.setCalendarPopup(True)
        self.lbl_deadline = QLabel(_("Termin zwrotu:"))

        # --- SEKCOJA ZAŁĄCZNIKA ---
        self.attachment_data = None
        self.btn_attach = QPushButton(_("📎 Załącznik"))
        self.btn_attach.setStyleSheet("""
            QPushButton { border: 1px solid #95a5a6; border-radius: 6px; padding: 3px; font-size: 11px; min-height: 22px; }
            QPushButton[attached="true"] { background-color: #2ecc71; color: white; border-color: #27ae60; }
        """)
        self.btn_attach.clicked.connect(self.select_attachment)

        # Układanie pól w formularzu
        self.form_layout.addRow(self.lbl_acc, self.account_combo) # <-- DODANE na górze
        self.form_layout.addRow(self.lbl_n, self.n)
        self.form_layout.addRow(self.lbl_c, self.c)
        self.form_layout.addRow(_("Kwota:"), self.a)
        self.form_layout.addRow(self.lbl_deadline, self.d)
        self.form_layout.addRow(_("Dokument:"), self.btn_attach)

        # --- STYLIZACJA PRZYCISKÓW GŁÓWNYCH ---
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_save = self.buttons.button(QDialogButtonBox.Save)
        btn_cancel = self.buttons.button(QDialogButtonBox.Cancel)

        main_btn_base = """
            QPushButton {
                font-size: 12px; font-weight: bold; padding: 2px 15px; border-radius: 6px;
                border: 2px solid; background-color: transparent; min-height: 22px; max-height: 22px;
            }
        """

        btn_save.setText(_("Zatwierdź"))
        btn_save.setStyleSheet(main_btn_base + """
            QPushButton { color: #d35400; border-color: #e67e22; }
            QPushButton:hover { background-color: #d35400; color: #ffffff; }
        """)

        btn_cancel.setText(_("Anuluj"))
        btn_cancel.setStyleSheet(main_btn_base + """
            QPushButton { color: #7f8c8d; border-color: #95a5a6; }
            QPushButton:hover { background-color: #7f8c8d; color: #ffffff; }
        """)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.toggle_mode()

    def select_attachment(self):
        from PySide6.QtWidgets import QFileDialog
        from config import _
        dialog = QFileDialog(self)
        dialog.setWindowTitle(_("Wybierz potwierdzenie"))
        dialog.setDirectory("")
        dialog.setNameFilters(["Pliki (*.jpg *.png *.pdf)"])
        dialog.setFileMode(QFileDialog.ExistingFile)

        # Wymuszamy natywne okno systemowe
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)

        path = ""
        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]
        if path:
            try:
                with open(path, "rb") as f:
                    self.attachment_data = f.read()
                self.btn_attach.setText(_("✅ Załączono"))
                self.btn_attach.setProperty("attached", True)
                self.btn_attach.style().unpolish(self.btn_attach)
                self.btn_attach.style().polish(self.btn_attach)
            except Exception as e:
                print(f"Błąd czytania pliku: {e}")

    def toggle_mode(self):
        is_new = self.rb_new.isChecked()
        self.lbl_n.setVisible(is_new)
        self.n.setVisible(is_new)
        self.lbl_c.setVisible(not is_new)
        self.c.setVisible(not is_new)

        if is_new:
            self.lbl_acc.setText(_("Pieniądze wpłynęły na:"))
            self.a.setPlaceholderText(_("Całkowita kwota do oddania"))
            self.lbl_deadline.setText(_("Termin zwrotu:"))
            self.d.setDate(QDate.currentDate().addMonths(1))
        else:
            self.lbl_acc.setText(_("Spłacam z konta:"))
            self.a.setPlaceholderText(_("Kwota wpłaty"))
            self.lbl_deadline.setText(_("Data wpłaty:"))
            self.d.setDate(QDate.currentDate())
            self.refresh_combo()

    def refresh_combo(self):
        self.c.clear()
        active_liabilities = self.db.get_active_liabilities_detailed()
        for l_id, name, remaining in active_liabilities:
            display_text = f"{name} (do spłaty: {remaining:.2f} zł)"
            self.c.addItem(display_text, l_id)

    def accept(self):
        from PySide6.QtWidgets import QMessageBox
        try:
            float(self.a.text().replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, _("Błąd"), _("Podaj poprawną kwotę!")); return

        if self.rb_new.isChecked():
            if not self.n.text().strip():
                QMessageBox.warning(self, _("Błąd"), _("Podaj nazwę wierzyciela!")); return
        else:
            if self.c.count() == 0:
                QMessageBox.warning(self, _("Błąd"), _("Brak aktywnych długów do spłaty!")); return

        super().accept()

    def get_data(self):
        amt_str = self.a.text().replace(",", ".")
        amt = float(amt_str) if amt_str else 0.0

        if self.rb_new.isChecked():
            return {
                "mode": "new",
                "name": self.n.text().strip(),
                "amount": amt,
                "deadline": self.d.date().toString("yyyy-MM-dd"),
                "attachment": self.attachment_data,
                "account_id": self.account_combo.currentData() # <-- DODANE
            }
        else:
            return {
                "mode": "pay",
                "ref_id": self.c.currentData(),
                "name": self.c.currentText().split(" (")[0],
                "amount": amt,
                "date": self.d.date().toString("yyyy-MM-dd"),
                "attachment": self.attachment_data,
                "account_id": self.account_combo.currentData() # <-- DODANE
            }



class DebtorsDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Zarządzaj Dłużnikami"))
        self.resize(450, 400) # Zwiększona wysokość na nowe pole
        self.layout = QVBoxLayout(self)

        # Selektor trybu
        self.tabs = QButtonGroup(self)
        self.rb_new = QRadioButton(_("Nowy Dłużnik (Pożyczam komuś)"))
        self.rb_pay = QRadioButton(_("Zwrot (Oddaje mi)"))
        self.rb_new.setChecked(True)
        self.tabs.addButton(self.rb_new)
        self.tabs.addButton(self.rb_pay)
        self.rb_new.toggled.connect(self.toggle_mode)

        h_tabs = QHBoxLayout()
        h_tabs.addWidget(self.rb_new)
        h_tabs.addWidget(self.rb_pay)
        self.layout.addLayout(h_tabs)

        # Formularz
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.layout.addWidget(self.form_widget)

        # --- NOWE: Wybór Konta ---
        self.lbl_acc = QLabel(_("Konto bankowe:"))
        self.account_combo = QComboBox()
        for acc_id, name, bal, acc_color in self.db.get_accounts():
            self.account_combo.addItem(name, acc_id)
        # -------------------------

        self.lbl_n = QLabel(_("Komu (Nazwa):"))
        self.n = QLineEdit()
        self.lbl_c = QLabel(_("Wybierz dłużnika:"))
        self.c = QComboBox()
        self.a = QLineEdit()
        self.a.setPlaceholderText("0.00")

        # --- DODANY WALIDATOR (BLOKADA TEKSTU) ---
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator
        self.a.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.,]*"), self))
        # ----------------------------------------

        self.d = QDateEdit(QDate.currentDate())
        self.d.setCalendarPopup(True)
        self.lbl_deadline = QLabel(_("Planowany zwrot:"))

        # --- SEKCOJA ZAŁĄCZNIKA ---
        self.attachment_data = None
        self.btn_attach = QPushButton(_("📎 Załącznik"))
        self.btn_attach.setStyleSheet("""
            QPushButton { border: 1px solid #95a5a6; border-radius: 6px; padding: 3px; font-size: 11px; min-height: 22px; }
            QPushButton[attached="true"] { background-color: #2ecc71; color: white; border-color: #27ae60; }
        """)
        self.btn_attach.clicked.connect(self.select_attachment)

        # Układanie w formularzu
        self.form_layout.addRow(self.lbl_acc, self.account_combo) # <-- DODANE na górze
        self.form_layout.addRow(self.lbl_n, self.n)
        self.form_layout.addRow(self.lbl_c, self.c)
        self.form_layout.addRow(_("Kwota:"), self.a)
        self.form_layout.addRow(self.lbl_deadline, self.d)
        self.form_layout.addRow(_("Dokument:"), self.btn_attach)

        # --- STYLIZACJA PRZYCISKÓW GŁÓWNYCH ---
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_save = self.buttons.button(QDialogButtonBox.Save)
        btn_cancel = self.buttons.button(QDialogButtonBox.Cancel)

        main_btn_base = """
            QPushButton {
                font-size: 12px; font-weight: bold; padding: 2px 15px; border-radius: 6px;
                border: 2px solid; background-color: transparent; min-height: 22px; max-height: 22px;
            }
        """

        btn_save.setText(_("Zatwierdź"))
        btn_save.setStyleSheet(main_btn_base + """
            QPushButton { color: #d35400; border-color: #e67e22; }
            QPushButton:hover { background-color: #d35400; color: #ffffff; }
        """)

        btn_cancel.setText(_("Anuluj"))
        btn_cancel.setStyleSheet(main_btn_base + """
            QPushButton { color: #7f8c8d; border-color: #95a5a6; }
            QPushButton:hover { background-color: #7f8c8d; color: #ffffff; }
        """)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.toggle_mode()

    def select_attachment(self):
        from PySide6.QtWidgets import QFileDialog
        from config import _
        dialog = QFileDialog(self)
        dialog.setWindowTitle(_("Wybierz potwierdzenie"))
        dialog.setDirectory("")
        dialog.setNameFilters(["Pliki (*.jpg *.png *.pdf)"])
        dialog.setFileMode(QFileDialog.ExistingFile)

        # Wymuszamy natywne okno systemowe
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)

        path = ""
        _filter = ""
        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]
                _filter = dialog.selectedNameFilter()
        if path:
            try:
                with open(path, "rb") as f:
                    self.attachment_data = f.read()
                self.btn_attach.setText(_("✅ Załączono"))
                self.btn_attach.setProperty("attached", True)
                self.btn_attach.style().unpolish(self.btn_attach)
                self.btn_attach.style().polish(self.btn_attach)
            except Exception as e:
                print(f"Błąd czytania pliku: {e}")

    def toggle_mode(self):
        is_new = self.rb_new.isChecked()
        self.lbl_n.setVisible(is_new)
        self.n.setVisible(is_new)
        self.lbl_c.setVisible(not is_new)
        self.c.setVisible(not is_new)

        if is_new:
            self.lbl_acc.setText(_("Płacę dłużnikowi z konta:"))
            self.a.setPlaceholderText(_("Ile pożyczasz"))
            self.lbl_deadline.setText(_("Planowany zwrot:"))
            self.d.setDate(QDate.currentDate().addMonths(1))
        else:
            self.lbl_acc.setText(_("Zwrot wpływa na konto:"))
            self.a.setPlaceholderText(_("Ile oddał"))
            self.lbl_deadline.setText(_("Data otrzymania zwrotu:"))
            self.d.setDate(QDate.currentDate())
            self.refresh_combo()

    def refresh_combo(self):
        self.c.clear()
        active_debtors = self.db.get_active_debtors_detailed()
        for d_id, name, remaining in active_debtors:
            display_text = f"{name} (zostało: {remaining:.2f} zł)"
            self.c.addItem(display_text, d_id)

    def accept(self):
        from PySide6.QtWidgets import QMessageBox
        try:
            val_str = self.a.text().replace(",", ".").strip()
            if not val_str: raise ValueError
            float(val_str)
        except ValueError:
            QMessageBox.warning(self, _("Błąd"), _("Podaj poprawną kwotę!")); return

        if self.rb_new.isChecked():
            if not self.n.text().strip():
                QMessageBox.warning(self, _("Błąd"), _("Podaj nazwę dłużnika!")); return
        else:
            if self.c.count() == 0:
                QMessageBox.warning(self, _("Błąd"), _("Brak aktywnych dłużników!")); return

        super().accept()

    def get_data(self):
        amt_str = self.a.text().replace(",", ".")
        amt = float(amt_str) if amt_str else 0.0

        if self.rb_new.isChecked():
            return {
                "mode": "new",
                "name": self.n.text().strip(),
                "amount": amt,
                "deadline": self.d.date().toString("yyyy-MM-dd"),
                "attachment": self.attachment_data,
                "account_id": self.account_combo.currentData() # <-- DODANE
            }
        else:
            selected_id = self.c.currentData()
            full_text = self.c.currentText()
            clean_name = full_text.split(" (")[0] if " (" in full_text else full_text

            return {
                "mode": "pay",
                "ref_id": selected_id,
                "name": clean_name,
                "amount": amt,
                "date": self.d.date().toString("yyyy-MM-dd"),
                "attachment": self.attachment_data,
                "account_id": self.account_combo.currentData() # <-- DODANE
            }

class FilterDialog(QDialog):
    def __init__(self, parent, cats, curr):
        super().__init__(parent)
        self.setWindowTitle(_("Filtr"))
        l=QVBoxLayout(self)
        self.c=QComboBox()
        self.c.addItem(_("--- Wszystkie ---"))
        self.c.addItems(sorted(cats))
        if curr: self.c.setCurrentText(curr)
        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        l.addWidget(QLabel(_("Kategoria:")))
        l.addWidget(self.c)
        l.addWidget(bb)
        self.selected_category=None

    def accept(self):
        t=self.c.currentText()
        self.selected_category = t if t != _("--- Wszystkie ---") else None
        super().accept()

class ReportSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Raport"))
        l=QVBoxLayout(self)
        self.rm=QRadioButton(_("Miesiąc"))
        self.ry=QRadioButton(_("Rok"))
        self.rm.setChecked(True)
        l.addWidget(self.rm); l.addWidget(self.ry)
        h=QHBoxLayout()
        self.cm=QComboBox()
        self.cm.addItems(MONTH_NAME)
        self.cy=QSpinBox()
        self.cy.setRange(2020, 2050)
        self.cy.setValue(QDate.currentDate().year())
        h.addWidget(self.cm); h.addWidget(self.cy)
        l.addLayout(h)
        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        l.addWidget(bb)
        self.selected_type="month"
        self.selected_month_str=""
        self.selected_year_str=""
        self.selected_month_name=""

    def accept(self):
        y=str(self.cy.value())
        self.selected_year_str=y
        if self.rm.isChecked():
            self.selected_type="month"
            idx=self.cm.currentIndex()+1
            self.selected_month_str=f"{y}-{idx:02d}"
            self.selected_month_name=self.cm.currentText()
        else: self.selected_type="year"
        super().accept()

class EditDialog(QDialog):
    def __init__(self, parent, data, db):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(_("Edycja transakcji"))
        self.resize(450, 530)  # Zwiększona wysokość na przycisk załącznika

        l = QFormLayout(self)

        # Dane wejściowe: tid=0, date=1, type=2, cat=3, sub=4, amount=5, details=6, has_file=7
        self.d = QDateEdit(QDate.fromString(data[1], "yyyy-MM-dd"))
        self.d.setCalendarPopup(True)

        self.c = QComboBox()
        self.c.setEditable(True)
        if data[2] == 'expense':
            self.c.addItems(self.db.get_categories())
        elif data[2] == 'income':
            self.c.addItems(self.db.get_people())
        else:
            self.c.addItem(data[3])
            self.c.setEnabled(False)
        self.c.setCurrentText(data[3])

        self.s = QLineEdit()
        self.s.setText(data[4])

        # --- NOWE: Wybór Konta ---
        self.lbl_acc = QLabel(_("Konto bankowe:"))
        self.account_combo = QComboBox()
        for acc_id, name, bal, acc_color in self.db.get_accounts():
            self.account_combo.addItem(name, acc_id)

        # Ustawiamy domyślne konto edytowanej transakcji (data[8] to account_id)
        if len(data) > 8 and data[8] is not None:
            current_acc_id = int(data[8])
            index = self.account_combo.findData(current_acc_id)
            if index >= 0:
                self.account_combo.setCurrentIndex(index)
        # -------------------------

        # --- Szczegóły jako QTextEdit ---
        self.det = QTextEdit()
        self.det.setText(data[6] if len(data) > 6 else "")
        self.det.setFixedHeight(80)
        self.det.setTabChangesFocus(True)

        self.a = QLineEdit(str(data[5]))

        # --- DODANY WALIDATOR (BLOKADA TEKSTU) ---
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QRegularExpressionValidator
        self.a.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.,]*"), self))
        # ----------------------------------------

        # --- SEKCJA ZAŁĄCZNIKA ---
        self.attachment_data = None
        self.btn_attach = QPushButton(_("📎 Załącznik"))
        self.btn_attach.setStyleSheet("""
            QPushButton {
                font-size: 11px; border: 1px solid #95a5a6; border-radius: 6px;
                padding: 4px; min-height: 22px; background-color: transparent;
            }
            QPushButton[attached="true"] {
                background-color: #2ecc71; color: white; border-color: #27ae60; font-weight: bold;
            }
        """)
        self.btn_attach.clicked.connect(self.select_attachment)

        # Sprawdzamy czy transakcja już posiada załącznik (8. element w danych z SQL)
        if len(data) > 7 and data[7]:
            self.btn_attach.setText(_("✅ Załącznik obecny"))
            self.btn_attach.setProperty("attached", True)

        # --- PRZYCISKI GŁÓWNYCH ---
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_save = bb.button(QDialogButtonBox.Save)
        btn_cancel = bb.button(QDialogButtonBox.Cancel)

        btn_base_style = """
            QPushButton {
                font-size: 12px; font-weight: bold; padding: 2px 15px; border-radius: 6px;
                border: 2px solid; background-color: transparent; min-height: 22px; max-height: 22px;
            }
        """

        btn_save.setText(_("Zapisz zmiany"))
        btn_save.setStyleSheet(btn_base_style + """
            QPushButton { color: #2980b9; border-color: #3498db; }
            QPushButton:hover { background-color: #2980b9; color: #ffffff; }
        """)

        btn_cancel.setText(_("Anuluj"))
        btn_cancel.setStyleSheet(btn_base_style + """
            QPushButton { color: #7f8c8d; border-color: #95a5a6; }
            QPushButton:hover { background-color: #7f8c8d; color: #ffffff; }
        """)

        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)

        # Układ formularza
        l.addRow(_("Data:"), self.d)
        l.addRow(_("Konto:"), self.account_combo)
        l.addRow(_("Kategoria:"), self.c)
        l.addRow(_("Opis (Sklep):"), self.s)
        l.addRow(_("Szczegóły:"), self.det)
        l.addRow(_("Kwota:"), self.a)
        l.addRow(_("Dokument:"), self.btn_attach)
        l.addRow(bb)

    def select_attachment(self):
        from PySide6.QtWidgets import QFileDialog
        from config import _

        # file_ext zamiast _ zapobiega błędom zasięgu
        dialog = QFileDialog(self)
        dialog.setWindowTitle(_("Wybierz potwierdzenie"))
        dialog.setDirectory("")
        dialog.setNameFilters(["Pliki (*.jpg *.png *.pdf)"])
        dialog.setFileMode(QFileDialog.ExistingFile)

        # Wymuszamy natywne okno systemowe
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)

        path = ""
        _filter = ""
        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]
                _filter = dialog.selectedNameFilter()

        if path:
            try:
                with open(path, "rb") as f:
                    self.attachment_data = f.read()
                self.btn_attach.setText(_("✅ Nowy załącznik"))
                self.btn_attach.setProperty("attached", True)
                self.btn_attach.style().unpolish(self.btn_attach)
                self.btn_attach.style().polish(self.btn_attach)
            except Exception as e:
                print(f"Błąd czytania pliku: {e}")

    def get_data(self):
        try:
            amount_val = float(self.a.text().replace(",", "."))
        except ValueError:
            amount_val = 0.0

        return {
            "date": self.d.date().toString("yyyy-MM-dd"),
            "category": self.c.currentText(),
            "subcategory": self.s.text(),
            "amount": amount_val,
            "details": self.det.toPlainText(),
            "attachment": self.attachment_data,
            "account_id": self.account_combo.currentData()
        }

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QComboBox, QPushButton, QTableWidget,
                               QTableWidgetItem, QHeaderView, QGroupBox,
                               QCheckBox, QAbstractItemView, QMessageBox, QDateEdit)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from config import _

class BillsManagerDialog(QDialog):
    def __init__(self, db, categories, parent=None):
        super().__init__(parent)
        self.db = db
        self.categories = categories
        self.setWindowTitle(_("Rachunki i opłaty"))
        self.resize(900, 600)

        self.layout = QVBoxLayout(self)

        # --- DEFINICJA STYLI (Lux Style) ---
        base_style = """
            QPushButton {
                font-size: 11px; font-weight: bold; padding: 5px 15px;
                border-radius: 6px; border: 2px solid; background-color: transparent;
                min-height: 24px;
            }
        """
        inc_style = base_style + """
            QPushButton { color: #27ae60; border-color: #2ecc71; }
            QPushButton:hover { background-color: #27ae60; color: #ffffff; }
        """
        exp_style = base_style + """
            QPushButton { color: #c0392b; border-color: #e74c3c; }
            QPushButton:hover { background-color: #c0392b; color: #ffffff; }
        """
        blue_style = base_style + """
            QPushButton { color: #3498db; border-color: #3498db; }
            QPushButton:hover { background-color: #3498db; color: #ffffff; }
        """

        # --- TABELA RACHUNKÓW ---
        self.table = QTableWidget(0, 6) # Zwiększamy do 6 kolumn dla ukrytego ref_id
        self.table.setHorizontalHeaderLabels([_("ID"), _("Termin"), _("Kwota"), _("Kategoria"), _("Opis"), _("RefID")])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.setColumnHidden(5, True) # Ukryte ID długu
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { border: 1px solid palette(mid); }")

        self.layout.addWidget(QLabel(f"<b>{_('Oczekujące płatności:')}</b>"))
        self.layout.addWidget(self.table)

        # --- FORMULARZ DODAWANIA ---
        form_group = QGroupBox(_("Dodaj nową płatność"))
        form_layout = QHBoxLayout(form_group)

        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setFixedWidth(110)

        self.amt_input = QLineEdit()
        self.amt_input.setPlaceholderText(_("Kwota"))
        self.amt_input.setFixedWidth(80)

        self.cat_input = QComboBox()
        # Dodajemy standardowe kategorie + naszą specjalną opcję
        display_cats = list(self.categories)
        if _("Spłata Długu") not in display_cats:
            display_cats.append(_("Spłata Długu"))
        self.cat_input.addItems(display_cats)
        self.cat_input.currentTextChanged.connect(self.toggle_liability_selector)

        # Combo do wyboru konkretnego długu (domyślnie ukryte)
        self.liability_selector = QComboBox()
        self.liability_selector.setFixedWidth(270)
        self.liability_selector.hide()
        self.refresh_liabilities_list()

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText(_("Opis (np. Czynsz)"))

        self.recurring_cb = QCheckBox(_("Stały"))

        btn_add = QPushButton(_("DODAJ"))
        btn_add.setFixedWidth(80)
        btn_add.setStyleSheet(inc_style)
        btn_add.clicked.connect(self.add_bill)

        form_layout.addWidget(self.date_input)
        form_layout.addWidget(self.amt_input)
        form_layout.addWidget(self.cat_input)
        form_layout.addWidget(self.liability_selector) # Wstawiamy między kategorię a opis
        form_layout.addWidget(self.desc_input)
        form_layout.addWidget(self.recurring_cb)
        form_layout.addWidget(btn_add)
        self.layout.addWidget(form_group)

        # --- PRZYCISKI AKCJI ---
        action_layout = QHBoxLayout()
        self.btn_pay = QPushButton(f"✅ {_('ZAPŁAĆ')}")
        self.btn_pay.setStyleSheet(inc_style)
        self.btn_pay.clicked.connect(self.pay_bill)

        self.btn_delete = QPushButton(f"🗑️ {_('USUŃ')}")
        self.btn_delete.setStyleSheet(exp_style)
        self.btn_delete.clicked.connect(self.delete_bill)

        btn_close = QPushButton(_("ZAMKNIJ"))
        btn_close.setStyleSheet(blue_style)
        btn_close.clicked.connect(self.reject)

        action_layout.addWidget(self.btn_pay)
        action_layout.addWidget(self.btn_delete)
        action_layout.addStretch()
        action_layout.addWidget(btn_close)
        self.layout.addLayout(action_layout)

        self.load_data()

    def refresh_liabilities_list(self):
        """Pobiera aktywne długi do listy wyboru."""
        self.liability_selector.clear()
        status = self.db.get_liabilities_status()
        for d in status:
            rem = d['total'] - d['paid']
            if rem > 0.01:
                # Wyświetlamy nazwę długu i ile zostało
                self.liability_selector.addItem(f"{d['name']} (zost. {rem:.2f})", d['id'])

    def toggle_liability_selector(self, text):
        """Pokazuje wybór długu tylko gdy wybrano kategorię 'Spłata Długu'."""
        is_lia = (text == _("Spłata Długu"))
        self.liability_selector.setVisible(is_lia)
        self.desc_input.setVisible(not is_lia)
        if is_lia:
            self.refresh_liabilities_list()

    def load_data(self):
        self.table.setRowCount(0)
        bills = self.db.get_pending_bills() # Upewnij się, że get_pending_bills zwraca też ref_id (7 kolumn)
        for b in bills:
            # Zakładamy: b_id, d_date, amt, cat, desc, is_rec, ref_id
            b_id, d_date, amt, cat, desc, is_rec = b[:6]
            ref_id = b[6] if len(b) > 6 else None

            row = self.table.rowCount()
            self.table.insertRow(row)

            id_item = QTableWidgetItem(str(b_id))
            id_item.setData(Qt.UserRole, is_rec)
            self.table.setItem(row, 0, id_item)

            date_item = QTableWidgetItem(d_date)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, date_item)

            amt_item = QTableWidgetItem(f"{amt:.2f} PLN")
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, amt_item)

            self.table.setItem(row, 3, QTableWidgetItem(cat))

            desc_text = f"🔄 {desc}" if is_rec == 1 else desc
            self.table.setItem(row, 4, QTableWidgetItem(desc_text))

            ref_item = QTableWidgetItem(str(ref_id) if ref_id else "")
            self.table.setItem(row, 5, ref_item)

    def add_bill(self):
        try:
            amt = float(self.amt_input.text().replace(',', '.'))
            cat = self.cat_input.currentText()
            is_rec = 1 if self.recurring_cb.isChecked() else 0

            if cat == _("Spłata Długu"):
                ref_id = self.liability_selector.currentData()
                desc = self.liability_selector.currentText().split(" (")[0]
            else:
                ref_id = None
                desc = self.desc_input.text().strip()

            self.db.add_pending_bill(
                self.date_input.date().toString("yyyy-MM-dd"),
                amt, cat, desc, is_rec, ref_id=ref_id
            )
            self.amt_input.clear(); self.desc_input.clear(); self.load_data()
        except Exception as e:
            print(f"Błąd dodawania rachunku: {e}")

    def pay_bill(self):
        row = self.table.currentRow()
        if row < 0: return

        b_id = int(self.table.item(row, 0).text())
        is_rec = self.table.item(row, 0).data(Qt.UserRole)
        date_str = self.table.item(row, 1).text()
        amt = float(self.table.item(row, 2).text().replace(" PLN", ""))
        cat = self.table.item(row, 3).text()
        desc = self.table.item(row, 4).text().replace("🔄 ", "")
        ref_id_str = self.table.item(row, 5).text()
        ref_id = int(ref_id_str) if ref_id_str else None

        pay_dlg = BillPaymentConfirmDialog(self, self.db, desc, amt)
        if pay_dlg.exec():
            res = pay_dlg.get_data()
            self.db.mark_bill_paid(b_id)

            # Logika wyboru typu transakcji
            t_type = 'liability_repayment' if cat == _("Spłata Długu") else 'expense'

            # Jeśli to spłata długu, sprawdź czy to ostatnia rata dla dodatkowego opisu
            final_details = res["details"]
            if t_type == 'liability_repayment' and ref_id:
                status = self.db.get_liabilities_status()
                dane_dlugu = next((d for d in status if d['id'] == ref_id), None)
                if dane_dlugu and amt >= (dane_dlugu['total'] - dane_dlugu['paid']):
                    final_details = f"{_('Spłacone w całości')}. {final_details}".strip(". ")

            # Dodanie do historii transakcji
            self.db.add_transaction(
                date=QDate.currentDate().toString("yyyy-MM-dd"),
                t_type=t_type,
                category=cat,
                subcategory=desc,
                amount=amt,
                details=final_details,
                attachment=res["attachment"],
                account_id=res["account_id"],
                ref_id=ref_id # Kluczowe dla zaliczenia spłaty długu!
            )

            if is_rec == 1:
                new_date = QDate.fromString(date_str, "yyyy-MM-dd").addMonths(1).toString("yyyy-MM-dd")
                self.db.add_pending_bill(new_date, amt, cat, desc, 1, ref_id=ref_id)

            self.load_data()

    def delete_bill(self):
        row = self.table.currentRow()
        if row >= 0:
            b_id = int(self.table.item(row, 0).text())
            self.db.delete_pending_bill(b_id)
            self.load_data()

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QHeaderView, QPushButton,
                               QLabel, QLineEdit, QComboBox, QDateEdit, QMessageBox, QAbstractItemView, QCheckBox)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
class BillPaymentConfirmDialog(QDialog):
    def __init__(self, parent, db, desc, amt):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(_("Potwierdzenie płatności"))
        self.setFixedWidth(400)
        layout = QVBoxLayout(self)

        # --- STYLE DLA PRZYCISKÓW DECYZJI ---
        base_style = """
            QPushButton {
                font-size: 11px; font-weight: bold; padding: 5px 15px;
                border-radius: 6px; border: 2px solid; background-color: transparent;
                min-height: 24px;
            }
        """
        inc_style = base_style + """
            QPushButton { color: #27ae60; border-color: #2ecc71; }
            QPushButton:hover { background-color: #27ae60; color: #ffffff; }
        """
        exp_style = base_style + """
            QPushButton { color: #c0392b; border-color: #e74c3c; }
            QPushButton:hover { background-color: #c0392b; color: #ffffff; }
        """

        # Treść pytania
        layout.addWidget(QLabel(f"{_('Czy na pewno opłaciłeś:')} <br><b>{desc}</b> ({amt:.2f} PLN)?"))

        # Sekcja wyboru konta
        layout.addWidget(QLabel(_("Zapłacono z konta:")))
        self.account_combo = QComboBox()
        for acc_id, name, bal, acc_color in self.db.get_accounts():
            self.account_combo.addItem(name, acc_id)
        layout.addWidget(self.account_combo)

        # Pole szczegółów
        self.details_input = QLineEdit()
        self.details_input.setPlaceholderText(_("Szczegóły (opcjonalnie)"))
        layout.addWidget(self.details_input)

        # --- SEKCOJA ZAŁĄCZNIKA (PRZYWRÓCONA DO ORGINAŁU) ---
        self.attachment_data = None
        self.btn_attach = QPushButton(_("📎 Załącznik"))
        self.btn_attach.setStyleSheet("""
            QPushButton {
                border: 1px solid #95a5a6; border-radius: 6px; padding: 3px;
                font-size: 11px; min-height: 22px;
            }
            QPushButton[attached="true"] {
                background-color: #2ecc71; color: white; border-color: #27ae60;
            }
        """)
        self.btn_attach.clicked.connect(self.select_attachment)
        layout.addWidget(self.btn_attach)

        # --- PRZYCISKI DECYZJI ---
        from PySide6.QtWidgets import QDialogButtonBox
        self.buttons = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)

        btn_yes = self.buttons.button(QDialogButtonBox.Yes)
        btn_yes.setText(_("Tak, opłacone"))
        btn_yes.setStyleSheet(inc_style)

        btn_no = self.buttons.button(QDialogButtonBox.No)
        btn_no.setText(_("Anuluj"))
        btn_no.setStyleSheet(exp_style)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def select_attachment(self):
        from PySide6.QtWidgets import QFileDialog
        dialog = QFileDialog(self)
        dialog.setWindowTitle(_("Wybierz potwierdzenie"))
        dialog.setDirectory("")
        dialog.setNameFilters(["Pliki (*.jpg *.png *.pdf)"])
        dialog.setFileMode(QFileDialog.ExistingFile)

        # Wymuszamy natywne okno systemowe
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)

        path = ""
        _filter = ""
        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]
                _filter = dialog.selectedNameFilter()

        if path:
            try:
                with open(path, "rb") as f:
                    self.attachment_data = f.read()

                # Przywrócenie Twojej logiki aktualizacji stylu
                self.btn_attach.setText(_("✅ Załączono"))
                self.btn_attach.setProperty("attached", True)
                self.btn_attach.style().unpolish(self.btn_attach)
                self.btn_attach.style().polish(self.btn_attach)
            except Exception as e:
                print(f"Błąd czytania załącznika: {e}")

    def get_data(self):
        acc_id = self.account_combo.currentData()
        return {
            "details": self.details_input.text().strip(),
            "attachment": self.attachment_data,
            "account_id": acc_id if acc_id is not None else 1
        }

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QWidget, QProgressBar
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QPainter, QPolygon, QColor, QBrush

class GuideArrow(QWidget):
    """Smukły, luksusowy wskaźnik (dziubek) dopasowany do motywu lux."""
    def __init__(self, parent, color="#2c3e50"):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.color = color
        self.setFixedSize(16, 20)
        self.direction_up = True

    def set_direction(self, points_up):
        self.direction_up = points_up
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        triangle = QPolygon()
        if self.direction_up:
            # Wskazuje w górę ▲
            triangle.append(QPoint(self.width() // 2, 0))
            triangle.append(QPoint(1, self.height()))
            triangle.append(QPoint(self.width() - 1, self.height()))
        else:
            # Wskazuje w dół ▼
            triangle.append(QPoint(1, 0))
            triangle.append(QPoint(self.width() - 1, 0))
            triangle.append(QPoint(self.width() // 2, self.height()))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.color)))
        painter.drawPolygon(triangle)


class GuideBubble(QFrame):
    """Elegancki, luksusowy dymek podpowiedzi dopasowany do stylistyki aplikacji."""
    def __init__(self, parent, text, target_widget, on_finish_callback, on_stop_callback):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.target = target_widget
        self.on_finish_callback = on_finish_callback
        self.on_stop_callback = on_stop_callback

        # Strzałka przejmuje luksusowy, ciemnografitowy kolor dymka
        self.arrow = GuideArrow(parent, color="#2c3e50")

        # --- LUKSUSOWA STYLIZACJA (PASUJE DO PRZYCISKÓW LUX) ---
        self.setStyleSheet("""
            GuideBubble {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34495e, stop:1 #2c3e50);
                color: #ecf0f1;
                border-radius: 8px;
                border: 1px solid #7f8c8d;
            }
            QLabel {
                background: transparent;
                font-size: 13px;
                font-weight: 500;
                color: #f3f3f3;
            }
            QPushButton#close_btn {
                background: transparent;
                color: rgba(255,255,255,140);
                font-weight: bold;
                border: none;
                font-size: 11px;
            }
            QPushButton#close_btn:hover {
                color: #e74c3c;
            }
        """)

        # Layout główny
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(12, 10, 12, 12)
        main_lay.setSpacing(6)

        # Pasek górny z przyciskiem X
        top_lay = QHBoxLayout()
        top_lay.setContentsMargins(0, 0, 0, 0)
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(18, 18)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.on_stop_callback)
        top_lay.addStretch()
        top_lay.addWidget(close_btn)
        main_lay.addLayout(top_lay)

        # Treść podpowiedzi
        self.lbl = QLabel(text)
        self.lbl.setWordWrap(True)
        self.lbl.setContentsMargins(5, 0, 5, 5)
        main_lay.addWidget(self.lbl)

        # Smukły pasek postępu (Lux-style progress bar)
        self.progress = QProgressBar(self)
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 30);
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1abc9c, stop:1 #2ecc71);
                border-radius: 2px;
            }
        """)
        main_lay.addWidget(self.progress)

        self.prog_timer = QTimer(self)
        self.prog_value = 0
        self.prog_timer.timeout.connect(self.update_progress)
        self.prog_timer.start(50)

        self.setMinimumWidth(280)
        self.adjustSize()

    def update_progress(self):
        self.prog_value += 1
        if self.prog_value <= 100:
            self.progress.setValue(self.prog_value)
        else:
            self.prog_timer.stop()
            if self.on_finish_callback:
                self.on_finish_callback()

    def show(self):
        super().show()
        self.arrow.show()

    def close(self):
        self.arrow.close()
        super().close()

    def deleteLater(self):
        self.arrow.deleteLater()
        super().deleteLater()

    def move_to_target(self):
        """Prawidłowe pozycjonowanie dymków w 100% lokalnie względem okna rodzica."""
        # MAPOWANIE LOKALNE: Zapobiega rozjeżdżaniu na Windowsie i trybach Full Screen
        local_pos = self.target.mapTo(self.parent(), QPoint(0, 0))
        target_center_x = local_pos.x() + (self.target.width() // 2)

        gap = 2
        arrow_points_up = True
        bubble_y_offset = self.target.height() + self.arrow.height() + gap
        arrow_y_offset = self.target.height() + gap

        # Sprawdzamy, czy dymek nie wychodzi poza dół głównego okna aplikacji
        if local_pos.y() + bubble_y_offset + self.height() > self.parent().height():
            arrow_points_up = False
            # Jeśli się nie mieści na dole, ląduje nad przyciskiem
            bubble_y_offset = -(self.height() + self.arrow.height() + gap)
            arrow_y_offset = -(self.arrow.height() + gap)

        self.arrow.set_direction(arrow_points_up)

        # Precyzyjne pozycjonowanie strzałki w osi X przycisku
        arrow_x = (self.target.width() // 2) - (self.arrow.width() // 2)
        self.arrow.move(local_pos + QPoint(arrow_x, arrow_y_offset))

        # Pozycjonowanie dymka w osi X z uwzględnieniem bezpiecznych marginesów okna aplikacji
        bubble_x = target_center_x - (self.width() // 2)
        margin = 15
        bubble_x = max(margin, min(bubble_x, self.parent().width() - self.width() - margin))
        self.move(QPoint(bubble_x, local_pos.y() + bubble_y_offset))


class AppGuide:
    def __init__(self, parent):
        self.parent = parent
        self.steps = [
            (parent.btn_sel_month, _("1. Wybór daty: Tu określasz, który miesiąc i rok chcesz teraz rozliczać.")),
            (parent.btn_weekly, _("2. Limity: Ustaw ile maksymalnie chcesz wydać w danym tygodniu.")),
            (parent.search_bar, _("3. Wyszukiwarka: Filtruj historię wpisując kwoty, kategorie lub nazwy sklepów.")),
            (parent.btn_income, _("4. Przychody: Tu dodajesz wypłaty, premie i inne wpływy.")),
            (parent.btn_expense, _("5. Wydatki: Twoje codzienne zakupy. Wybierz kategorię, by widzieć statystyki.")),
            (parent.btn_savings, _("6. Oszczędności: Odkładaj na konkretne cele lub fundusz awaryjny.")),
            (parent.btn_liabilities, _("7. Twoje długi: Tutaj pilnujesz spłaty własnych kredytów i pożyczek.")),
            (parent.btn_debtors, _("8. Dłużnicy: Spis osób, które pożyczyły pieniądze od Ciebie.")),
            (parent.btn_bills, _("9. Rachunki: Stałe opłaty jak czynsz czy prąd. Apka przypomni Ci o terminach!")),
            (parent.table, _("10. Rejestr: Tutaj widzisz pełną listę wszystkich operacji w wybranym miesiącu.")),
            (parent.btn_pdf, _("11. Raport: Kliknij tutaj na koniec miesiąca, by stworzyć podsumowanie w PDF.")),
            (parent.btn_back, _("12. Backup: Zawsze rób kopię zapasową bazy danych przed większymi zmianami."))
        ]
        self.current_step = 0
        self.bubble = None

    def start(self):
        self.current_step = 0
        self.show_step()

    def show_step(self):
        if self.bubble:
            self.bubble.close()
            self.bubble.deleteLater()

        if self.current_step < len(self.steps):
            target_widget, text = self.steps[self.current_step]
            self.bubble = GuideBubble(self.parent, text, target_widget, self.next_step, self.stop_guide)
            self.bubble.show()
            self.bubble.move_to_target()

    def next_step(self):
        self.current_step += 1
        QTimer.singleShot(100, self.show_step)

    def stop_guide(self):
        """Całkowite zatrzymanie prezentacji."""
        if self.bubble:
            try:
                # 1. Próba użycia oficjalnego shiboken do walidacji obiektów C++
                if shiboken is not None:
                    if shiboken.isValid(self.bubble):
                        if hasattr(self.bubble, 'prog_timer') and shiboken.isValid(self.bubble.prog_timer):
                            self.bubble.prog_timer.stop() # Zatrzymujemy pasek

                        self.bubble.close()
                        self.bubble.deleteLater()
                # 2. Awaryjny fallback, gdyby shiboken nie był załadowany
                else:
                    self.bubble.parent() # Wywoła RuntimeError jeśli obiekt jest martwy
                    if hasattr(self.bubble, 'prog_timer'):
                        self.bubble.prog_timer.parent()
                        self.bubble.prog_timer.stop()

                    self.bubble.close()
                    self.bubble.deleteLater()

            except (RuntimeError, AttributeError, NameError):
                # Cichy powrót, jeśli C++ usunął obiekty z pamięci przed nami
                pass
            finally:
                self.bubble = None

        self.current_step = 999 # Blokujemy dalsze kroki

class AccountHistoryDialog(QDialog):
    def __init__(self, parent, db, account_id, account_name):
        super().__init__(parent)
        self.db = db
        self.account_id = account_id
        self.setWindowTitle(f"{_('Historia konta')}: {account_name}")
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        # --- FILTRY ---
        filter_layout = QHBoxLayout()

        self.date_from = QDateEdit(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            _("Wszystkie"), _("Wpływy"), _("Wydatki"),
            _("Oszczędności"), _("Spłaty długów"), _("Zwroty od dłużników")
        ])
        # Mapowanie dla bazy danych
        self.type_map = {
            _("Wszystkie"): None,
            _("Wpływy"): "income",
            _("Wydatki"): "expense",
            _("Oszczędności"): "savings",
            _("Spłaty długów"): "liability_repayment",
            _("Zwroty od dłużników"): "debtor_repayment"
        }

        btn_refresh = QPushButton(_("Filtruj"))
        btn_refresh.clicked.connect(self.load_history)

        # Styl spójny z resztą aplikacji (Lux style)
        btn_refresh.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: bold;
                padding: 4px 15px;
                border-radius: 6px;
                border: 2px solid #3498db;
                color: #2980b9;
                background-color: transparent;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #3498db;
                color: #ffffff;
            }
        """)
        btn_refresh.setCursor(Qt.PointingHandCursor) # Dodajemy łapkę

        filter_layout.addWidget(QLabel(_("Od:")))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel(_("Do:")))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(QLabel(_("Typ:")))
        filter_layout.addWidget(self.type_combo)
        filter_layout.addWidget(btn_refresh)
        layout.addLayout(filter_layout)

        # --- TABELA ---
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([_("Data"), _("Kategoria"), _("Opis"), _("Kwota"), _("Szczegóły")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        # --- PODSUMOWANIE ---
        self.lbl_summary = QLabel("")
        self.lbl_summary.setStyleSheet("font-weight: bold; font-size: 13px; color: #2c3e50;")
        layout.addWidget(self.lbl_summary)

        self.load_history()

    def load_history(self):
        from PySide6.QtGui import QColor, QPalette
        d1 = self.date_from.date().toString("yyyy-MM-dd")
        d2 = self.date_to.date().toString("yyyy-MM-dd")
        selected_text = self.type_combo.currentText()
        t_type = self.type_map.get(selected_text)

        rows = self.db.get_account_history(self.account_id, d1, d2, t_type)

        self.table.setRowCount(0)
        total_val = 0.0

        for r in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            self.table.setItem(row_idx, 0, QTableWidgetItem(r[0])) # Data
            self.table.setItem(row_idx, 1, QTableWidgetItem(r[2])) # Kategoria
            self.table.setItem(row_idx, 2, QTableWidgetItem(r[3])) # Opis

            amt = r[4]
            # Kolorowanie kwoty w tabeli
            item_amt = QTableWidgetItem(f"{amt:.2f}")
            if r[1] in ['income', 'debtor_repayment']:
                item_amt.setForeground(QColor("#2ecc71")) # Jaśniejszy zielony dla lepszego kontrastu
                total_val += amt
            else:
                item_amt.setForeground(QColor("#e74c3c")) # Jaśniejszy czerwony
                total_val -= amt

            self.table.setItem(row_idx, 3, item_amt)
            self.table.setItem(row_idx, 4, QTableWidgetItem(r[5] or ""))

        # --- LOGIKA KOLOROWANIA PODSUMOWANIA (BEZ NIEBIESKIEGO NAPISU) ---
        theme_text_color = self.palette().color(QPalette.WindowText).name()

        if total_val > 0.01:
            val_color = "#2ecc71" # Zielony
        elif total_val < -0.01:
            val_color = "#e74c3c" # Czerwony
        else:
            val_color = theme_text_color

        self.lbl_summary.setStyleSheet(f"QLabel {{ color: {theme_text_color}; font-size: 13px; font-weight: bold; }}")

        self.lbl_summary.setText(
            f"{_('Bilans operacji w tym okresie')}: "
            f"<span style='color:{val_color};'>{total_val:.2f} PLN</span>"
        )

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QFrame, QProgressBar, QPushButton, QGroupBox)
from PySide6.QtCore import Qt, QTimer
from forecaster import FinanceForecaster

class ForecastDialog(QDialog):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.db = db_manager
        self.forecaster = FinanceForecaster(db_manager)
        self.setWindowTitle(_("Prognozy Finansowe"))
        self.resize(1000, 750)

        # Słownik na widżety, które będziemy aktualizować dynamicznie
        self.live_widgets = {}

        # 1. Budujemy strukturę raz
        self.setup_ui()

        # 2. Wypełniamy danymi
        self.refresh_data()

        # Timer do odświeżania porad i danych
        self.ai_timer = QTimer(self)
        self.ai_timer.timeout.connect(self.refresh_data)
        self.ai_timer.start(30000) # 30 sekund
        self.btn_what_if.clicked.connect(self.open_what_if_dialog)

    def open_what_if_dialog(self):
        from forecaster import FinanceForecaster

        # Inicjalizujemy forecaster, jeśli jeszcze nie istnieje
        if not hasattr(self, 'forecaster') or self.forecaster is None:
            self.forecaster = FinanceForecaster(self.db)

        dlg = WhatIfDialog(self, self.db, self.forecaster)
        dlg.exec_()

    def setup_ui(self):
        # Główny layout
        self.main_layout = QVBoxLayout(self)

        # --- GÓRA: KAFELKI ---
        self.top_layout = QHBoxLayout()
        self.card_bal = self._create_kpi_card(_("PROGNOZOWANE SALDO"))
        self.card_health = self._create_kpi_card(_("ZDROWIE FINANSOWE"))
        self.card_days = self._create_kpi_card(_("ZEROWE SALDO ZA:"))

        self.top_layout.addWidget(self.card_bal)
        self.top_layout.addWidget(self.card_health)
        self.top_layout.addWidget(self.card_days)
        self.main_layout.addLayout(self.top_layout)

        # --- ŚRODEK ---
        self.mid_layout = QHBoxLayout()

        # Sekcja kategorii
        self.cat_box = QGroupBox(_("Estymacja wydatków do końca miesiąca"))
        self.cat_v = QVBoxLayout(self.cat_box)
        self.mid_layout.addWidget(self.cat_box, 2)

        # Sekcja porad AI
        self.alert_box = QGroupBox(_("Analiza i Sugestie"))
        self.alert_v = QVBoxLayout(self.alert_box)
        self.mid_layout.addWidget(self.alert_box, 1)

        self.main_layout.addLayout(self.mid_layout)

        # --- DÓŁ ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)  # Odstęp między przyciskami

        # 1. Przycisk Symulacji (lewa strona)
        self.btn_what_if = QPushButton(_("🚀 SYMULACJA 'CO JEŚLI'"))
        self.btn_what_if.setCursor(Qt.PointingHandCursor)
        self.btn_what_if.setStyleSheet("""
            QPushButton {
                border: 2px solid #3498db; color: #3498db; font-weight: bold;
                padding: 15px; border-radius: 10px; font-size: 14px; background: transparent;
            }
            QPushButton:hover { background: #3498db; color: white; }
        """)

        # 2. Przycisk Zamknij (prawa strona)
        self.btn_close = QPushButton(_("Zamknij"))
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                border: 2px solid #7f8c8d; color: #7f8c8d; font-weight: bold;
                padding: 15px; border-radius: 10px; font-size: 14px; background: transparent;
            }
            QPushButton:hover { background: #7f8c8d; color: white; }
        """)
        # Podpięcie zamknięcia okna dialogowego
        self.btn_close.clicked.connect(self.accept)

        # Dodanie do poziomego układu
        bottom_layout.addWidget(self.btn_what_if)
        bottom_layout.addWidget(self.btn_close)

        # Dodanie całości do głównego układu pionowego
        self.main_layout.addLayout(bottom_layout)

    def refresh_data(self):
        data = self.forecaster.get_predictions()
        self.setUpdatesEnabled(False)  # Zapobiega migotaniu interfejsu podczas zmian

        try:
            # 1. PROGNOZOWANE SALDO
            bal_lbl = self.card_bal.findChild(QLabel, "val_lbl")
            projected = data['projected_end_month']
            bal_lbl.setText(f"{projected:.2f} zł")

            # Kolorowanie: zielony dla plusa, czerwony dla minusa
            bal_color = "#2ecc71" if projected > 0 else "#e74c3c"
            bal_lbl.setStyleSheet(f"color: {bal_color}; font-size: 24px; font-weight: bold;")
            bal_lbl.setToolTip(f"<span style='font-size: 11px;'>{_('Suma obecnego salda, przewidywanych wpływów i rachunków do opłacenia.')}</span>")

            # Dynamiczny podpis pod kafelkiem salda
            bal_sub = self.card_bal.findChild(QLabel, "sub_lbl")
            if not bal_sub:
                bal_sub = QLabel(self.card_bal)
                bal_sub.setObjectName("sub_lbl")
                bal_sub.setAlignment(Qt.AlignCenter)
                self.card_bal.layout().addWidget(bal_sub)

            bal_sub.setText(_("tyle powinno zostać na koniec m-ca"))
            bal_sub.setStyleSheet("color: gray; font-size: 11px;")

            # 2. HEALTH SCORE
            health_lbl = self.card_health.findChild(QLabel, "val_lbl")
            health_lbl.setText(f"{data['health_score']}/100")
            health_lbl.setToolTip(f"<span style='font-size: 11px;'>{_('Wskaźnik oparty na relacji oszczędności do wydatków i terminowości rachunków.')}</span>")

            # 3. BEZPIECZNY MARGINES
            days_to_zero = data['days_to_zero']
            days_lbl = self.card_days.findChild(QLabel, "val_lbl")
            days_sub = self.card_days.findChild(QLabel, "sub_lbl")

            if not days_sub:
                days_sub = QLabel(self.card_days)
                days_sub.setObjectName("sub_lbl")
                days_sub.setAlignment(Qt.AlignCenter)
                self.card_days.layout().addWidget(days_sub)

            if days_to_zero >= 999:
                days_lbl.setText("∞")
                days_lbl.setStyleSheet("color: #2ecc71; font-size: 24px; font-weight: bold;")
                days_sub.setText(_("pełne bezpieczeństwo"))
            else:
                days_lbl.setText(f"{days_to_zero} dni")
                # Kolorowanie progresywne
                if days_to_zero < 3: color = "#e74c3c"
                elif days_to_zero < 7: color = "#e67e22"
                else: color = "#95a5a6"
                days_lbl.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")

                if days_to_zero == 0:
                    days_sub.setText(_("brak środków na dziś"))
                else:
                    days_sub.setText(_("średnio na tyle dni wystarczy"))

            days_sub.setStyleSheet("color: gray; font-size: 11px;")

            # 4. KATEGORIE (Top 8)
            self._clear_layout(self.cat_v)

            header_label = QLabel(_("WYDANO W TYM MSC / ŚREDNIA Z 3 M-CY"))
            header_label.setStyleSheet("font-size: 10px; font-weight: bold; color: gray; margin-bottom: 5px;")
            header_label.setAlignment(Qt.AlignRight)
            self.cat_v.addWidget(header_label)

            for cat in data['category_forecasts']:
                h_layout = QHBoxLayout()
                cat_name = QLabel(f"<b>{cat['name']}</b>")
                cat_name.setStyleSheet("font-size: 12px;")

                # Dodajemy info o procencie wykonania normy w tooltipie
                values_lbl = QLabel(f"{cat['current']:.0f} / {cat['predicted']:.0f} zł")
                values_lbl.setStyleSheet("font-size: 11px;")
                values_lbl.setToolTip(f"{cat['risk']}% {_('historycznej średniej')}")

                h_layout.addWidget(cat_name)
                h_layout.addStretch()
                h_layout.addWidget(values_lbl)
                self.cat_v.addLayout(h_layout)

                p_bar = QProgressBar()
                p_bar.setFixedHeight(6)
                p_bar.setValue(min(100, cat['risk']))
                p_bar.setTextVisible(False)

                # Kolor paska: niebieski -> pomarańczowy (>70%) -> czerwony (>90%)
                if cat['risk'] > 90: p_color = "#e74c3c"
                elif cat['risk'] > 70: p_color = "#e67e22"
                else: p_color = "#3498db"

                p_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {p_color}; border-radius: 2px; }}")
                self.cat_v.addWidget(p_bar)

            self.cat_v.addStretch()

            # 5. ALERTY AI
            self._clear_layout(self.alert_v)

            # Pobieramy bezpiecznie obie listy z danymi
            alerts_hard = data.get('ai_alerts_hard', [])
            alerts_tips = data.get('ai_alerts_tips', [])

            # --- BLOK 1: TWARDA ANALIZA (Niebieskie kafelki) ---
            for msg in alerts_hard:
                alert_lbl = QLabel()
                alert_lbl.setTextFormat(Qt.RichText)
                alert_lbl.setText(msg)
                alert_lbl.setWordWrap(True)
                alert_lbl.setStyleSheet("""
                    padding: 10px;
                    background: rgba(52, 152, 219, 0.05);
                    border-left: 4px solid #3498db;
                    border-radius: 4px;
                    margin-bottom: 4px;
                """)
                self.alert_v.addWidget(alert_lbl)

            # Dodajemy naturalny, elegancki odstęp między analizą a tipami
            self.alert_v.addSpacing(12)

            # --- BLOK 2: PORADY I SUGESTIE (Szare, pochylone kafelki) ---
            for msg in alerts_tips:
                tip_lbl = QLabel()
                tip_lbl.setTextFormat(Qt.RichText)
                tip_lbl.setText(msg)
                tip_lbl.setWordWrap(True)
                tip_lbl.setStyleSheet("""
                    padding: 8px 10px;
                    background: rgba(149, 165, 166, 0.05);
                    border-left: 4px solid #95a5a6;
                    border-radius: 4px;
                    margin-bottom: 4px;
                    font-style: italic;
                    color: palette(text);
                """)
                self.alert_v.addWidget(tip_lbl)

            self.alert_v.addStretch()

        finally:
            self.setUpdatesEnabled(True)  # Włączamy rysowanie z powrotem

    def _create_kpi_card(self, title):
        card = QFrame()
        card.setStyleSheet("QFrame { border: 1px solid palette(mid); border-radius: 12px; padding: 10px; }")
        l = QVBoxLayout(card)

        t = QLabel(title)
        t.setStyleSheet("font-size: 13px; font-weight: bold; color: palette(text);")
        t.setAlignment(Qt.AlignCenter)

        v = QLabel("--")
        v.setObjectName("val_lbl") # Nazwa, by łatwo znaleźć widżet przy odświeżaniu
        v.setStyleSheet("color: palette(text); font-size: 24px; font-weight: bold;")
        v.setAlignment(Qt.AlignCenter)

        l.addWidget(t); l.addWidget(v)
        return card

    def _clear_layout(self, layout):
        """Bezpieczne czyszczenie layoutu w PySide6 bez użycia modułu sip."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self._clear_layout(sub_layout)

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QSlider, QPushButton, QLineEdit, QListWidget,
                             QFrame, QGridLayout, QGroupBox, QScrollArea, QWidget)
from PySide6.QtCore import Qt
from simulator import WhatIfSimulator  # Importujemy nasz nowy symulator

class WhatIfDialog(QDialog):
    def __init__(self, parent, db_manager, forecaster):
        super().__init__(parent)
        self.db = db_manager
        self.forecaster = forecaster
        self.simulator = WhatIfSimulator(self.forecaster)
        self.advice_rotation_index = 0

        # Pobieramy stan początkowy bazy
        self.simulator.load_current_state()

        self.setWindowTitle(_("Symulator finansowy \"Co jeśli?\""))
        self.resize(620, 750)  # Sztywny, komfortowy wymiar okna
        self.init_ui()
        self.recalculate()
        self.advice_timer = QTimer(self)
        self.advice_timer.timeout.connect(self.rotate_advice)
        self.advice_timer.start(30000)

    def rotate_advice(self):
        self.advice_rotation_index += 1
        self.recalculate()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --- TWÓJ ORYGINALNY BAZOWY STYL DLA PRZYCISKÓW ---
        top_base_style = """
            QPushButton {
                font-size: 12px; font-weight: bold; border-radius: 6px;
                border: 2px solid; background-color: transparent;
                min-height: 26px; max-height: 26px; padding: 2px 8px;
            }
        """

        # --- TWOJE STYLE KOLORYSTYCZNE ---
        back_style = top_base_style + """
            QPushButton { color: #7f8c8d; border-color: #95a5a6; }
            QPushButton:hover { background-color: #7f8c8d; color: #ffffff; }
        """
        shop_style = top_base_style + """
            QPushButton { color: #16a085; border-color: #1abc9c; }
            QPushButton:hover { background-color: #16a085; color: #ffffff; }
        """
        pdf_style = top_base_style + """
            QPushButton { color: #c0392b; border-color: #e74c3c; }
            QPushButton:hover { background-color: #c0392b; color: #ffffff; }
        """
        close_style = top_base_style + """
            QPushButton { color: #ba4a00; border-color: #e67e22; }
            QPushButton:hover { background-color: #ba4a00; color: #ffffff; }
        """

        # --- NAGŁÓWEK ---
        title = QLabel(f"<b>{_('Symulator scenariuszy \"Co jeśli?\"')}</b>")
        title.setStyleSheet("font-size: 16px;")
        layout.addWidget(title)

        subtitle = QLabel(_("Sprawdź jak decyzje wpłyną na Twoje finanse bez dotykania prawdziwej bazy danych."))
        subtitle.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        # --- PANEL PORÓWNANIA (KAFELKI SYSTEMOWE) ---
        grid = QGridLayout()
        layout.addLayout(grid)

        # Kafelek oryginalny
        self.card_orig = QFrame()
        self.card_orig.setFrameShape(QFrame.StyledPanel)
        v_orig = QVBoxLayout(self.card_orig)
        v_orig.addWidget(QLabel(f"<b>{_('OBECNA PROGNOZA')}</b>"))
        self.lbl_orig_val = QLabel("0.00 zł")
        self.lbl_orig_val.setStyleSheet("font-size: 20px; font-weight: bold; color: gray;")
        self.lbl_orig_days = QLabel(_("Margines: - dni"))
        v_orig.addWidget(self.lbl_orig_val)
        v_orig.addWidget(self.lbl_orig_days)

        # Kafelek symulowany
        self.card_sim = QFrame()
        self.card_sim.setFrameShape(QFrame.StyledPanel)
        v_sim = QVBoxLayout(self.card_sim)
        v_sim.addWidget(QLabel(f"<b>{_('PO SYMULACJI')}</b>"))
        self.lbl_sim_val = QLabel("0.00 zł")
        self.lbl_sim_val.setStyleSheet("font-size: 20px; font-weight: bold; color: #2ecc71;")
        self.lbl_sim_days = QLabel(_("Margines: - dni"))
        v_sim.addWidget(self.lbl_sim_val)
        v_sim.addWidget(self.lbl_sim_days)

        grid.addWidget(self.card_orig, 0, 0)
        grid.addWidget(self.card_sim, 0, 1)

        # --- SUWAK STYLU ŻYCIA ---
        layout.addWidget(QLabel(f"<b>{_('Zmień codzienne wydatki (np. oszczędzanie na jedzeniu):')}</b>"))
        h_slider = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(-50, 50)  # Oszczędność maks. 50% lub wzrost o 50%
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(10)
        self.slider.valueChanged.connect(self.on_slider_changed)

        self.lbl_slider_val = QLabel(_("Normalnie (0%)"))
        self.lbl_slider_val.setFixedWidth(120)
        self.lbl_slider_val.setStyleSheet("font-weight: bold;")

        h_slider.addWidget(self.slider)
        h_slider.addWidget(self.lbl_slider_val)
        layout.addLayout(h_slider)

        # --- SEKCOWANE DODAWANIE WIRTUALNYCH TRANSAKCJI ---
        layout.addWidget(QLabel(f"<b>{_('Dodaj wirtualną transakcję jednorazową (np. zakup konsoli, premia):')}</b>"))
        h_add = QHBoxLayout()

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText(_("Nazwa (np. Nowy telefon)"))
        self.input_name.textChanged.connect(self.recalculate)

        self.input_amount = QLineEdit()
        self.input_amount.setPlaceholderText(_("Kwota (np. 1500)"))
        self.input_amount.setFixedWidth(120)  # Stabilna i bezpieczna szerokość pola kwoty
        self.input_amount.textChanged.connect(self.recalculate)

        self.btn_add_exp = QPushButton(_("Dodaj Koszt (-)"))
        self.btn_add_exp.setStyleSheet(pdf_style)
        self.btn_add_exp.clicked.connect(self.add_virtual_expense)

        self.btn_add_inc = QPushButton(_("Dodaj Wpływ (+)"))
        self.btn_add_inc.setStyleSheet(shop_style)
        self.btn_add_inc.clicked.connect(self.add_virtual_income)

        h_add.addWidget(self.input_name)
        h_add.addWidget(self.input_amount)
        h_add.addWidget(self.btn_add_exp)
        h_add.addWidget(self.btn_add_inc)
        layout.addLayout(h_add)

        # --- LISTA AKTYWNYCH MODYFIKATORÓW ---
        layout.addWidget(QLabel(f"<b>{_('Aktywne wirtualne zmiany:')}</b>"))
        self.list_modifiers = QListWidget()
        self.list_modifiers.setMaximumHeight(80)  # Ograniczamy wysokość na rzecz dużego dymka AI
        layout.addWidget(self.list_modifiers)

        # --- SEKCJA: DYNAMICZNE REKOMENDACJE AI (SCROLLAREA) ---
        self.ai_advice_group = QGroupBox(_("Analiza i rekomendacje AI"))
        self.ai_advice_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        self.ai_advice_group.setFixedHeight(220)  # Zamrożony i nienaruszalny layout grupy

        # Tworzymy ScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background-color: transparent;")

        # Kontener wewnętrzny
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background-color: transparent;")
        self.ai_advice_layout = QVBoxLayout(self.scroll_widget)
        self.ai_advice_layout.setContentsMargins(5, 5, 5, 5)
        self.ai_advice_layout.setSpacing(6)

        # --- ZMIANA: Etykieta jako zmienna klasy w celu łatwego ukrywania/pokazywania ---
        self.lbl_ai_advice_placeholder = QLabel(_("Wprowadź kwotę lub wirtualne koszty, aby zobaczyć rekomendacje..."))
        self.lbl_ai_advice_placeholder.setWordWrap(True)
        self.lbl_ai_advice_placeholder.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 12px;")
        self.ai_advice_layout.addWidget(self.lbl_ai_advice_placeholder)

        self.scroll_area.setWidget(self.scroll_widget)

        # Układ pionowy dla grupy QGroupBox
        group_layout = QVBoxLayout(self.ai_advice_group)
        group_layout.addWidget(self.scroll_area)

        layout.addWidget(self.ai_advice_group)

        # --- PODSUMOWANIE DYNAMICZNE ---
        self.lbl_summary = QLabel("")
        self.lbl_summary.setWordWrap(True)
        self.lbl_summary.setStyleSheet("""
            padding: 10px;
            border: 1px solid palette(mid);
            border-radius: 4px;
            margin-top: 5px;
            font-size: 12px;
        """)
        layout.addWidget(self.lbl_summary)

        # --- PRZYCISKI STOPKI ---
        h_foot = QHBoxLayout()
        btn_reset = QPushButton(_("Resetuj symulację"))
        btn_reset.setStyleSheet(close_style)
        btn_reset.clicked.connect(self.reset_simulation)

        btn_close = QPushButton(_("Zamknij"))
        btn_close.setStyleSheet(back_style)
        btn_close.clicked.connect(self.accept)

        h_foot.addWidget(btn_reset)
        h_foot.addStretch()
        h_foot.addWidget(btn_close)
        layout.addLayout(h_foot)

    def on_slider_changed(self, val):
        if val == 0:
            self.lbl_slider_val.setText(_("Normalnie (0%)"))
        elif val < 0:
            self.lbl_slider_val.setText(f"{_('Oszczędzasz')}: {val}%")
        else:
            self.lbl_slider_val.setText(f"{_('Wydatki')}: +{val}%")

        self.simulator.set_lifestyle_multiplier(val)
        self.recalculate()

    def add_virtual_expense(self):
        name = self.input_name.text().strip() or _("Wirtualny koszt")
        try:
            amt = float(self.input_amount.text().replace(',', '.'))
            self.simulator.add_one_off_expense(name, amt)
            self.list_modifiers.addItem(f"🔴 {_('Wydatek')}: {name} (-{amt:.2f} zł)")
            self.input_name.blockSignals(True)
            self.input_amount.blockSignals(True)
            self.input_name.clear()
            self.input_amount.clear()
            self.input_name.blockSignals(False)
            self.input_amount.blockSignals(False)
            self.recalculate()
        except ValueError:
            pass

    def add_virtual_income(self):
        name = self.input_name.text().strip() or _("Wirtualny wpływ")
        try:
            amt = float(self.input_amount.text().replace(',', '.'))
            self.simulator.add_one_off_income(name, amt)
            self.list_modifiers.addItem(f"🟢 {_('Wpływ')}: {name} (+{amt:.2f} zł)")
            self.input_name.blockSignals(True)
            self.input_amount.blockSignals(True)
            self.input_name.clear()
            self.input_amount.clear()
            self.input_name.blockSignals(False)
            self.input_amount.blockSignals(False)
            self.recalculate()
        except ValueError:
            pass

    def reset_simulation(self):
        self.slider.setValue(0)
        self.list_modifiers.clear()
        self.simulator.reset_scenarios()
        self.recalculate()

    def recalculate(self):
        # 1. Odpalamy silnik symulacji
        res = self.simulator.run_simulation()
        base = self.simulator.base_predictions

        # Dane bazowe
        base_val = base['projected_end_month']
        daily_avg = base.get('daily_avg', 300.0)
        if daily_avg <= 0:
            daily_avg = 300.0

        base_days = max(0, int(base_val / daily_avg)) if base_val > 0 else 0

        self.lbl_orig_val.setText(f"{base_val:.2f} zł")
        self.lbl_orig_days.setText(f"{_('Przy obecnym tempie wydatków masz')} <b>{base_days}</b> {_('dni bezpieczeństwa')}")

        # Dane symulowane
        sim_val = res['projected_end_month']
        sim_days = max(0, int(sim_val / daily_avg)) if sim_val > 0 else 0

        self.lbl_sim_val.setText(f"{sim_val:.2f} zł")
        self.lbl_sim_days.setText(f"{_('Przy symulowanym tempie wydatków masz')} <b>{sim_days}</b> {_('dni bezpieczeństwa')}")

        # Kolorystyka wyniku końcowego i podsumowania
        if sim_val > 0:
            sim_color = "#2ecc71"
            self.lbl_summary.setStyleSheet("padding: 10px; border: 1px solid #2ecc71; border-radius: 4px; margin-top: 5px; font-size: 12px;")
        else:
            sim_color = "#e74c3c"
            self.lbl_summary.setStyleSheet("padding: 10px; border: 1px solid #e74c3c; border-radius: 4px; margin-top: 5px; font-size: 12px;")

        self.lbl_sim_val.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {sim_color};")
        self.lbl_summary.setText(res['simulation_summary'])

        # 2. --- POŁĄCZENIE SYSTEMOWE: DYNAMICZNE PRZELICZANIE KWOT W LOCIE ---
        total_virtual_expenses = 0.0
        detected_category = "Inne"

        # KROK A: Pobieramy kwotę z pola tekstowego (nawet przed kliknięciem "Dodaj")
        if hasattr(self, 'input_amount') and self.input_amount.text().strip():
            try:
                raw_amt = self.input_amount.text().replace(',', '.')
                total_virtual_expenses += float(raw_amt)
            except ValueError:
                pass

        # KROK B: Dodajemy do tego kwoty z aktywnych modyfikatorów na liście
        for i in range(self.list_modifiers.count()):
            text = self.list_modifiers.item(i).text()
            if "🔴" in text:
                try:
                    parts = text.split("(-")
                    val_str = parts[1].replace(" zł)", "").strip()
                    total_virtual_expenses += float(val_str)

                    lower_text = text.lower()
                    if any(x in lower_text for x in ["auto", "samochód", "paliwo", "opony", "ubezpieczenie"]):
                        detected_category = "Samochód"
                    elif any(x in lower_text for x in ["biedronka", "lidl", "jedzenie", "zakupy", "spożywcze"]):
                        detected_category = "Zakupy"
                    elif any(x in lower_text for x in ["netflix", "spotify", "kino", "rozrywka", "pub"]):
                        detected_category = "Rozrywka"
                except Exception:
                    pass

        # KROK C: Sprawdzamy wpisaną nazwę pod kątem wykrywania kategorii w locie
        if hasattr(self, 'input_name') and self.input_name.text().strip():
            lower_input_name = self.input_name.text().lower()
            if any(x in lower_input_name for x in ["auto", "samochód", "paliwo", "opony", "ubezpieczenie"]):
                detected_category = "Samochód"
            elif any(x in lower_input_name for x in ["biedronka", "lidl", "jedzenie", "zakupy", "spożywcze"]):
                detected_category = "Zakupy"
            elif any(x in lower_input_name for x in ["netflix", "spotify", "kino", "rozrywka", "pub"]):
                detected_category = "Rozrywka"

        slider_value = self.slider.value()

        # --- OBSŁUGA ZNIKANIA PLACEHOLDERA ---
        # Jeśli są jakieś zmiany (suwak != 0 lub kwota > 0), to ukrywamy placeholder startowy
        if slider_value != 0 or total_virtual_expenses > 0:
            self.lbl_ai_advice_placeholder.hide()
        else:
            self.lbl_ai_advice_placeholder.show()

        # Czyszczenie starych dynamicznych kafelków (oprócz naszego placeholdera, którego po prostu kontrolujemy przez hide/show)
        for i in reversed(range(self.ai_advice_layout.count())):
            item = self.ai_advice_layout.itemAt(i)
            widget = item.widget()
            if widget and widget != self.lbl_ai_advice_placeholder:
                widget.deleteLater()

        # Pobieramy najnowsze spersonalizowane rekomendacje z uwzględnieniem dynamicznej kwoty i suwaka!
        if slider_value != 0 or total_virtual_expenses > 0:
            advices = self.forecaster.get_what_if_advice(
                total_virtual_expenses,
                detected_category,
                slider_value,
                rotation_index=self.advice_rotation_index
            )
        else:
            advices = []

        # Budujemy nowe, czytelniejsze kafelki
        for adv in advices:
            lbl = QLabel()
            lbl.setTextFormat(Qt.RichText)
            lbl.setText(adv)
            lbl.setWordWrap(True)  # Pancerne zawijanie tekstu w dymkach

            if "Zagrożenie" in adv or "⚠️" in adv:
                bg_color = "rgba(192, 57, 43, 0.05)"
                border_color = "#c0392b"
            elif "Bezpieczny" in adv or "✅" in adv or "Generujesz" in adv:
                bg_color = "rgba(39, 174, 96, 0.05)"
                border_color = "#27ae60"
            else:
                bg_color = "rgba(149, 165, 166, 0.05)"
                border_color = "#95a5a6"

            lbl.setStyleSheet(f"""
                padding: 10px 12px;
                background: {bg_color};
                border-left: 4px solid {border_color};
                border-radius: 4px;
                margin-bottom: 6px;
                font-size: 12px;
                line-height: 1.4;
            """)
            self.ai_advice_layout.addWidget(lbl)

def get_detailed_os_info():
    """Zwraca czytelny dla człowieka opis systemu operacyjnego wraz z wersją jądra."""
    try:
        sys_platform = sys.platform

        # --- 1. WINDOWS ---
        if sys_platform == "win32":
            win_release = platform.release() # np. "10" lub "11"
            win_version = platform.version() # np. "10.0.22631"
            return f"Windows {win_release} (Wersja: {win_version}, Jądro: NT)"

        # --- 2. MACOS (DARWIN) ---
        elif sys_platform == "darwin":
            mac_ver = platform.mac_ver()[0] # np. "14.4"
            kernel_ver = platform.release() # np. "23.4.0"
            return f"macOS {mac_ver} (Jądro: Darwin {kernel_ver})"

        # --- 3. LINUX (Arch, Ubuntu itp.) ---
        elif sys_platform.startswith("linux"):
            # Próbujemy odczytać dane z /etc/os-release (standard na nowoczesnych dystrybucjach)
            dist_name = "Linux"
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    info = {}
                    for line in lines:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            info[k] = v.strip('"')
                    # Próbujemy wyciągnąć 'PRETTY_NAME' (np. "Arch Linux" lub "Ubuntu 22.04.4 LTS")
                    dist_name = info.get("PRETTY_NAME", info.get("NAME", "Linux"))

            kernel_ver = platform.release() # np. "6.12.1-arch1-1"
            return f"{dist_name} (Jądro: Linux {kernel_ver})"

    except Exception as e:
        # Fallback w razie jakichkolwiek problemów z uprawnieniami / odczytem
        return f"{platform.system()} {platform.release()} (Błąd detekcji: {str(e)})"

    return f"{platform.system()} {platform.release()}"

import os
import sys
import platform
import urllib.parse
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from config import _

class BugReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Zgłoś błąd lub sugestię"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Inicjalizacja layoutu
        layout = QVBoxLayout(self)

        # 1. Instrukcja
        info_label = QLabel(
            _("Opisz krótko napotkany problem lub swoją sugestię.<br>"
              "Po kliknięciu 'Zgłoś na GitHub' zostaniesz przekierowany do przeglądarki, "
              "gdzie zgłoszenie zostanie automatycznie przygotowane.")
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        layout.addSpacing(10)

        # 2. Tytuł błędu
        layout.addWidget(QLabel(_("Krótki tytuł zgłoszenia:")))
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText(_("np. Błąd przy generowaniu PDF, Sugestia dotycząca wykresu"))
        layout.addWidget(self.title_input)
        layout.addSpacing(10)

        # 3. Szczegółowy opis
        layout.addWidget(QLabel(_("Szczegółowy opis (co robiłeś, co poszło nie tak):")))
        self.desc_input = QTextEdit(self)
        self.desc_input.setPlaceholderText(_("Wpisz tutaj jak najwięcej szczegółów..."))
        layout.addWidget(self.desc_input)
        layout.addSpacing(15)

        # 4. Przyciski dolne w Twoim Lux Style
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton(_("Anuluj"), self)
        self.btn_send = QPushButton(_("Zgłoś na GitHub"), self)
        self.btn_send.setDefault(True)

        # --- STYLIZACJA LUX STYLE ---
        # Styl dla przycisku akcji (ciemna zieleń przechodząca w jaśniejszą na hover)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2980b9;
                border: 2px solid #3498db;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #1f618d;
                border-color: #1f618d;
                color: #ffffff;
            }
        """)

        # Styl dla przycisku Anuluj (neutralny, ciemny szary przechodzący w jasny szary)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7f8c8d;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #616a6b;
                border-color: #616a6b;
                color: #ffffff;
            }
        """)
        # -----------------------------

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_send.clicked.connect(self.send_to_github)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_send)
        layout.addLayout(btn_layout)

    def send_to_github(self):
        title = self.title_input.text().strip()
        description = self.desc_input.toPlainText().strip()

        if not title:
            title = "Zgłoszenie błędu"

        # --- UŻYCIE NOWEJ, SZCZEGÓŁOWEJ DETEKCJI ---
        os_info = get_detailed_os_info()
        arch_info = platform.machine() # np. "AMD64" lub "x86_64"
        python_ver = platform.python_version()

        try:
            from config import WERSJA
            app_version = WERSJA
        except ImportError:
            app_version = "NIEROZPOZNANA"

        # Szablon zgłoszenia błędu dla repozytorium SerwisApp
        github_body = (
            f"### Opis problemu\n"
            f"{description}\n\n"
            f"--- \n"
            f"### Środowisko uruchomieniowe\n"
            f"- **Wersja aplikacji:** {app_version}\n"
            f"- **System operacyjny:** {os_info}\n"
            f"- **Architektura:** {arch_info}\n"
            f"- **Wersja Pythona:** {python_ver}\n"
        )

        encoded_title = urllib.parse.quote(title)
        encoded_body = urllib.parse.quote(github_body)

        # Link kierujący do Twojego repozytorium SerwisApp
        github_url = (
            f"https://github.com/KlapkiSzatana/serwis-app/issues/new"
            f"?title={encoded_title}"
            f"&body={encoded_body}"
        )

        # Wywołanie systemowe otwarcia URL (zachowaj swój dotychczasowy kod otwierający przeglądarkę)
        if os.name == 'nt':
            try:
                os.startfile(github_url)
            except Exception:
                subprocess.Popen(['cmd', '/c', 'start', '', github_url], shell=True)
        else:
            env = dict(os.environ)
            env.pop('LD_LIBRARY_PATH', None)
            env.pop('QT_PLUGIN_PATH', None)
            env.pop('QT_QPA_PLATFORM_PLUGIN_PATH', None)

            opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
            try:
                subprocess.Popen([opener, github_url], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"Nie udało się otworzyć przeglądarki: {e}")

        self.accept()
