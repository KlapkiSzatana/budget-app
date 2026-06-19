from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QCheckBox, QPushButton, QDialogButtonBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
                               QColorDialog, QMessageBox, QComboBox, QLabel,
                               QFileDialog)
from PySide6.QtCore import Qt
import os
import config
from config import _

class SettingsDialog(QDialog):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.initial_language = config.get_language_code()
        self.restart_required = False
        self.setWindowTitle(_("Ustawienia i Konta"))
        self.resize(620, 760)
        layout = QVBoxLayout(self)


        base_style = """
            QPushButton {
                font-size: 12px; font-weight: bold; padding: 5px 10px;
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


        modules_group = QGroupBox(_("Widoczne moduły i systemy"))
        mod_lay = QVBoxLayout(modules_group)

        self.cb_liabilities = QCheckBox(_("System Długów (Zobowiązania)"))
        self.cb_liabilities.setChecked(self.db.get_config_bool("show_liabilities", True))

        self.cb_debtors = QCheckBox(_("System Dłużników (Należności)"))
        self.cb_debtors.setChecked(self.db.get_config_bool("show_debtors", True))

        self.cb_shopping = QCheckBox(_("Moduł: Lista Zakupów"))
        self.cb_shopping.setChecked(self.db.get_config_bool("show_shopping", True))

        self.cb_weekly = QCheckBox(_("System: Limit Tygodniowy"))
        self.cb_weekly.setChecked(self.db.get_config_bool("show_weekly", True))


        self.cb_forecast = QCheckBox(_("Moduł: Prognozy i Analiza AI"))
        self.cb_forecast.setChecked(self.db.get_config_bool("show_forecast", True))


        for cb in [self.cb_liabilities, self.cb_debtors, self.cb_shopping, self.cb_weekly, self.cb_forecast]:
            mod_lay.addWidget(cb)
        layout.addWidget(modules_group)

        sync_group = QGroupBox(_("Synchronizacja LAN"))
        sync_lay = QVBoxLayout(sync_group)

        self.cb_sync_server = QCheckBox(_("Włącz serwer synchronizacji na PC"))
        self.cb_sync_server.setChecked(self.db.get_config_bool("sync_server_enabled", True))
        sync_lay.addWidget(self.cb_sync_server)

        sync_peer_row = QHBoxLayout()
        sync_peer_row.setSpacing(10)
        sync_peer_row.addWidget(QLabel(_("Adres telefonu:")))
        self.sync_peer_url = QLineEdit()
        self.sync_peer_url.setPlaceholderText("http://192.168.1.50:8765")
        self.sync_peer_url.setText(str(self.db.get_config("sync_peer_url") or ""))
        sync_peer_row.addWidget(self.sync_peer_url, 1)
        sync_lay.addLayout(sync_peer_row)

        try:
            from budget_sync import local_ipv4_addresses
            local_urls = ", ".join(f"http://{ip}:8765" for ip in local_ipv4_addresses())
        except Exception:
            local_urls = "http://127.0.0.1:8765"
        sync_hint = QLabel(_("Adresy tego PC dla Androida: {}").format(local_urls))
        sync_hint.setWordWrap(True)
        sync_hint.setStyleSheet("color: gray; font-size: 11px;")
        sync_lay.addWidget(sync_hint)

        layout.addWidget(sync_group)


        acc_group = QGroupBox(_("Zarządzanie kontami"))
        acc_group.setMaximumHeight(300)
        acc_lay = QVBoxLayout(acc_group)


        self.acc_table = QTableWidget(0, 3)
        self.acc_table.setHorizontalHeaderLabels([_("Nazwa konta"), _("Saldo pocz."), _("Kolor")])
        self.acc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.acc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.acc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.acc_table.setColumnWidth(2, 100)

        self.acc_table.setAlternatingRowColors(True)
        self.acc_table.setStyleSheet("QTableWidget { font-size: 12px; }")
        acc_lay.addWidget(self.acc_table)


        add_acc_lay = QHBoxLayout()
        add_acc_lay.setSpacing(10)
        self.new_acc_name = QLineEdit()
        self.new_acc_name.setPlaceholderText(_("Nazwa konta"))
        self.new_acc_name.setMaxLength(30)

        self.new_acc_bal = QLineEdit()
        self.new_acc_bal.setPlaceholderText(_("Saldo startowe"))

        btn_add_acc = QPushButton(_("Dodaj konto"))
        btn_add_acc.setStyleSheet(inc_style)
        btn_add_acc.clicked.connect(self.add_account_action)

        add_acc_lay.addWidget(self.new_acc_name)
        add_acc_lay.addWidget(self.new_acc_bal)
        add_acc_lay.addWidget(btn_add_acc)
        acc_lay.addLayout(add_acc_lay)

        layout.addWidget(acc_group)

        language_group = QGroupBox(_("Język aplikacji"))
        language_lay = QVBoxLayout(language_group)

        lang_row = QHBoxLayout()
        lang_row.setSpacing(10)
        lang_row.addWidget(QLabel(_("Wybierz język:")))
        self.language_combo = QComboBox()
        self.language_codes = config.discover_languages()
        current_language = config.get_language_code()
        for code in self.language_codes:
            self.language_combo.addItem(config.display_language_name(code), code)
        current_idx = self.language_combo.findData(current_language)
        if current_idx >= 0:
            self.language_combo.setCurrentIndex(current_idx)
        lang_row.addWidget(self.language_combo, 1)
        language_lay.addLayout(lang_row)

        lang_hint = QLabel(_("PL jest językiem domyślnym."))
        lang_hint.setWordWrap(True)
        lang_hint.setStyleSheet("color: gray; font-size: 11px;")
        language_lay.addWidget(lang_hint)
        layout.addWidget(language_group)

        db_group = QGroupBox(_("Katalog bazy danych"))
        db_lay = QVBoxLayout(db_group)
        db_row = QHBoxLayout()
        db_row.setSpacing(10)
        self.database_dir_edit = QLineEdit()
        self.database_dir_edit.setReadOnly(True)
        self.database_dir_edit.setText(config.get_database_dir())
        btn_choose_db_dir = QPushButton(_("Wybierz katalog"))
        btn_choose_db_dir.clicked.connect(self.choose_database_dir)
        db_row.addWidget(self.database_dir_edit, 1)
        db_row.addWidget(btn_choose_db_dir)
        db_lay.addLayout(db_row)
        db_hint = QLabel(_("Jeśli nie zmienisz katalogu, aplikacja używa dotychczasowej lokalizacji domyślnej."))
        db_hint.setWordWrap(True)
        db_hint.setStyleSheet("color: gray; font-size: 11px;")
        db_lay.addWidget(db_hint)
        layout.addWidget(db_group)

        self.refresh_accounts()


        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        if self.buttons.layout():
            self.buttons.layout().setSpacing(12)
        self.buttons.accepted.connect(self.save_and_close)
        self.buttons.rejected.connect(self.reject)

        btn_save = self.buttons.button(QDialogButtonBox.Save)
        if btn_save:
            btn_save.setText(_("ZAPISZ"))
            btn_save.setStyleSheet(inc_style)

        btn_cancel = self.buttons.button(QDialogButtonBox.Cancel)
        if btn_cancel:
            btn_cancel.setText(_("ANULUJ"))
            btn_cancel.setStyleSheet(exp_style)

        layout.addWidget(self.buttons)

    def choose_database_dir(self):
        start_dir = self.database_dir_edit.text().strip() or config.get_database_dir()
        start_dir = os.path.abspath(os.path.expanduser(start_dir))
        if not os.path.isdir(start_dir):
            start_dir = config.get_database_dir()
        os.makedirs(start_dir, exist_ok=True)

        directory = QFileDialog.getExistingDirectory(
            self,
            _("Wybierz katalog bazy danych"),
            start_dir,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog
        )
        if directory:
            self.database_dir_edit.setText(os.path.abspath(directory))

    def refresh_accounts(self):
        self.acc_table.setRowCount(0)
        accounts = self.db.get_accounts()

        for acc_id, name, bal, color in accounts:
            row = self.acc_table.rowCount()
            self.acc_table.insertRow(row)


            name_item = QTableWidgetItem(name)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.acc_table.setItem(row, 0, name_item)


            bal_item = QTableWidgetItem(f"{bal:.2f} zł")
            bal_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.acc_table.setItem(row, 1, bal_item)


            color_widget = QPushButton(_("Zmień"))
            color_widget.setStyleSheet(f"""
                QPushButton {{
                    border-left: 10px solid {color};
                    font-size: 11px; padding: 2px;
                    border-top: 1px solid gray; border-right: 1px solid gray; border-bottom: 1px solid gray;
                }}
            """)
            color_widget.clicked.connect(lambda ch, aid=acc_id, n=name: self.change_account_color(aid, n))
            self.acc_table.setCellWidget(row, 2, color_widget)

    def change_account_color(self, acc_id, name):
        color = QColorDialog.getColor()
        if color.isValid():
            new_hex = color.name()
            if self.db.update_account_color(acc_id, new_hex):
                self.refresh_accounts()

                if hasattr(self.parent(), 'load_transactions'):
                    self.parent().load_transactions()

    def add_account_action(self):
        name = self.new_acc_name.text().strip()
        raw = self.new_acc_bal.text().replace(',', '.')

        try:
            bal = float(raw) if raw else 0.0
        except ValueError:
            bal = 0.0

        if not name:
            return

        color = QColorDialog.getColor()
        color_hex = color.name() if color.isValid() else "#7f8c8d"

        if self.db.add_account(name, bal, color_hex):
            self.new_acc_name.clear()
            self.new_acc_bal.clear()
            self.refresh_accounts()

            if hasattr(self.parent(), 'load_transactions'):
                self.parent().load_transactions()
            QMessageBox.information(self, _("Sukces"), _("Konto '{}' zostało dodane.").format(name))
        else:
            QMessageBox.warning(self, _("Błąd"), _("Nie udało się dodać konta."))

    def save_and_close(self):
        selected_db_dir = self.database_dir_edit.text().strip() or config.get_database_dir()
        selected_db_dir = os.path.abspath(os.path.expanduser(selected_db_dir))
        if selected_db_dir != config.get_database_dir():
            try:
                self.db.switch_database_dir(selected_db_dir)
            except Exception as error:
                QMessageBox.critical(self, _("Błąd"), _("Nie udało się przełączyć katalogu bazy:\n{}").format(error))
                return

        selected_language = self.language_combo.currentData() or config.DEFAULT_LANGUAGE
        language_changed = config.normalize_language_code(selected_language) != self.initial_language
        config.install_language(selected_language, persist=True)
        self.db.set_config("language", selected_language)

        self.db.set_config("show_liabilities", self.cb_liabilities.isChecked())
        self.db.set_config("show_debtors", self.cb_debtors.isChecked())
        self.db.set_config("show_shopping", self.cb_shopping.isChecked())
        self.db.set_config("show_weekly", self.cb_weekly.isChecked())

        self.db.set_config("show_forecast", self.cb_forecast.isChecked())
        self.db.set_config("sync_server_enabled", self.cb_sync_server.isChecked())
        self.db.set_config("sync_peer_url", self.sync_peer_url.text().strip())
        if language_changed:
            QMessageBox.information(
                self,
                _("Restart aplikacji"),
                _("Język został zapisany. Aplikacja zostanie teraz uruchomiona ponownie.")
            )
            self.restart_required = True
        self.accept()
