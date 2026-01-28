from datetime import datetime

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                               QGroupBox, QAbstractItemView,
                               QWidget, QListWidget, QComboBox)
from PySide6.QtCore import Qt

from config import _, DAYS_PL, MONTH_NAME

class ShoppingHistoryDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle(_("Archiwum List Zakupów"))
        self.resize(900, 500)
        self.selected_list_id = None
        self.selected_list_name = None

        main_layout = QHBoxLayout(self)

        # LEWA STRONA (Lista list)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel(_("Dostępne listy:")))

        self.table_lists = QTableWidget()
        self.table_lists.setColumnCount(4)
        self.table_lists.setHorizontalHeaderLabels([_("ID"), _("Nazwa"), _("Data"), _("Status")])
        self.table_lists.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_lists.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_lists.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_lists.setColumnHidden(0, True)
        self.table_lists.itemSelectionChanged.connect(self.show_preview)
        left_layout.addWidget(self.table_lists)

        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton(_("Otwórz / Edytuj"))
        self.btn_open.clicked.connect(self.open_selected)
        self.btn_close_list = QPushButton(_("Zamknij (status)"))
        self.btn_close_list.clicked.connect(self.close_selected_list)
        self.btn_del = QPushButton(_("Usuń"))
        self.btn_del.clicked.connect(self.delete_selected)
        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_close_list)
        btn_layout.addWidget(self.btn_del)
        left_layout.addLayout(btn_layout)
        main_layout.addWidget(left_widget, stretch=3)

        # PRAWA STRONA (Podgląd)
        right_group = QGroupBox(_("Podgląd produktów"))
        right_layout = QVBoxLayout(right_group)
        self.list_preview = QListWidget()
        self.list_preview.setFocusPolicy(Qt.NoFocus)
        self.list_preview.setStyleSheet("border: none;")
        right_layout.addWidget(self.list_preview)
        main_layout.addWidget(right_group, stretch=2)

        self.load_lists()

    def load_lists(self):
        from PySide6.QtGui import QColor

        self.table_lists.setRowCount(0)
        lists = self.db.get_shopping_lists()
        for r in lists:
            row_idx = self.table_lists.rowCount()
            self.table_lists.insertRow(row_idx)
            self.table_lists.setItem(row_idx, 0, QTableWidgetItem(str(r[0])))
            self.table_lists.setItem(row_idx, 1, QTableWidgetItem(r[1]))
            self.table_lists.setItem(row_idx, 2, QTableWidgetItem(r[2]))

            status_text = _("Zamknięta") if r[3] == 'closed' else _("Otwarta")
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor("gray") if r[3] == 'closed' else QColor("green"))
            self.table_lists.setItem(row_idx, 3, status_item)

    def show_preview(self):
        from collections import defaultdict

        self.list_preview.clear()
        row = self.table_lists.currentRow()
        if row < 0: return

        list_id = int(self.table_lists.item(row, 0).text())
        items = self.db.get_shopping_items(list_id)

        grouped = defaultdict(list)
        for item in items:
            store = item[3] if len(item) > 3 and item[3] else _("Inne")
            grouped[store].append(f"{item[1]} ({item[2]})")

        for store in sorted(grouped.keys()):
            self.list_preview.addItem(f"--- {store} ---")
            for prod in grouped[store]:
                self.list_preview.addItem(f"    • {prod}")
            self.list_preview.addItem("")

    def open_selected(self):
        row = self.table_lists.currentRow()
        if row < 0: return
        self.selected_list_id = int(self.table_lists.item(row, 0).text())
        self.selected_list_name = self.table_lists.item(row, 1).text()
        self.accept()

    def close_selected_list(self):
        row = self.table_lists.currentRow()
        if row < 0: return
        list_id = int(self.table_lists.item(row, 0).text())
        self.db.close_shopping_list(list_id)
        self.load_lists()

    def delete_selected(self):
        from PySide6.QtWidgets import QMessageBox

        row = self.table_lists.currentRow()
        if row < 0: return
        list_id = int(self.table_lists.item(row, 0).text())
        if QMessageBox.Yes == QMessageBox.question(self, _("Usuń"), _("Usunąć tę listę trwale?")):
            self.db.delete_shopping_list(list_id)
            self.load_lists()
            self.list_preview.clear()


