import sys
import os
from datetime import datetime, timedelta

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                               QGroupBox, QMessageBox, QAbstractItemView, QFrame, QSpinBox,
                               QFileDialog, QProgressBar, QSizePolicy, QMenu, QScrollArea,
                               QButtonGroup, QCheckBox)
from PySide6.QtCore import Qt, QSettings, QDate, QTimer, QTranslator, QLibraryInfo, QLocale
from PySide6.QtGui import QColor, QPalette, QIcon, QKeyEvent, QAction

# IMPORTY MODUŁOWE (Nasza nowa struktura)
from config import (WERSJA, PRODUCENT, APP_DIR, setup_crash_handlers, _,
                    MONTH_NAME, CASH_SAVINGS_NAME, BASE_DIR, APPNAME)
from database import DatabaseManager
from charts import BudgetChart

class BudgetApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. Inicjalizacja podstawowa
        self.setWindowTitle(f"{APPNAME}")
        self.resize(1200, 950)
        self.db = DatabaseManager()
        self.settings = QSettings("BudgetApp", "Config")
        self.pdf_gen = None
        self.active_filter_cat = None
        self.weekly_filter_cat = None
        self.week_offset = 0

        # Ikona aplikacji
        icon_path = os.path.join(BASE_DIR, "budget.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Timer do odświeżania (debounce)
        self.update_timer = QTimer()
        self.update_timer.setInterval(300)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.load_transactions)

        # 2. Budowa Interfejsu (UI)
        c = QWidget(); self.setCentralWidget(c); self.main_layout = QVBoxLayout(c)
        self.setup_top_bar()
        self.setup_dashboard()
        self.setup_buttons()
        self.setup_table()
        self.setup_footer()

        # 3. Przywracanie stanu okna
        if g := self.settings.value("geometry"): self.restoreGeometry(g)
        if s := self.settings.value("windowState"): self.restoreState(s)

        # Przywracanie ostatnio wybranego miesiąca
        ly = self.settings.value("last_year", type=int)
        lm = self.settings.value("last_month", type=int)
        today = QDate.currentDate()
        if ly and lm is not None:
            self.sel_year.setValue(ly)
            self.sel_month.setCurrentIndex(lm)
        else:
            self.sel_year.setValue(today.year())
            self.sel_month.setCurrentIndex(today.month() - 1)

        # Podpięcie zdarzeń wykresu
        self.chart.mpl_connect('pick_event', self.on_chart_pick)

        # 4. Start
        self.load_transactions()
        self.check_new_week_prompt()

        # Logika opóźnionego kliknięcia w wykres (fix crashy)
        self._pending_category_click = None
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._process_delayed_click_logic)

    def check_new_week_prompt(self):
        from dialogs import WeeklyLimitDialog

        if not self.db.is_weekly_system_enabled():
            return

        today = datetime.now().date()
        monday_real = today - timedelta(days=today.weekday())
        monday_str = monday_real.strftime("%Y-%m-%d")

        found, _, _ = self.db.get_weekly_limit_for_week(monday_str)

        if not found:
            dlg = WeeklyLimitDialog(self, self.db, target_monday_date=monday_str)
            if dlg.exec():
                def safe_startup_refresh():
                    self.chart.setVisible(False)
                    self.weekly_widget.setVisible(True)
                    self.load_transactions()
                QTimer.singleShot(10, safe_startup_refresh)

    def setup_top_bar(self):
        from dialogs import BackupDialog
        from shopping import ShoppingListDialog

        l = QHBoxLayout(); l.setContentsMargins(0, 0, 0, 10)
        lbl = QLabel(_("Okres:"))
        lbl.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.sel_year = QSpinBox()
        self.sel_year.setRange(2020, 2050)
        self.sel_year.valueChanged.connect(self.schedule_update)

        self.sel_month = QComboBox()
        self.sel_month.addItems(MONTH_NAME)
        self.sel_month.currentIndexChanged.connect(self.schedule_update)

        btn_back = QPushButton(_("Backup"))
        btn_back.clicked.connect(lambda: BackupDialog(self, self.db).exec())

        # SEARCH BAR
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(_("Szukaj: '19zł', 'czynsz', '21.06'..."))
        self.search_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_bar.textChanged.connect(self.schedule_update)

        btn_shop = QPushButton(_("🛒 Zakupy"))
        btn_shop.clicked.connect(lambda: ShoppingListDialog(self, self.db).exec())

        self.btn_filter = QPushButton(_("🔍 Filtruj"))
        self.btn_filter.clicked.connect(self.open_filter_dialog)

        self.btn_weekly = QPushButton(_("📅 Limit Tygodnia"))
        self.btn_weekly.clicked.connect(self.open_weekly_settings_safe)

        self.btn_pdf = QPushButton(_("📄 PDF"))
        self.btn_pdf.clicked.connect(self.open_report_dialog)

        self.btn_close_month = QPushButton(_("🔒 Zamknij Miesiąc"))
        self.btn_close_month.clicked.connect(self.toggle_month_lock)

        l.addWidget(lbl); l.addWidget(self.sel_month); l.addWidget(self.sel_year); l.addWidget(btn_back)
        l.addSpacing(20)
        l.addWidget(self.search_bar, 1)
        l.addSpacing(20)
        l.addWidget(self.btn_weekly); l.addWidget(btn_shop); l.addWidget(self.btn_filter); l.addWidget(self.btn_pdf); l.addWidget(self.btn_close_month)
        self.main_layout.addLayout(l)

    def schedule_update(self): self.update_timer.start()

    def open_weekly_settings(self):
        from dialogs import WeeklyLimitDialog

        today = datetime.now().date()
        target = today + timedelta(weeks=self.week_offset)
        monday = target - timedelta(days=target.weekday())
        monday_str = monday.strftime("%Y-%m-%d")

        dlg = WeeklyLimitDialog(self, self.db, target_monday_date=monday_str)

        if dlg.exec():
            def safe_delayed_update():
                is_enabled = self.db.is_weekly_system_enabled()
                if is_enabled:
                    self.chart.setVisible(False)
                    self.weekly_widget.setVisible(True)
                else:
                    self.chart.setVisible(True)
                    self.weekly_widget.setVisible(False)
                    self.weekly_filter_cat = None
                self.load_transactions()
            QTimer.singleShot(50, safe_delayed_update)

    def open_weekly_settings_safe(self):
        self.update_timer.stop()
        self.open_weekly_settings()

    def setup_dashboard(self):
        dash_group = QGroupBox(_("Bilans Miesięczny"))
        dash_layout = QHBoxLayout()

        stats_widget = QWidget()
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(5)
        stats_layout.setContentsMargins(0,0,0,0)

        # --- DEFINICJA LABELI ---
        self.lbl_balance = QLabel(_("SALDO: 0.00 PLN"))
        self.lbl_balance.setStyleSheet("font-size: 22px; font-weight: bold; color: #2ecc71;")

        self.lbl_prev_balance = QLabel(_("z poprzedniego miesiąca: 0.00 PLN"))
        self.lbl_prev_balance.setStyleSheet("font-size: 13px; color: gray;")

        self.lbl_expenses_month = QLabel(_("Wydatki (ten msc): 0.00 PLN"))
        self.lbl_expenses_month.setStyleSheet("font-size: 14px; color: #c0392b; font-weight: bold; margin-top: 10px;")

        self.lbl_savings_month = QLabel(_("Oszczędności Gotówka (ten msc): 0.00 PLN"))
        self.lbl_savings_month.setStyleSheet("font-size: 14px; color: #2874A6;")

        self.lbl_income_breakdown = QLabel(_("Przychody..."))
        self.lbl_income_breakdown.setStyleSheet("font-size: 13px; color: #555;")
        self.lbl_income_breakdown.setAlignment(Qt.AlignRight | Qt.AlignTop)

        self.lbl_savings_total = QLabel(_("ŁĄCZNIE (GOTÓWKA): 0.00 PLN"))
        self.lbl_savings_total.setStyleSheet("font-size: 13px; color: #1F618D; font-weight: bold; margin-top: 5px; border-top: 1px solid #ccc; padding-top: 5px;")

        top_split_layout = QHBoxLayout()
        top_left_v = QVBoxLayout()
        top_left_v.addWidget(self.lbl_balance)
        top_left_v.addWidget(self.lbl_prev_balance)
        top_left_v.addWidget(self.lbl_expenses_month)
        top_left_v.addWidget(self.lbl_savings_month)
        top_left_v.addStretch()

        top_right_v = QVBoxLayout()
        inc_header = QLabel(_("Wpływy:"))
        inc_header.setStyleSheet("color:#555; font-weight:bold;")
        inc_header.setAlignment(Qt.AlignRight)
        top_right_v.addWidget(inc_header)
        top_right_v.addWidget(self.lbl_income_breakdown)
        top_right_v.addStretch()

        top_split_layout.addLayout(top_left_v, 60)
        top_split_layout.addLayout(top_right_v, 40)
        stats_layout.addLayout(top_split_layout)

        # --- CELE OSZCZĘDNOŚCIOWE ---
        self.goals_box = QGroupBox(_("Oszczędzamy na:"))
        self.goals_box.setStyleSheet("""
            QGroupBox { border: 1px solid #3498db; border-radius: 5px; margin-top: 7px; font-weight: bold; color: #2874A6; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
        """)
        self.goals_lay = QVBoxLayout()
        self.goals_lay.setContentsMargins(10, 5, 10, 5)
        self.goals_list_layout = QVBoxLayout()
        self.goals_list_layout.setSpacing(8)

        h = QHBoxLayout()
        btn_tr = QPushButton(_("⇄ Transfer"))
        btn_tr.setFixedWidth(65)
        btn_tr.setStyleSheet("font-size:10px; padding:2px; background:#5DADE2; color:white; border-radius:3px;")
        btn_tr.clicked.connect(self.open_transfer_dialog)

        btn_add = QPushButton(_("+ Cel"))
        btn_add.setFixedWidth(40)
        btn_add.setStyleSheet("font-size:10px; padding:2px;")
        btn_add.clicked.connect(self.open_new_goal_dialog)

        h.addWidget(QLabel(_("Postęp:"))); h.addStretch(); h.addWidget(btn_tr); h.addWidget(btn_add)
        self.goals_lay.addLayout(h)
        self.goals_lay.addLayout(self.goals_list_layout)
        self.goals_box.setLayout(self.goals_lay)

        # --- DŁUGI ---
        self.lia_box = QGroupBox(_("Do oddania:"))
        self.lia_box.setStyleSheet("""
            QGroupBox { border: 1px solid #e74c3c; border-radius: 5px; margin-top: 7px; font-weight: bold; color: #c0392b; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
        """)
        self.liabilities_layout = QVBoxLayout()
        self.liabilities_layout.setContentsMargins(10, 5, 10, 5)
        self.liabilities_layout.setSpacing(8)
        self.lia_box.setLayout(self.liabilities_layout)
        self.lia_box.hide()

        stats_layout.addWidget(self.lbl_savings_total)
        stats_layout.addWidget(self.goals_box)
        stats_layout.addWidget(self.lia_box)

        stats_widget.setLayout(stats_layout)

        # --- PRAWY PANEL ---
        self.right_panel = QWidget()
        self.right_panel_layout = QVBoxLayout(self.right_panel)
        self.right_panel_layout.setContentsMargins(0,0,0,0)

        self.chart = BudgetChart(self, width=4.0, height=3.0)

        self.weekly_widget = QWidget()
        self.weekly_ui_layout = QVBoxLayout(self.weekly_widget)
        self.setup_weekly_ui()
        self.weekly_widget.hide()

        self.right_panel_layout.addWidget(self.chart)
        self.right_panel_layout.addWidget(self.weekly_widget)

        dash_layout.addWidget(stats_widget, stretch=1)
        dash_layout.addWidget(self.right_panel, stretch=1)
        dash_group.setLayout(dash_layout)
        self.main_layout.addWidget(dash_group)

    def setup_weekly_ui(self):
        nav_layout = QHBoxLayout()

        btn_prev = QPushButton("<")
        btn_prev.setFixedSize(30, 30)
        btn_prev.clicked.connect(lambda: self.change_week(-1))

        self.lbl_week_range = QLabel("...")
        self.lbl_week_range.setStyleSheet("font-weight: bold; font-size: 15px; color: #333;")
        self.lbl_week_range.setAlignment(Qt.AlignCenter)

        btn_next = QPushButton(">")
        btn_next.setFixedSize(30, 30)
        btn_next.clicked.connect(lambda: self.change_week(1))

        nav_layout.addWidget(btn_prev)
        nav_layout.addWidget(self.lbl_week_range, stretch=1)
        nav_layout.addWidget(btn_next)

        self.lbl_current_limit = QLabel(_("Limit: 0.00 zł"))
        self.lbl_current_limit.setStyleSheet("color: #555; font-size: 12px; font-weight: bold;")
        self.lbl_current_limit.setAlignment(Qt.AlignCenter)

        self.weekly_pbar = QProgressBar()
        self.weekly_pbar.setFixedHeight(15)
        self.weekly_pbar.setAlignment(Qt.AlignCenter)

        self.lbl_weekly_spent = QLabel(_("Wydano: 0.00 zł"))
        self.lbl_weekly_spent.setStyleSheet("color: #c0392b; font-size: 12px;")

        self.lbl_weekly_remaining = QLabel(_("Pozostało w tym tygodniu: 0.00 zł"))
        self.lbl_weekly_remaining.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")

        self.lbl_last_week_saved = QLabel(_("Z poprzedniego tygodnia wróciło: 0.00 zł"))
        self.lbl_last_week_saved.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 11px;")

        self.lbl_month_savings = QLabel(_("Udało się zaoszczędzić w tym miesiącu: 0.00 zł"))
        self.lbl_month_savings.setStyleSheet("color: #2980b9; font-weight: bold; font-size: 12px; margin-bottom: 5px;")

        self.lbl_cat_head = QLabel(_("Struktura wydatków:"))
        self.lbl_cat_head.setStyleSheet("font-weight: bold; margin-top: 10px;")

        self.weekly_cat_area = QScrollArea()
        self.weekly_cat_area.setWidgetResizable(True)
        self.weekly_cat_area.setStyleSheet("background: transparent; border: none;")

        self.weekly_cat_container = QWidget()
        self.weekly_cat_layout = QVBoxLayout(self.weekly_cat_container)
        self.weekly_cat_layout.setContentsMargins(0, 0, 0, 0)
        self.weekly_cat_area.setWidget(self.weekly_cat_container)

        self.weekly_ui_layout.addLayout(nav_layout)
        self.weekly_ui_layout.addWidget(self.lbl_current_limit)
        self.weekly_ui_layout.addWidget(self.weekly_pbar)

        h_nums = QHBoxLayout()
        h_nums.addWidget(self.lbl_weekly_spent)
        h_nums.addStretch()
        h_nums.addWidget(self.lbl_weekly_remaining)
        self.weekly_ui_layout.addLayout(h_nums)

        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setStyleSheet("background: #ccc;")
        self.weekly_ui_layout.addWidget(line)
        self.weekly_ui_layout.addWidget(self.lbl_last_week_saved)
        self.weekly_ui_layout.addWidget(self.lbl_month_savings)

        self.weekly_ui_layout.addWidget(self.lbl_cat_head)
        self.weekly_ui_layout.addWidget(self.weekly_cat_area, stretch=1)

    def change_week(self, offset):
        self.week_offset += offset
        self.load_transactions(refresh_panel=True)

    def update_weekly_stats_no_data(self):
        self.weekly_widget.setVisible(True)
        self.chart.setVisible(False)

        today_real = datetime.now().date()
        target_date = today_real + timedelta(weeks=self.week_offset)
        start_of_week = target_date - timedelta(days=target_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        range_str = f"{start_of_week.strftime('%d.%m')} - {end_of_week.strftime('%d.%m')}"

        if self.week_offset == 0:
            self.lbl_week_range.setText(_("Obecny: {}").format(range_str))
            self.lbl_week_range.setStyleSheet("font-weight: bold; font-size: 15px; color: #27ae60;")
        else:
            self.lbl_week_range.setText(_("Tydzień: {}").format(range_str))
            self.lbl_week_range.setStyleSheet("font-weight: bold; font-size: 15px;")

        self.lbl_current_limit.setText(_("Brak limitu na ten tydzień"))
        self.lbl_cat_head.setText("")
        self.weekly_pbar.setValue(0)
        self.weekly_pbar.setFormat("")
        self.lbl_weekly_spent.setText("")
        self.lbl_weekly_remaining.setText(_("Użyj 📅 Limit Tygodnia, aby ustalić limit."))
        self.lbl_weekly_remaining.setStyleSheet("color: gray; font-style: italic;")
        self.lbl_last_week_saved.setText("")
        self.lbl_month_savings.setText("")

        while self.weekly_cat_layout.count():
            item = self.weekly_cat_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def update_weekly_stats(self, weekly_enabled, weekly_limit, weekly_cats=None):
        if not weekly_enabled:
            self.chart.setVisible(True)
            self.weekly_widget.setVisible(False)
            self.weekly_filter_cat = None
            self.week_offset = 0
            return

        self.chart.setVisible(False)
        self.weekly_widget.setVisible(True)

        today_real = datetime.now().date()
        target_date = today_real + timedelta(weeks=self.week_offset)

        start_of_week = target_date - timedelta(days=target_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        s_str = start_of_week.strftime("%Y-%m-%d")
        e_str = end_of_week.strftime("%Y-%m-%d")
        range_str = f"{start_of_week.strftime('%d.%m')} - {end_of_week.strftime('%d.%m')}"

        if self.week_offset == 0:
            self.lbl_week_range.setText(_("Obecny: {}").format(range_str))
            self.lbl_week_range.setStyleSheet("font-weight: bold; font-size: 15px; color: #27ae60;")
        else:
            self.lbl_week_range.setText(_("Tydzień: {}").format(range_str))
            self.lbl_week_range.setStyleSheet("font-weight: bold; font-size: 15px;")

        self.lbl_current_limit.setText(_("Limit tygodniowy: {:.2f} zł").format(weekly_limit))
        self.lbl_cat_head.setText(_("Struktura ({}):").format(range_str))

        cat_data = self.db.get_expenses_in_range(s_str, e_str, weekly_cats)

        total_spent = sum(amt for cat, amt in cat_data)
        remaining = weekly_limit - total_spent

        if weekly_limit > 0: pct = int((remaining / weekly_limit) * 100)
        else: pct = 0

        visual_pct = max(0, min(100, pct))
        self.weekly_pbar.setValue(visual_pct)
        self.weekly_pbar.setFormat(f"{pct}%")

        if pct > 50: col = "#2ecc71"
        elif pct > 20: col = "#f39c12"
        else: col = "#e74c3c"

        self.weekly_pbar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid palette(mid);
                border-radius: 3px;
                text-align: center;
                background: transparent;
            }}
            QProgressBar::chunk {{
                background-color: {col};
            }}
        """)

        self.lbl_weekly_spent.setText(_("Wydano: {:.2f} zł").format(total_spent))
        if remaining < 0:
            self.lbl_weekly_remaining.setText(_("Przekroczono: {:.2f} zł").format(abs(remaining)))
            self.lbl_weekly_remaining.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px;")
        else:
            self.lbl_weekly_remaining.setText(_("Pozostało: {:.2f} zł").format(remaining))
            self.lbl_weekly_remaining.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")

        # Logika poprzedniego tygodnia
        prev_start = start_of_week - timedelta(days=7)
        prev_end = prev_start + timedelta(days=6)
        prev_s_str = prev_start.strftime("%Y-%m-%d")

        found_prev, prev_limit, prev_cats = self.db.get_weekly_limit_for_week(prev_s_str)

        if found_prev:
            prev_data = self.db.get_expenses_in_range(prev_s_str, prev_end.strftime("%Y-%m-%d"), prev_cats)
            prev_spent = sum(amt for cat, amt in prev_data)
            prev_saved = max(0, prev_limit - prev_spent)
            self.lbl_last_week_saved.setText(_("Z poprzedniego tygodnia wróciło: {:.2f} zł").format(prev_saved))
        else:
            self.lbl_last_week_saved.setText(_("Poprzedni tydzień: brak ustaleń"))

        # Logika oszczędności w miesiącu
        viewed_month_idx = end_of_week.month
        accumulated_savings = 0.0
        check_sunday = end_of_week

        while check_sunday.month == viewed_month_idx:
            if check_sunday < today_real:
                check_monday = check_sunday - timedelta(days=6)
                c_s_str = check_monday.strftime("%Y-%m-%d")
                c_e_str = check_sunday.strftime("%Y-%m-%d")

                h_found, h_limit, h_cats = self.db.get_weekly_limit_for_week(c_s_str)
                if h_found:
                    w_data = self.db.get_expenses_in_range(c_s_str, c_e_str, h_cats)
                    w_spent = sum(amt for cat, amt in w_data)
                    accumulated_savings += max(0, h_limit - w_spent)
            check_sunday -= timedelta(days=7)

        current_month_name = MONTH_NAME[viewed_month_idx - 1]
        self.lbl_month_savings.setText(_("Udało się zaoszczędzić w miesiącu {}: {:.2f} zł").format(current_month_name, accumulated_savings))

        # Lista kategorii
        while self.weekly_cat_layout.count():
            item = self.weekly_cat_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not cat_data:
            lbl = QLabel(_("Brak wydatków."))
            lbl.setStyleSheet("color: gray; font-style: italic; margin-top: 10px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.weekly_cat_layout.addWidget(lbl)
        else:
            for cat, amt in cat_data:
                cat_pct = int((amt / total_spent) * 100) if total_spent > 0 else 0
                row_w = QWidget(); row_l = QHBoxLayout(row_w); row_l.setContentsMargins(0, 2, 0, 2)
                is_active = (self.weekly_filter_cat == cat)

                btn_name = QPushButton(f"{cat}")
                btn_name.setCursor(Qt.PointingHandCursor)
                if is_active:
                    btn_name.setStyleSheet("QPushButton { text-align: left; font-weight: bold; color: #3498db; border: none; background: transparent; }")
                else:
                    btn_name.setStyleSheet("QPushButton { text-align: left; color: palette(text); border: none; background: transparent; } QPushButton:hover { color: #3498db; text-decoration: underline; }")

                btn_name.clicked.connect(lambda _, c=cat: self._handle_text_category_click(c))

                lbl_amt = QLabel(f"{amt:.2f} zł ({cat_pct}%)")
                lbl_amt.setAlignment(Qt.AlignRight)
                if is_active:
                    lbl_amt.setStyleSheet("font-weight: bold; color: #3498db;")

                row_l.addWidget(btn_name, stretch=1)
                row_l.addWidget(lbl_amt)
                self.weekly_cat_layout.addWidget(row_w)

        self.weekly_cat_layout.addStretch()
        return remaining

    def _handle_text_category_click(self, category):
        if self.weekly_filter_cat == category:
            self.weekly_filter_cat = None
        else:
            self.weekly_filter_cat = category
        QTimer.singleShot(50, self._execute_safe_chart_update)

    def setup_buttons(self):
        l = QHBoxLayout()

        base_style = """
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
                border-radius: 8px;
                border: 2px solid;
                background-color: transparent;
            }
        """
        inc_style = base_style + """ QPushButton { color: #155724; border-color: #28a745; } QPushButton:hover { background-color: #d4edda; } """
        exp_style = base_style + """ QPushButton { color: #721c24; border-color: #dc3545; } QPushButton:hover { background-color: #f8d7da; } """
        sav_style = base_style + """ QPushButton { color: #2874A6; border-color: #3498db; } QPushButton:hover { background-color: #d6eaf8; } """
        lia_style = base_style + """ QPushButton { color: #922b21; border-color: #e74c3c; } QPushButton:hover { background-color: #fadbd8; } """

        self.btn_income = QPushButton(_("+ DODAJ PRZYCHÓD"))
        self.btn_income.setStyleSheet(inc_style)
        self.btn_income.clicked.connect(self.open_income_dialog)

        self.btn_expense = QPushButton(_("- DODAJ WYDATEK"))
        self.btn_expense.setStyleSheet(exp_style)
        self.btn_expense.clicked.connect(self.open_expense_dialog)

        self.btn_savings = QPushButton(_("$$ OSZCZĘDNOŚCI"))
        self.btn_savings.setStyleSheet(sav_style)
        self.btn_savings.clicked.connect(self.open_savings_dialog)

        self.btn_liabilities = QPushButton(_("!! DO ODDANIA"))
        self.btn_liabilities.setStyleSheet(lia_style)
        self.btn_liabilities.clicked.connect(self.open_liabilities_dialog)

        self.btns = [self.btn_income, self.btn_expense, self.btn_savings, self.btn_liabilities]
        for b in self.btns: l.addWidget(b)
        self.main_layout.addLayout(l)

    def setup_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([_("ID"), _("Data"), _("Kto/Kategoria"), _("Opis"), _("Kwota")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setColumnHidden(0, True)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        self.table.doubleClicked.connect(self.open_edit_dialog)
        self.main_layout.addWidget(self.table, 2)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Delete and self.table.hasFocus(): self.delete_selected_transaction()
        super().keyPressEvent(e)

    def open_context_menu(self, position):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows: return
        menu = QMenu()
        is_locked = self.db.is_month_locked(self.get_current_month_str())

        if len(selected_rows) == 1 and not is_locked:
            edit_action = QAction(_("Edytuj"), self)
            edit_action.triggered.connect(self.open_edit_dialog)
            menu.addAction(edit_action)

        if not is_locked:
            del_action = QAction(_("Usuń ({})").format(len(selected_rows)), self)
            del_action.triggered.connect(self.delete_selected_transaction)
            menu.addAction(del_action)

        if not menu.isEmpty():
            menu.exec(self.table.viewport().mapToGlobal(position))

    def setup_footer(self):
        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        lbl_version = QLabel(f" {WERSJA} ")
        lbl_version.setStyleSheet("color: gray; font-size: 10px;")
        current_year = datetime.now().year
        start_year = 2026
        year_str = f"{start_year} - {current_year}" if current_year > start_year else str(start_year)
        copy_text = f"{PRODUCENT} {year_str}"
        lbl_copy = QLabel(copy_text)
        lbl_copy.setStyleSheet("color: gray; font-size: 10px;")
        lbl_copy.setAlignment(Qt.AlignRight)
        footer_layout.addWidget(lbl_version)
        footer_layout.addStretch()
        footer_layout.addWidget(lbl_copy)
        self.main_layout.addWidget(footer_widget)

    def get_current_month_str(self): return f"{self.sel_year.value()}-{self.sel_month.currentIndex()+1:02d}"

    def toggle_month_lock(self):
        m = self.get_current_month_str(); locked = self.db.is_month_locked(m)
        act = _("ODBLOKOWAĆ") if locked else _("ZAMKNĄĆ")
        if QMessageBox.Yes == QMessageBox.question(self, _("Miesiąc"), _("Czy na pewno chcesz {} miesiąc {}?").format(act, m)):
            if locked: self.db.unlock_month(m)
            else: self.db.lock_month(m)
            self.schedule_update()

    def load_transactions(self, refresh_panel=True):
        import re

        if hasattr(self, 'update_timer'): self.update_timer.stop()

        weekly_system_on = self.db.is_weekly_system_enabled()
        weekly_view_active = self.weekly_widget.isVisible()
        if weekly_system_on and not self.chart.isVisible(): weekly_view_active = True

        if weekly_view_active: self.active_filter_cat = None
        else: self.weekly_filter_cat = None

        m_str = self.get_current_month_str()
        search = self.search_bar.text().lower().strip()
        is_searching = bool(search)

        today_real = datetime.now().date()
        target_date = today_real + timedelta(weeks=self.week_offset)
        start_of_displayed_week = target_date - timedelta(days=target_date.weekday())
        end_of_displayed_week = start_of_displayed_week + timedelta(days=6)
        s_date_str = start_of_displayed_week.strftime("%Y-%m-%d")
        e_date_str = end_of_displayed_week.strftime("%Y-%m-%d")

        reserved_for_week = 0.0
        weekly_limit_amount = 0.0
        weekly_limit_cats = []

        if weekly_system_on and weekly_view_active:
            found, amt, cats = self.db.get_weekly_limit_for_week(s_date_str)
            if found:
                weekly_limit_amount = amt
                weekly_limit_cats = cats
                if refresh_panel: self.update_weekly_stats(True, weekly_limit_amount, weekly_limit_cats)

                real_start = today_real - timedelta(days=today_real.weekday())
                if s_date_str == real_start.strftime("%Y-%m-%d"):
                    real_expenses = self.db.get_expenses_in_range(s_date_str, e_date_str, weekly_limit_cats)
                    real_spent = sum(amt for c, amt in real_expenses)
                    rem_real = weekly_limit_amount - real_spent
                    if rem_real > 0: reserved_for_week = rem_real
            else:
                if refresh_panel: self.update_weekly_stats_no_data()
        else:
            if refresh_panel: self.update_weekly_stats(False, 0, None)

        if is_searching:
            for i, n in enumerate(MONTH_NAME):
                if n.lower() in search: search = search.replace(n.lower(), f"{i+1:02d}")
            if "." in search:
                dm = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", search)
                if dm: search = f"{dm.group(3)}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}"

        search_amount = None
        clean_num_str = search.replace("zł", "").replace(" ", "").replace(",", ".").strip()
        if clean_num_str:
            try: search_amount = float(clean_num_str)
            except ValueError: search_amount = None

        locked = self.db.is_month_locked(m_str)
        for b in self.btns: b.setEnabled(not locked)

        if locked:
            self.btn_close_month.setText(_("🔒 ODBLOKUJ MIESIĄC"))
            self.btn_close_month.setStyleSheet("background:#c0392b;color:white;font-weight:bold")
        else:
            self.btn_close_month.setText(_("🔒 Zamknij Miesiąc"))
            self.btn_close_month.setStyleSheet("background:#95a5a6;color:white")

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setRowCount(0)
        rows = self.db.get_all_transactions()

        stats_inc = stats_exp = stats_sav = stats_lia = 0.0
        inc_map = {}; exp_map = {}

        for r in rows:
            tid, tdate, ttype, tcat, tsub, tamt = r
            show = False

            if weekly_system_on and weekly_view_active and self.weekly_filter_cat:
                if tcat == self.weekly_filter_cat and s_date_str <= tdate <= e_date_str and ttype == 'expense': show = True
            elif (not weekly_view_active) and self.active_filter_cat:
                if tcat == self.active_filter_cat:
                    if tdate.startswith(m_str): show = True
            else:
                if not is_searching:
                    if tdate.startswith(m_str): show = True
                else:
                    is_amount_match = False
                    if search_amount is not None:
                        if search_amount.is_integer():
                            if int(tamt) == int(search_amount): is_amount_match = True
                        else:
                            if abs(tamt - search_amount) < 0.01: is_amount_match = True
                    txt_match = (search in tdate.lower()) or (search in tcat.lower()) or (search in tsub.lower()) or (search in str(tamt))
                    if "zł" in self.search_bar.text().lower() and search_amount is not None: show = is_amount_match
                    else: show = txt_match or is_amount_match

            if show:
                idx = self.table.rowCount(); self.table.insertRow(idx)
                self.table.setItem(idx, 0, QTableWidgetItem(str(tid)))
                self.table.setItem(idx, 1, QTableWidgetItem(tdate))
                display_cat = tcat
                display_desc = tsub
                if ttype == 'savings':
                    display_cat = _("Oszczędności")
                    display_desc = tsub
                elif ttype == 'liability_repayment':
                    display_cat = _("Spłata Długu")
                    display_desc = tsub
                self.table.setItem(idx, 2, QTableWidgetItem(display_cat))
                self.table.setItem(idx, 3, QTableWidgetItem(display_desc))
                c = "#27ae60" if ttype=="income" else ("#c0392b" if ttype=="expense" else "#2874A6")
                it = QTableWidgetItem(f"{tamt:.2f}"); it.setForeground(QColor(c)); self.table.setItem(idx, 4, it)

            if tdate.startswith(m_str):
                if ttype=="income": stats_inc+=tamt; inc_map[tcat]=inc_map.get(tcat,0)+tamt
                elif ttype=="expense": stats_exp+=tamt; exp_map[tcat]=exp_map.get(tcat,0)+tamt
                elif ttype=="savings" and tsub==CASH_SAVINGS_NAME: stats_sav+=tamt
                elif ttype=="liability_repayment": stats_lia+=tamt

        prev = self.db.get_net_balance_pln_before_date(f"{m_str}-01")
        real_balance = prev + stats_inc - stats_exp - sum(r[5] for r in rows if r[1].startswith(m_str) and r[2]=='savings') - stats_lia
        display_balance = real_balance - reserved_for_week

        self.lbl_balance.setText(_("SALDO: {:.2f} PLN").format(display_balance))

        if weekly_system_on and weekly_view_active and reserved_for_week > 0:
             self.lbl_balance.setToolTip(_("Realne saldo: {:.2f} PLN\nZarezerwowane na OBECNY tydzień: {:.2f} PLN").format(real_balance, reserved_for_week))
        else:
             self.lbl_balance.setToolTip("")

        self.lbl_prev_balance.setText(_("z poprzedniego miesiąca: {:.2f} PLN").format(prev))
        self.lbl_expenses_month.setText(_("Wydatki (ten msc): {:.2f} PLN").format(stats_exp))
        self.lbl_savings_month.setText(_("Oszczędności Gotówka (ten msc): {:.2f} PLN").format(stats_sav))
        self.lbl_income_breakdown.setText("\n".join([f"{k}: {v:.2f} PLN" for k,v in inc_map.items()]) if inc_map else _("Brak przychodów"))
        self.lbl_savings_total.setText(_("ŁĄCZNIE (GOTÓWKA): {:.2f} PLN").format(self.db.get_total_savings_cash_pln()))

        if not weekly_view_active and refresh_panel:
            self.chart.update_chart_pie_app(
                exp_map, stats_sav, stats_lia,
                _("Wydatki {} {}").format(MONTH_NAME[self.sel_month.currentIndex()], self.sel_year.value()),
                self.palette().color(QPalette.WindowText).name(),
                highlight_cat=self.active_filter_cat
            )

        self.update_goals_display(); self.update_liabilities_display()

    def on_chart_pick(self, event):
        if event.mouseevent.button != 1: return
        try:
            artist = event.artist
            category = artist.get_gid()
        except: category = None
        if category:
            self._pending_category_click = category
            self._debounce_timer.start(250)

    def _process_delayed_click_logic(self):
        category = self._pending_category_click
        if not category: return
        if self.active_filter_cat == category: self.active_filter_cat = None
        else: self.active_filter_cat = category
        self._execute_safe_chart_update()

    def _execute_safe_chart_update(self):
        if not self.isVisible(): return
        try: self.load_transactions(refresh_panel=True)
        except Exception as e: print(f"Błąd update: {e}")

    def delete_selected_transaction(self):
        if self.db.is_month_locked(self.get_current_month_str()): return
        sel = self.table.selectionModel().selectedRows()
        if not sel: return
        msg = _("Czy na pewno chcesz usunąć {} wpisów?").format(len(sel)) if len(sel) > 1 else _("Czy na pewno chcesz usunąć ten wpis?")
        if QMessageBox.Yes == QMessageBox.question(self, _("Usuń"), msg):
            for idx in sorted(sel, reverse=True):
                self.db.delete_transaction(int(self.table.item(idx.row(), 0).text()))
            self.schedule_update()

    def open_income_dialog(self):
        from dialogs import IncomeDialog
        d=IncomeDialog(self, self.db); self.save_transaction(d.get_data()) if d.exec() else None

    def open_expense_dialog(self):
        from dialogs import AddExpenseDialog
        d=AddExpenseDialog(self, self.db); self.save_transaction(d.get_data()) if d.exec() else None

    def open_savings_dialog(self):
        from dialogs import AddSavingsDialog
        d=AddSavingsDialog(self, self.db); self.save_transaction(d.get_data()) if d.exec() else None

    def open_liabilities_dialog(self):
        from dialogs import LiabilitiesDialog
        d=LiabilitiesDialog(self, self.db)
        if d.exec():
            dat=d.get_data()
            if dat['mode']=='new':
                if self.db.add_liability(dat['name'],dat['amount'],dat['deadline']): QMessageBox.information(self,"OK",_("Dodano zobowiązanie."))
                else: QMessageBox.warning(self,_("Błąd"),_("Taka nazwa już istnieje."))
            else: self.db.add_transaction(dat['date'], 'liability_repayment', _('Spłata Długu'), dat['name'], dat['amount'])
            self.schedule_update()

    def open_transfer_dialog(self):
        from dialogs import TransferDialog
        d=TransferDialog(self, self.db)
        if d.exec():
            try:
                s,t,a = d.get_data()
                dt = QDate.currentDate().toString("yyyy-MM-dd")
                self.db.add_transaction(dt, "savings", _("Oszczędności"), s, -a)
                self.db.add_transaction(dt, "savings", _("Oszczędności"), t, a)
                self.schedule_update(); QMessageBox.information(self, _("Transfer"), _("Przesunięto {:.2f} PLN z '{}' do '{}'.").format(a, s, t))
            except ValueError as e: QMessageBox.warning(self, _("Błąd"), str(e))

    def open_new_goal_dialog(self):
        from dialogs import AddGoalDialog
        d=AddGoalDialog(self, self.db)
        if d.exec():
            try:
                n,t = d.get_data()
                if self.db.add_goal(n,t): self.schedule_update()
                else: QMessageBox.warning(self,_("Błąd"),_("Taki cel już istnieje!"))
            except ValueError as e: QMessageBox.warning(self,_("Błąd"),str(e))

    def open_edit_dialog(self):
        from dialogs import EditDialog
        if self.db.is_month_locked(self.get_current_month_str()): return
        r = self.table.currentRow()
        if r<0 or len(self.table.selectionModel().selectedRows()) > 1: return
        tid = int(self.table.item(r,0).text())
        d = self.db.get_transaction_by_id(tid)
        dlg = EditDialog(self, d, self.db)
        if dlg.exec(): self.db.update_transaction(tid, *dlg.get_data()); self.schedule_update()

    def save_transaction(self, data):
        if self.db.is_month_locked(data['date'][:7]):
            QMessageBox.critical(self, _("Błąd"), _("Miesiąc zamknięty!"))
            return
        if data['type']=='income':
            self.db.add_person(data['cat'])

        # Przekazujemy parametr 'exclude' z okienka (0 lub 1)
        self.db.add_transaction(
            data['date'],
            data['type'],
            data['cat'],
            data['sub'],
            data['amount'],
            data.get('exclude', 0) # To jest kluczowe!
        )
        self.schedule_update()

    def open_filter_dialog(self):
        from dialogs import FilterDialog
        cats = set(self.db.get_categories())
        cats.update(self.db.get_people())
        cats.add(_("Oszczędności"))
        cats.update(self.db.get_liabilities_list())
        cats.update(self.db.get_all_historical_liabilities())

        d = FilterDialog(self, list(cats), self.active_filter_cat)

        if d.exec():
            self.active_filter_cat = d.selected_category
            # POPRAWKA NA SEGMENTATION FAULT:
            # Używamy QTimer.singleShot(10, ...), aby opóźnić odświeżenie o 10 milisekund.
            # To pozwala oknu dialogowemu bezpiecznie się zamknąć i zwolnić pamięć C++,
            # zanim Python zacznie przebudowywać tabelę i wykresy.
            QTimer.singleShot(20, self.load_transactions)

    def open_report_dialog(self):
        from reports import PDFReportGenerator
        from dialogs import ReportSelectionDialog

        if not self.pdf_gen: self.pdf_gen = PDFReportGenerator()
        d = ReportSelectionDialog(self)
        if d.exec():
            last_dir = self.settings.value("last_report_dir", os.path.expanduser("~"))
            fn = f"budzet_{d.selected_month_str.replace('-','_')}.pdf" if d.selected_type=="month" else f"bilans_{d.selected_year_str}.pdf"
            path, _ext = QFileDialog.getSaveFileName(self, _("Zapisz"), os.path.join(last_dir, fn), "PDF (*.pdf)")
            if path:
                self.settings.setValue("last_report_dir", os.path.dirname(path))
                self.gen_rep(path, d.selected_month_str if d.selected_type=="month" else d.selected_year_str, d.selected_month_name, d.selected_type=="year")

    def gen_rep(self, path, d_str, m_name, ann):
        tr = self.db.get_year_transactions(d_str) if ann else [t for t in self.db.get_all_transactions() if t[1].startswith(d_str)]
        t_txt = _("Raport Roczny {}").format(d_str) if ann else _("Raport Miesięczny: {} {}").format(m_name, d_str.split('-')[0])
        chart_title = _("Wydatki {}").format(d_str) if ann else _("Wydatki {} {}").format(m_name, d_str.split('-')[0])
        exp, sav, lia, inc = {}, 0, 0, 0
        for r in tr:
            v=r[5]
            if r[2]=='income': inc+=v
            elif r[2]=='expense': exp[r[3]]=exp.get(r[3],0)+v
            elif r[2]=='savings' and r[4]==CASH_SAVINGS_NAME: sav+=v
            elif r[2]=='liability_repayment': lia+=v
        ch = BudgetChart(width=6, height=5)
        ch.update_chart_bar_pdf(exp, sav, lia, inc, chart_title, '#000000')
        self.pdf_gen.generate(path, t_txt, tr, ch.get_image_bytes(), self.db.get_liabilities_status())
        QMessageBox.information(self, _("Sukces"), _("Zapisano: {}").format(path))

    def update_goals_display(self):
        for i in reversed(range(self.goals_list_layout.count())):
            self.goals_list_layout.itemAt(i).widget().setParent(None)
        goals_data = self.db.get_goals_progress_simple()
        if not goals_data:
            lbl = QLabel(_("Brak celów. Dodaj pierwszy (+)"))
            lbl.setStyleSheet("font-style: italic; color: grey; font-size: 10px;")
            self.goals_list_layout.addWidget(lbl)
            return
        for g in goals_data:
            g_id, name, target, current = g['id'], g['name'], g['target'], g['collected']
            item_widget = QWidget(); item_layout = QHBoxLayout(item_widget); item_layout.setContentsMargins(0, 2, 0, 5); item_layout.setSpacing(5)
            info_layout = QVBoxLayout(); info_layout.setSpacing(2)
            lbl = QLabel(_("{}: {:.2f} / {:.0f} PLN").format(name, current, target))
            lbl.setStyleSheet("font-size: 11px; font-weight: bold;")
            pbar = QProgressBar(); pbar.setFixedHeight(12)
            if target > 0: percent = int((current / target) * 100)
            else: percent = 0
            if percent > 100: percent = 100
            pbar.setValue(percent)
            color = "#2ecc71" if percent >= 100 else "#3498db"
            pbar.setStyleSheet(f"QProgressBar {{ border: 1px solid #bbb; border-radius: 4px; background-color: #f0f0f0; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}")
            pbar.setTextVisible(False)
            info_layout.addWidget(lbl); info_layout.addWidget(pbar)
            btn_del = QPushButton("-"); btn_del.setFixedSize(20, 20)
            btn_del.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; font-weight: bold; border-radius: 10px; padding-bottom: 2px; border:none; } QPushButton:hover { background-color: #c0392b; }")
            btn_del.clicked.connect(lambda checked, gid=g_id, gname=name: self.delete_goal_handler(gid, gname))
            item_layout.addLayout(info_layout, stretch=1); item_layout.addWidget(btn_del)
            self.goals_list_layout.addWidget(item_widget)

    def delete_goal_handler(self, goal_id, goal_name):
        msg = QMessageBox(); msg.setWindowTitle(_("Usuń cel")); msg.setText(_("Czy na pewno chcesz usunąć cel: {}?").format(goal_name))
        msg.setInformativeText(_("Historia wpłat pozostanie w systemie, ale cel zniknie z listy."))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if msg.exec() == QMessageBox.Yes: self.db.delete_goal(goal_id); self.schedule_update()

    def update_liabilities_display(self):
        for i in reversed(range(self.liabilities_layout.count())): self.liabilities_layout.itemAt(i).widget().setParent(None)
        debts = self.db.get_liabilities_status()
        if not debts: self.lia_box.hide(); return
        self.lia_box.show()
        today = datetime.now().date()
        for d in debts:
            rem = d['total'] - d['paid']
            if rem <= 0: continue
            w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(0, 0, 0, 8); v.setSpacing(2)
            try:
                deadline_dt = datetime.strptime(d['deadline'], "%Y-%m-%d").date()
                delta = (deadline_dt - today).days
                if delta < 0:
                    status_text = _("PRZETERMINOWANE: {} dni").format(abs(delta)); col = "#e74c3c"; is_overdue=True
                else:
                    weeks = delta // 7; days = delta % 7
                    status_text = _("Pozostało: {} tyg. i {} dni").format(weeks, days) if weeks > 0 else _("Pozostało: {} dni").format(days)
                    col = "#7f8c8d"; is_overdue=False
            except: status_text = _("Błąd daty"); col = "gray"; is_overdue=False
            h_top = QHBoxLayout(); info_lbl = QLabel(_("{}: Zostało {:.2f} PLN").format(d['name'], rem)); info_lbl.setStyleSheet("font-size: 11px;")
            btn_del = QPushButton("x"); btn_del.setFixedSize(16, 16); btn_del.setStyleSheet("border: none; color: gray; font-weight: bold;")
            btn_del.clicked.connect(lambda ch, lid=d['id']: self.delete_liability(lid))
            h_top.addWidget(info_lbl); h_top.addStretch(); h_top.addWidget(btn_del)
            pbar = QProgressBar(); pbar.setFixedHeight(10); percent = int((d['paid'] / d['total']) * 100) if d['total'] > 0 else 0; pbar.setValue(percent)
            chunk_color = "#e57373" if is_overdue else "#3498db"
            pbar.setStyleSheet(f"QProgressBar {{ border: 1px solid #ccc; border-radius: 4px; background-color: #f0f0f0; }} QProgressBar::chunk {{ background-color: {chunk_color}; border-radius: 3px; }}"); pbar.setTextVisible(False)
            status_lbl = QLabel(status_text); status_lbl.setStyleSheet(f"font-size: 10px; color: {col}; font-style: italic;")
            v.addLayout(h_top); v.addWidget(pbar); v.addWidget(status_lbl); self.liabilities_layout.addWidget(w)

    def delete_liability(self, lid):
        if QMessageBox.Yes == QMessageBox.question(self, _("Usuń"), _("Usunąć ten dług z listy? (Historia wpłat zostanie)")):
            self.db.delete_liability(lid); self.schedule_update()

    def closeEvent(self, e):
        import time
        from dialogs import ProcessingDialog

        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("last_year", self.sel_year.value())
        self.settings.setValue("last_month", self.sel_month.currentIndex())
        cfg = self.db.get_config("backup_config")
        if cfg and cfg.get("auto_backup"):
            pd=ProcessingDialog(self,_("Zamykanie"),_("Backup...")); pd.show(); QApplication.processEvents(); time.sleep(0.5); self.db.perform_backup(); pd.close()
        e.accept()

if __name__ == "__main__":
    # Konfiguracja obsługi błędów
    setup_crash_handlers()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # --- KULOODPORNE TŁUMACZENIE SYSTEMOWE (BEZ PLIKÓW .QM) ---
    class HardcodedSystemTranslator(QTranslator):
        def __init__(self):
            super().__init__()
            # Słownik tłumaczeń standardowych przycisków Qt
            # Klucze to angielskie oryginały (często z ampersandem & dla skrótów)
            self.translations = {
                "&Yes": "Tak",
                "Yes": "Tak",
                "&No": "Nie",
                "No": "Nie",
                "&Cancel": "Anuluj",
                "Cancel": "Anuluj",
                "&OK": "OK",
                "OK": "OK",
                "&Save": "Zapisz",
                "Save": "Zapisz",
                "&Open": "Otwórz",
                "Open": "Otwórz",
                "&Close": "Zamknij",
                "Close": "Zamknij",
                "Apply": "Zastosuj",
                "Reset": "Resetuj",
                "&Discard": "Porzuć",
                "Discard": "Porzuć",
                "Help": "Pomoc",
                "&Help": "Pomoc",
                "Show Details...": "Pokaż szczegóły...",
                "Hide Details...": "Ukryj szczegóły...",
                # Nagłówki kalendarza (jeśli używasz QDateEdit w popupie)
                "AM": "AM",
                "PM": "PM",
                # --- DIALOGI PLIKÓW (QFileDialog) ---
                "Look in:": "Szukaj w:",
                "File name:": "Nazwa pliku:",
                "Files of type:": "Pliki typu:",
                "All Files (*)": "Wszystkie pliki (*)",
                "Back": "Wstecz",
                "Parent Directory": "Katalog nadrzędny",
                "Create New Folder": "Utwórz nowy folder",
                "List View": "Lista",
                "Detail View": "Szczegóły",

                # --- KOMUNIKATY O NADPISYWANIU I BŁĘDACH ---
                # %1 to zmienna (nazwa pliku), którą Qt samo podstawi
                "%1 already exists.\nDo you want to replace it?": "%1 już istnieje.\nCzy chcesz go nadpisać?",
                "The file %1 already exists.\nDo you want to replace it?": "Plik %1 już istnieje.\nCzy chcesz go nadpisać?",
                "%1\nFile not found.\nPlease verify the correct file name was given.": "%1\nNie znaleziono pliku.\nSprawdź, czy podana nazwa jest poprawna.",
                "Could not delete directory.": "Nie można usunąć katalogu.",
                "New Folder": "Nowy folder",
                "Directory:": "Katalog:"
            }

        def translate(self, context, source_text, disambiguation=None, n=-1):
            # Sprawdzamy, czy tekst jest w naszym słowniku
            if source_text in self.translations:
                return self.translations[source_text]

            # Fallback: Jeśli nie znamy tłumaczenia, zwracamy pusty string,
            # co każe Qt użyć tekstu oryginalnego (angielskiego)
            return ""

    # Sprawdzanie języka systemu
    # Jeśli system jest Polski -> Instalujemy naszego "ręcznego" tłumacza
    if QLocale.system().language() == QLocale.Language.Polish:
        manual_translator = HardcodedSystemTranslator()
        app.installTranslator(manual_translator)
        # Przechowujemy referencję, żeby Python nie usunął obiektu (Garbage Collector)
        app._manual_translator_ref = manual_translator

    # --- KONIEC TŁUMACZENIA ---

    # Obsługa tłumaczeń własnych (i18n z gettext - to co masz w config.py działa osobno)
    # config.py robi swoje, a powyższy kod załatwia tylko przyciski Qt.

    w = BudgetApp()
    w.show()
    sys.exit(app.exec())
