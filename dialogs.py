from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QPushButton, QDateEdit, QGroupBox, QFormLayout,
                               QDialogButtonBox, QRadioButton, QButtonGroup,
                               QProgressBar, QTextEdit, QSpinBox, QFrame, QWidget,
                               QCheckBox, QListWidget, QListWidgetItem, QAbstractItemView)
from PySide6.QtCore import Qt, QDate
from config import _, CASH_SAVINGS_NAME, MONTH_NAME

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
        self.pbar.setRange(0, 0) # Indeterminate state
        layout.addWidget(self.lbl)
        layout.addWidget(self.pbar)

class BackupDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Kopia Zapasowa"))
        self.resize(500, 250)
        layout = QVBoxLayout(self)

        gb = QGroupBox(_("Ustawienia"))
        form = QFormLayout()

        self.cb_auto = QCheckBox(_("Rób automatycznie przy zamknięciu"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)

        h = QHBoxLayout()
        h.addWidget(self.path_edit)
        btn = QPushButton("...")
        btn.clicked.connect(self.select_path)
        h.addWidget(btn)

        form.addRow(self.cb_auto)
        form.addRow(_("Lokalizacja:"), h)
        gb.setLayout(form)
        layout.addWidget(gb)

        h_act = QHBoxLayout()
        b1 = QPushButton(_("Utwórz Kopię Teraz"))
        b1.clicked.connect(self.create_now)
        b2 = QPushButton(_("Przywróć z Kopii"))
        b2.clicked.connect(self.restore_now)
        h_act.addWidget(b1)
        h_act.addWidget(b2)
        layout.addLayout(h_act)

        self.load_config()

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.accept)
        layout.addWidget(btns)

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
        if d:
            self.path_edit.setText(d)
            self.save_config()

    def create_now(self):
        import time
        from PySide6.QtWidgets import QApplication, QMessageBox

        self.save_config()
        pd = ProcessingDialog(self, "Backup", _("Tworzenie..."))
        pd.show()
        QApplication.processEvents()
        time.sleep(0.5)
        success, msg = self.db.perform_backup()
        pd.close()

        if success:
            QMessageBox.information(self, _("Sukces"), _("Utworzono:\n{}").format(msg))
        else:
            QMessageBox.warning(self, _("Błąd"), msg)

    def restore_now(self):
        import sys
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        path = self.path_edit.text()
        f, _ext = QFileDialog.getOpenFileName(self, _("Wybierz plik"), path, "Backup (*.bak)")

        if f and QMessageBox.Yes == QMessageBox.question(self, _("Potwierdź"), _("Przywrócenie nadpisze dane. Kontynuować?")):
            if self.db.restore_database(f):
                QMessageBox.information(self, _("Sukces"), _("Przywrócono. Restartuj aplikację."))
                sys.exit(0)
            else:
                QMessageBox.critical(self, _("Błąd"), _("Nie udało się przywrócić."))

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
        h_btns.addWidget(btn_all)
        h_btns.addWidget(btn_none)
        self.settings_layout.addLayout(h_btns)

        layout.addWidget(self.settings_container)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.save_and_close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.load_settings()

    def toggle_inputs(self, checked):
        self.settings_container.setEnabled(checked)

    def load_settings(self):
        is_system_enabled = self.db.is_weekly_system_enabled()
        self.cb_enabled.setChecked(is_system_enabled)

        # Pobieramy dane dla konkretnego tygodnia
        found, amount, saved_cats = self.db.get_weekly_limit_for_week(self.target_date)

        # Pobieramy globalną listę kategorii wliczanych z configu
        global_cfg = self.db.get_config("weekly_limit_config")
        global_active_cats = global_cfg.get("categories", []) if global_cfg else []

        # Jeśli dla tego tygodnia nie było jeszcze ustawień,
        # bazujemy na tym co jest w globalnym configu
        if not found:
            amount = 0.0
            saved_cats = global_active_cats

        self.amount_edit.setText(str(amount))
        all_cats = self.db.get_categories()

        self.cat_list.clear()
        for cat in all_cats:
            item = QListWidgetItem(cat)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)

            # LOGIKA: Jeśli kategoria jest w zapisanych dla tygodnia LUB
            # właśnie została dodana do globalnego configu - zaznacz
            if cat in saved_cats or cat in global_active_cats:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

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
            try:
                amt = float(self.amount_edit.text().replace(",", "."))
            except ValueError:
                amt = 0.0

            selected_cats = []
            for i in range(self.cat_list.count()):
                item = self.cat_list.item(i)
                if item.checkState() == Qt.Checked:
                    selected_cats.append(item.text())

            self.db.set_weekly_limit_for_week(self.target_date, amt, selected_cats)

        self.accept()

class IncomeDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Dodaj Przychód"))
        self.resize(400, 250)
        l = QFormLayout(self)
        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)
        self.person = QComboBox()
        self.person.setEditable(True)
        self.person.addItems(self.db.get_people())
        self.src = QLineEdit()
        self.src.setText(_("Wpływ"))
        self.amt = QLineEdit()
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        l.addRow(_("Data:"), self.date)
        l.addRow(_("Osoba:"), self.person)
        l.addRow(_("Źródło:"), self.src)
        l.addRow(_("Kwota:"), self.amt)
        l.addRow(bb)

    def get_data(self):
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "type": "income",
            "cat": self.person.currentText(),
            "sub": self.src.text(),
            "amount": float(self.amt.text().replace(",", "."))
        }

class AddExpenseDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Dodaj Wydatek"))
        self.resize(450, 300)
        l = QFormLayout(self)
        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)
        h = QHBoxLayout()
        self.cat = QComboBox()
        self.cat.addItems(self.db.get_categories())
        b1 = QPushButton("+"); b1.setFixedWidth(30); b1.clicked.connect(self.add_c)
        b2 = QPushButton("-"); b2.setFixedWidth(30); b2.clicked.connect(self.del_c)
        h.addWidget(self.cat); h.addWidget(b1); h.addWidget(b2)
        self.desc = QTextEdit(); self.desc.setFixedHeight(50)
        self.amt = QLineEdit()
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        l.addRow(_("Data:"), self.date)
        l.addRow(_("Kat:"), h)
        l.addRow(_("Opis:"), self.desc)
        l.addRow(_("Kwota:"), self.amt)
        self.cb_exclude = QCheckBox(_("Pomiń w limicie tygodniowym"))
        #self.cb_exclude.setStyleSheet("color: #7f8c8d; font-style: italic;")
        # ... w l.addRow:
        l.addRow("", self.cb_exclude)
        l.addRow(bb)

    def add_c(self):
        from PySide6.QtWidgets import QInputDialog

        t, ok = QInputDialog.getText(self, _("Nowa"), _("Nazwa:"))
        if ok and t:
            self.db.add_category(t)
            self.cat.clear()
            self.cat.addItems(self.db.get_categories())
            self.cat.setCurrentText(t)

    def del_c(self):
        from PySide6.QtWidgets import QMessageBox

        c = self.cat.currentText()
        if c and c != _("Inne") and QMessageBox.Yes == QMessageBox.question(self, _("Usuń"), _("Usunąć '{}'?").format(c)):
            self.db.delete_category_safe(c)
            self.cat.clear()
            self.cat.addItems(self.db.get_categories())
            self.cat.setCurrentText("Inne")

    def get_data(self):
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "type": "expense",
            "cat": self.cat.currentText(),
            "sub": self.desc.toPlainText(),
            "amount": float(self.amt.text().replace(",", ".")),
            "exclude": 1 if self.cb_exclude.isChecked() else 0
        }
class AddGoalDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.setWindowTitle(_("Nowy Cel"))
        self.resize(300, 150)
        l=QFormLayout(self)
        self.n=QLineEdit()
        self.t=QLineEdit()
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        l.addRow(_("Nazwa:"), self.n)
        l.addRow(_("Cel (PLN):"), self.t)
        l.addRow(bb)

    def get_data(self):
        return self.n.text().strip(), float(self.t.text().replace(",", "."))

class AddSavingsDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db=db_manager
        self.setWindowTitle(_("Oszczędności"))
        self.resize(400, 250)
        l=QFormLayout(self)
        self.rd=QRadioButton(_("Wpłacam"))
        self.rw=QRadioButton(_("Wypłacam"))
        self.rd.setChecked(True)
        h=QHBoxLayout()
        h.addWidget(self.rd)
        h.addWidget(self.rw)
        self.date=QDateEdit(QDate.currentDate())
        h2=QHBoxLayout()
        self.g=QComboBox()
        self.g.addItem(CASH_SAVINGS_NAME)
        self.g.addItems(self.db.get_goals())
        b=QPushButton("+")
        b.setFixedWidth(30)
        b.clicked.connect(self.add_g)
        h2.addWidget(self.g)
        h2.addWidget(b)
        self.amt=QLineEdit()
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        l.addRow(h)
        l.addRow(_("Data:"), self.date)
        l.addRow(_("Cel:"), h2)
        l.addRow(_("Kwota:"), self.amt)
        l.addRow(bb)

    def add_g(self):
        d=AddGoalDialog(self,self.db)
        if d.exec():
            self.db.add_goal(*d.get_data())
            self.g.clear()
            self.g.addItem(CASH_SAVINGS_NAME)
            self.g.addItems(self.db.get_goals())

    def get_data(self):
        a=float(self.amt.text().replace(",", "."))
        if self.rw.isChecked(): a = -a
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "type": "savings",
            "cat": "Oszczędności", # Kategoria stała w bazie
            "sub": self.g.currentText(),
            "amount": a
        }

class TransferDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.setWindowTitle(_("Transfer"))
        self.resize(350, 200)
        l=QFormLayout(self)
        self.cf=QComboBox()
        self.ct=QComboBox()
        i=[CASH_SAVINGS_NAME] + db_manager.get_goals()
        self.cf.addItems(i)
        self.ct.addItems(i)
        self.amt=QLineEdit()
        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        l.addRow(_("Z:"), self.cf)
        l.addRow(_("Do:"), self.ct)
        l.addRow(_("Kwota:"), self.amt)
        l.addRow(bb)

    def get_data(self):
        return self.cf.currentText(), self.ct.currentText(), float(self.amt.text().replace(",", "."))

class LiabilitiesDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Zarządzaj Długami"))
        self.resize(450, 300)
        self.layout = QVBoxLayout(self)
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
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.layout.addWidget(self.form_widget)
        self.lbl_n = QLabel(_("Komu (Nazwa):"))
        self.n = QLineEdit()
        self.lbl_c = QLabel(_("Wybierz dług:"))
        self.c = QComboBox()
        self.a = QLineEdit()
        self.d = QDateEdit(QDate.currentDate())
        self.d.setCalendarPopup(True)
        self.lbl_date = QLabel(_("Data wpłaty:"))
        self.lbl_deadline = QLabel(_("Termin zwrotu:"))
        self.form_layout.addRow(self.lbl_n, self.n)
        self.form_layout.addRow(self.lbl_c, self.c)
        self.form_layout.addRow(_("Kwota:"), self.a)
        self.form_layout.addRow(self.lbl_deadline, self.d)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        self.toggle_mode()

    def toggle_mode(self):
        is_new = self.rb_new.isChecked()
        self.lbl_n.setVisible(is_new)
        self.n.setVisible(is_new)
        self.lbl_c.setVisible(not is_new)
        self.c.setVisible(not is_new)
        if is_new:
            self.a.setPlaceholderText(_("Całkowita kwota do oddania"))
            self.lbl_deadline.setText(_("Termin zwrotu:"))
            self.d.setDate(QDate.currentDate().addMonths(1))
        else:
            self.a.setPlaceholderText(_("Kwota wpłaty"))
            self.lbl_deadline.setText(_("Data wpłaty:"))
            self.d.setDate(QDate.currentDate())
            self.refresh_combo()

    def refresh_combo(self):
        self.c.clear()
        self.c.addItems(self.db.get_liabilities_list())

    def accept(self):
        from PySide6.QtWidgets import QMessageBox

        if self.rb_new.isChecked():
            if not self.n.text().strip(): QMessageBox.warning(self, _("Błąd"), _("Podaj nazwę!")); return
            if not self.a.text(): QMessageBox.warning(self, _("Błąd"), _("Podaj kwotę!")); return
        else:
            if self.c.count() == 0: QMessageBox.warning(self, _("Błąd"), _("Brak długów!")); return
            if not self.a.text(): QMessageBox.warning(self, _("Błąd"), _("Podaj kwotę!")); return
        super().accept()

    def get_data(self):
        amt = float(self.a.text().replace(",", "."))
        if self.rb_new.isChecked():
            return { "mode": "new", "name": self.n.text().strip(), "amount": amt, "deadline": self.d.date().toString("yyyy-MM-dd") }
        else:
            return { "mode": "pay", "name": self.c.currentText(), "amount": amt, "date": self.d.date().toString("yyyy-MM-dd") }

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
        l.addWidget(self.rm)
        l.addWidget(self.ry)
        h=QHBoxLayout()
        self.cm=QComboBox()
        self.cm.addItems(MONTH_NAME)
        self.cy=QSpinBox()
        self.cy.setRange(2020, 2050)
        self.cy.setValue(QDate.currentDate().year())
        h.addWidget(self.cm)
        h.addWidget(self.cy)
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
        self.db=db
        self.setWindowTitle(_("Edycja"))
        l=QFormLayout(self)
        self.d=QDateEdit(QDate.fromString(data[1],"yyyy-MM-dd"))
        self.c=QComboBox()
        self.c.setEditable(True)
        if data[2]=='expense': self.c.addItems(self.db.get_categories())
        elif data[2]=='income': self.c.addItems(self.db.get_people())
        else: self.c.addItem(data[3]); self.c.setEnabled(False)
        self.c.setCurrentText(data[3])
        self.s=QTextEdit()
        self.s.setText(data[4])
        self.s.setFixedHeight(50)
        self.a=QLineEdit(str(data[5]))
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        l.addRow(_("Data:"), self.d)
        l.addRow(_("Kat:"), self.c)
        l.addRow(_("Opis:"), self.s)
        l.addRow(_("Kwota:"), self.a)
        l.addRow(bb)

    def get_data(self):
        return self.d.date().toString("yyyy-MM-dd"), self.c.currentText(), self.s.toPlainText(), float(self.a.text().replace(",", "."))