class ShoppingListDialog(QDialog):
    def __init__(self, parent=None, db_manager=None, list_id=None, list_name=None):
        super().__init__(parent)
        self.db = db_manager
        self.list_id = list_id
        self.setWindowTitle(_("Lista Zakupów"))
        self.resize(750, 550)

        self.layout = QVBoxLayout(self)

        # --- GÓRA ---
        h_top = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(_("Nazwa listy"))
        self.name_edit.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")

        if list_name:
            self.name_edit.setText(list_name)
        else:
            today = datetime.now()
            day_name = DAYS_PL[today.weekday()]
            month_name = MONTH_NAME[today.month-1]
            default_name = _("{} {} {} ({})").format(today.day, month_name, today.year, day_name)
            self.name_edit.setText(default_name)

        h_top.addWidget(QLabel(_("Nazwa listy:")))
        h_top.addWidget(self.name_edit)
        self.layout.addLayout(h_top)

        # --- DODAWANIE ---
        gb_add = QGroupBox(_("Dodaj produkt"))
        h_add = QHBoxLayout()

        self.store_combo = QComboBox()
        self.store_combo.setEditable(True)
        self.store_combo.setPlaceholderText(_("Sklep (np. Biedronka)"))
        self.store_combo.setFixedWidth(130)
        self.refresh_shops()

        self.prod_edit = QLineEdit()
        self.prod_edit.setPlaceholderText(_("Produkt (np. Mleko)"))

        self.qty_edit = QLineEdit()
        self.qty_edit.setPlaceholderText(_("Ile"))
        self.qty_edit.setFixedWidth(70)

        self.store_combo.lineEdit().returnPressed.connect(self.prod_edit.setFocus)
        self.prod_edit.returnPressed.connect(self.qty_edit.setFocus)
        self.qty_edit.returnPressed.connect(self.add_item)

        btn_add = QPushButton(_("Dodaj"))
        btn_add.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_add.clicked.connect(self.add_item)

        h_add.addWidget(self.store_combo)
        h_add.addWidget(self.prod_edit)
        h_add.addWidget(self.qty_edit)
        h_add.addWidget(btn_add)
        gb_add.setLayout(h_add)
        self.layout.addWidget(gb_add)

        # --- TABELA ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([_("ID"), _("Sklep"), _("Produkt"), _("Ilość")])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.doubleClicked.connect(self.delete_item)
        self.layout.addWidget(self.table)

        # --- MENU DOLNE ---
        self.layout.addWidget(QLabel(_("--- Opcje ---")))
        h_actions = QHBoxLayout()

        self.btn_history = QPushButton(_("📜 Archiwum"))
        self.btn_history.clicked.connect(self.open_history)

        self.btn_print = QPushButton(_("🖨️ Drukuj (PDF)"))
        self.btn_print.clicked.connect(self.print_list)

        self.btn_email = QPushButton(_("📧 E-mail"))
        self.btn_email.clicked.connect(self.send_email)

        self.btn_finish = QPushButton(_("✓ Zakończ listę"))
        self.btn_finish.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 5px;")
        self.btn_finish.clicked.connect(self.finalize_list)

        self.btn_close = QPushButton(_("Wyjdź"))
        self.btn_close.clicked.connect(self.accept)

        h_actions.addWidget(self.btn_history)
        h_actions.addStretch()
        h_actions.addWidget(self.btn_print)
        h_actions.addWidget(self.btn_email)
        h_actions.addWidget(self.btn_finish)
        h_actions.addWidget(self.btn_close)
        self.layout.addLayout(h_actions)

        self.load_items()

    def refresh_shops(self):
        current = self.store_combo.currentText()
        self.store_combo.clear()
        shops = self.db.get_shops()
        self.store_combo.addItems(shops)
        self.store_combo.setCurrentText(current)

    def _ensure_list_exists(self):
        if self.list_id is None:
            self.list_id = self.db.create_shopping_list(self.name_edit.text())

    def load_items(self):
        self.table.setRowCount(0)
        if self.list_id is None:
            return

        items = self.db.get_shopping_items(self.list_id)
        for r in items:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(r[0])))
            store_str = r[3] if len(r) > 3 and r[3] else ""
            self.table.setItem(row_idx, 1, QTableWidgetItem(store_str))
            self.table.setItem(row_idx, 2, QTableWidgetItem(r[1]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(r[2]))

    def add_item(self):
        prod = self.prod_edit.text().strip()
        store = self.store_combo.currentText().strip()
        raw_qty = self.qty_edit.text().strip()

        if not prod: return
        if not raw_qty: raw_qty = "1"
        clean_qty = raw_qty.lower().replace("szt.", "").replace("szt", "").strip()
        final_qty = f"{clean_qty} szt."

        self._ensure_list_exists()

        if store:
            self.db.add_shop(store)

        self.db.add_shopping_item(self.list_id, prod, final_qty, store)

        self.prod_edit.clear()
        self.qty_edit.clear()
        self.prod_edit.setFocus()
        self.load_items()

        self.refresh_shops()
        self.store_combo.setCurrentText(store)

    def delete_item(self):
        row = self.table.currentRow()
        if row < 0: return
        item_id = int(self.table.item(row, 0).text())
        self.db.delete_shopping_item(item_id)
        self.load_items()

    def _force_status_update(self, status):
        if self.list_id is not None:
            try:
                self.db.conn.execute("UPDATE shopping_lists SET status=? WHERE id=?", (status, self.list_id))
                self.db.conn.commit()
            except: pass

    def print_list(self):
        import sys
        import os
        import tempfile
        import subprocess
        from PySide6.QtWidgets import QMessageBox
        from reports import ShoppingPDFGenerator, PDF_FILES_TO_CLEAN

        self._ensure_list_exists()
        items = []
        for row in range(self.table.rowCount()):
            store = self.table.item(row, 1).text()
            prod = self.table.item(row, 2).text()
            qty = self.table.item(row, 3).text()
            items.append((prod, qty, store))

        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%H%M%S")
        safe_name = self.name_edit.text().replace("/", "_").replace(" ", "_")
        pdf_path = os.path.join(temp_dir, f"zakupy_{safe_name}_{timestamp}.pdf")

        try:
            gen = ShoppingPDFGenerator()
            gen.generate(pdf_path, self.name_edit.text(), items)
            PDF_FILES_TO_CLEAN.append(pdf_path)
            self._force_status_update('closed')

            if sys.platform == "win32":
                os.startfile(pdf_path)
            else:
                subprocess.call(['xdg-open', pdf_path])

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, _("Błąd"), _("Nie udało się wygenerować PDF:\n{}").format(str(e)))

    def send_email(self):
        import urllib.parse
        from collections import defaultdict
        from PySide6.QtCore import QUrl, QTimer
        from PySide6.QtGui import QDesktopServices

        self._ensure_list_exists()

        grouped = defaultdict(list)
        for row in range(self.table.rowCount()):
            store = self.table.item(row, 1).text()
            if not store: store = _("Inne")
            prod = self.table.item(row, 2).text().upper()
            qty = self.table.item(row, 3).text().lower()
            grouped[store].append(f"[ ] {prod} ({qty})")

        items_str = ""
        for store in sorted(grouped.keys()):
            items_str += f"\n--- {store} ---\n"
            for item_line in grouped[store]:
                items_str += item_line + "\n"

        subject = urllib.parse.quote(_("ZAKUPY: {}").format(self.name_edit.text()))
        body_content = _("LISTA: {}\n{}\n\n--\nBudżet Domowy").format(self.name_edit.text(), items_str)
        body = urllib.parse.quote(body_content)

        url = QUrl(f"mailto:?subject={subject}&body={body}")
        self._force_status_update('closed')
        QDesktopServices.openUrl(url)
        QTimer.singleShot(2000, self.accept)

    def finalize_list(self):
        if self.list_id is not None:
            self._force_status_update('closed')
        self.accept()

    def open_history(self):
        dlg = ShoppingHistoryDialog(self, self.db)
        if dlg.exec() == QDialog.Accepted:
            if dlg.selected_list_id is not None:
                self.list_id = dlg.selected_list_id
                self.name_edit.setText(dlg.selected_list_name)
                self._force_status_update('open')
                self.load_items()
