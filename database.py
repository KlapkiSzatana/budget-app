import sqlite3
import os
import json
from datetime import datetime, timedelta
from config import APP_DIR, CASH_SAVINGS_NAME

class DatabaseManager:
    def __init__(self, db_name="budzet.db"):
        # Używamy ścieżki zdefiniowanej w config.py
        self.db_path = os.path.join(APP_DIR, db_name)
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()
        self.initialize_config()

    def create_tables(self):
        # Tabela transakcji z obsługą kolumny exclude_from_weekly
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, type TEXT, category TEXT, subcategory TEXT,
            amount REAL, currency TEXT, exchange_rate REAL,
            exclude_from_weekly INTEGER DEFAULT 0
        )""")

        self.conn.execute("CREATE TABLE IF NOT EXISTS people (name TEXT PRIMARY KEY)")

        # TE NAZWY MUSZĄ ZOSTAĆ PO POLSKU (Kompatybilność bazy z poprzednimi wersjami)
        self.conn.execute("INSERT OR IGNORE INTO people VALUES ('Mąż')")
        self.conn.execute("INSERT OR IGNORE INTO people VALUES ('Żona')")

        self.conn.execute("CREATE TABLE IF NOT EXISTS month_locks (month_str TEXT PRIMARY KEY)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS categories (name TEXT PRIMARY KEY)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, target_amount REAL)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS liabilities (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, total_amount REAL, deadline TEXT)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS app_config (key TEXT PRIMARY KEY, value TEXT)")

        # Zakupy
        self.conn.execute("CREATE TABLE IF NOT EXISTS shopping_lists (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, created_at TEXT, status TEXT DEFAULT 'open')")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS shopping_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER,
                product_name TEXT,
                quantity TEXT,
                store TEXT DEFAULT '',
                is_checked INTEGER DEFAULT 0,
                FOREIGN KEY(list_id) REFERENCES shopping_lists(id) ON DELETE CASCADE
            )
        """)

        # --- MIGRACJE ---
        try:
            self.conn.execute("ALTER TABLE shopping_items ADD COLUMN store TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

        try:
            self.conn.execute("ALTER TABLE transactions ADD COLUMN exclude_from_weekly INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass # Kolumna już istnieje

        # --- TABELA SKLEPÓW ---
        self.conn.execute("CREATE TABLE IF NOT EXISTS shops (name TEXT PRIMARY KEY)")

        cursor = self.conn.execute("SELECT count(*) FROM shops")
        if cursor.fetchone()[0] == 0:
            default_shops = ["Biedronka", "Dino", "Lidl", "Polo", "Kaufland", "Apteka", "Rossmann", "Pepco"]
            for s in default_shops:
                self.conn.execute("INSERT OR IGNORE INTO shops VALUES (?)", (s,))

        cursor = self.conn.execute("SELECT count(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            defaults = [
                "Zakupy", "Remonty", "Spłata długów", "Samochód",
                "Ciuchy", "Opłaty", "Rozrywka", "Inne", "Zdrowie"
            ]
            for d in defaults:
                self.conn.execute("INSERT INTO categories VALUES (?)", (d,))

        # --- HISTORIA TYGODNIOWA ---
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS weekly_history (
                monday_date TEXT PRIMARY KEY,
                amount REAL,
                categories TEXT
            )
        """)
        self.conn.commit()

    # --- METODY KONFIGURACJI ---
    def initialize_config(self):
        if not self.get_config("backup_config"):
            self.save_config("backup_config", {"auto_backup": False, "backup_path": os.path.join(APP_DIR, "backups")})
        if not self.get_config("weekly_limit_config"):
            # Przy inicjalizacji zaznaczamy wszystkie obecne kategorie jako wliczane
            self.save_config("weekly_limit_config", {"enabled": False, "amount": 500.0, "categories": self.get_categories()})

    def get_config(self, key):
        cursor = self.conn.execute("SELECT value FROM app_config WHERE key=?", (key,))
        res = cursor.fetchone()
        if res:
            try: return json.loads(res[0])
            except: return res[0]
        return None

    def save_config(self, key, value):
        json_val = json.dumps(value)
        self.conn.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)", (key, json_val))
        self.conn.commit()

    def get_weekly_config(self):
        cfg = self.get_config("weekly_limit_config")
        if not cfg:
            return False, 0.0, None
        return cfg.get("enabled", False), cfg.get("amount", 0.0), cfg.get("categories", None)

    # --- METODY BACKUPU ---
    def perform_backup(self):
        import shutil
        from config import _
        cfg = self.get_config("backup_config")
        if not cfg: return False, _("Błąd konfiguracji")
        target_dir = cfg.get("backup_path", "")
        if not target_dir: return False, _("Brak ścieżki backupu")
        if not os.path.exists(target_dir):
            try: os.makedirs(target_dir)
            except OSError: return False, _("Nie można utworzyć folderu")
        filename = f"{datetime.now().strftime('%Y-%m-%d')}.bak"
        target_path = os.path.join(target_dir, filename)
        try:
            shutil.copy2(self.db_path, target_path)
            self._cleanup_backups(target_dir)
            return True, target_path
        except Exception as e: return False, str(e)

    def _cleanup_backups(self, folder):
        import glob
        try:
            files = glob.glob(os.path.join(folder, "*.bak"))
            files.sort(key=os.path.getmtime)
            while len(files) > 10:
                oldest = files.pop(0)
                os.remove(oldest)
        except: pass

    def restore_database(self, backup_file):
        import shutil
        if not os.path.exists(backup_file): return False
        try:
            self.conn.close()
            shutil.copy2(backup_file, self.db_path)
            self.conn = sqlite3.connect(self.db_path)
            return True
        except Exception:
            self.conn = sqlite3.connect(self.db_path)
            return False

    # --- TRANSAKCJE ---
    def add_transaction(self, date, t_type, category, subcategory, amount, exclude=0):
        # Parametr exclude domyślnie 0 (wliczany), 1 (pomijany w tygodniówce)
        self.conn.execute("""
            INSERT INTO transactions (date, type, category, subcategory, amount, currency, exchange_rate, exclude_from_weekly)
            VALUES (?, ?, ?, ?, ?, 'PLN', 1.0, ?)""",
            (date, t_type, category, subcategory, amount, exclude))
        self.conn.commit()

    def update_transaction(self, t_id, date, category, subcategory, amount):
        try:
            self.conn.execute("UPDATE transactions SET date=?, category=?, subcategory=?, amount=? WHERE id=?", (date, category, subcategory, amount, t_id))
            self.conn.commit()
        except: pass

    def delete_transaction(self, t_id):
        self.conn.execute("DELETE FROM transactions WHERE id=?", (t_id,))
        self.conn.commit()

    def get_all_transactions(self):
        try:
            cursor = self.conn.execute("SELECT id, date, type, category, subcategory, amount FROM transactions ORDER BY date DESC, id DESC")
            return cursor.fetchall()
        except sqlite3.OperationalError: return []

    def get_year_transactions(self, year_str):
        try:
            cursor = self.conn.execute("SELECT id, date, type, category, subcategory, amount FROM transactions WHERE date LIKE ? ORDER BY date", (f"{year_str}%",))
            return cursor.fetchall()
        except: return []

    def get_transaction_by_id(self, t_id):
        cursor = self.conn.execute("SELECT id, date, type, category, subcategory, amount FROM transactions WHERE id=?", (t_id,))
        return cursor.fetchone()

    def get_expenses_in_range(self, start_date, end_date, allowed_categories=None):
        # Sumujemy tylko te wydatki, które NIE są wykluczone (exclude_from_weekly = 0)
        query = """
            SELECT category, SUM(amount)
            FROM transactions
            WHERE type='expense'
            AND exclude_from_weekly = 0
            AND date >= ? AND date <= ?
        """
        params = [start_date, end_date]
        if allowed_categories is not None:
            if not allowed_categories: return []
            placeholders = ','.join('?' for _ in allowed_categories)
            query += f" AND category IN ({placeholders})"
            params.extend(allowed_categories)
        query += " GROUP BY category ORDER BY SUM(amount) DESC"
        return self.conn.execute(query, params).fetchall()

    # --- POMOCNICZE (Ludzie/Kategorie) ---
    def add_person(self, name):
        if name:
            self.conn.execute("INSERT OR IGNORE INTO people VALUES (?)", (name,))
            self.conn.commit()

    def add_category(self, name):
        if name:
            name = name.strip()
            self.conn.execute("INSERT OR IGNORE INTO categories VALUES (?)", (name,))

            # 1. Automatyczne dopisanie do GLOBALNEGO limitu (zaznaczona domyślnie)
            cfg = self.get_config("weekly_limit_config")
            if cfg:
                if "categories" not in cfg or cfg["categories"] is None:
                    cfg["categories"] = []
                if name not in cfg["categories"]:
                    cfg["categories"].append(name)
                    self.save_config("weekly_limit_config", cfg)

            # 2. Automatyczne dopisanie do TRWAJĄCEGO tygodnia (natychmiastowe liczenie)
            today = datetime.now().date()
            monday = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
            found, amt, cats = self.get_weekly_limit_for_week(monday)
            if found:
                if name not in cats:
                    cats.append(name)
                    self.set_weekly_limit_for_week(monday, amt, cats)

            self.conn.commit()

    def delete_category_safe(self, name):
        fallback_cat = "Inne"
        if name == fallback_cat: return False
        try:
            self.conn.execute("INSERT OR IGNORE INTO categories VALUES (?)", (fallback_cat,))
            self.conn.execute("UPDATE transactions SET category=? WHERE category=? AND type='expense'", (fallback_cat, name))
            self.conn.execute("DELETE FROM categories WHERE name=?", (name,))
            self.conn.commit()
            return True
        except: return False

    def get_people(self):
        return [r[0] for r in self.conn.execute("SELECT name FROM people ORDER BY name").fetchall()]

    def get_categories(self):
        return [r[0] for r in self.conn.execute("SELECT name FROM categories ORDER BY name").fetchall()]

    # --- CELE ---
    def add_goal(self, name, target_amount):
        try:
            self.conn.execute("INSERT INTO goals (name, target_amount) VALUES (?, ?)", (name, target_amount))
            self.conn.commit()
            return True
        except: return False

    def delete_goal(self, goal_id):
        self.conn.execute("DELETE FROM goals WHERE id=?", (goal_id,))
        self.conn.commit()

    def get_goals(self):
        return [r[0] for r in self.conn.execute("SELECT name FROM goals ORDER BY name").fetchall()]

    def get_goals_progress_simple(self):
        goals_data = []
        for g_id, g_name, g_target in self.conn.execute("SELECT id, name, target_amount FROM goals").fetchall():
            res = self.conn.execute("SELECT SUM(amount) FROM transactions WHERE type='savings' AND subcategory=?", (g_name,)).fetchone()[0]
            current_sum = res if res else 0.0
            goals_data.append({'id': g_id, 'name': g_name, 'target': g_target, 'collected': current_sum})
        return goals_data

    # --- DŁUGI ---
    def add_liability(self, name, amount, deadline):
        try:
            self.conn.execute("INSERT INTO liabilities (name, total_amount, deadline) VALUES (?, ?, ?)", (name, amount, deadline))
            self.conn.commit()
            return True
        except: return False

    def delete_liability(self, lid):
        self.conn.execute("DELETE FROM liabilities WHERE id=?", (lid,))
        self.conn.commit()

    def get_liabilities_list(self):
        return [r[0] for r in self.conn.execute("SELECT name FROM liabilities ORDER BY name").fetchall()]

    def get_liabilities_status(self):
        liabilities = []
        for lid, name, total, deadline in self.conn.execute("SELECT id, name, total_amount, deadline FROM liabilities").fetchall():
            res = self.conn.execute("SELECT SUM(amount) FROM transactions WHERE type='liability_repayment' AND subcategory=?", (name,)).fetchone()[0]
            paid = res if res else 0.0
            liabilities.append({'id': lid, 'name': name, 'total': total, 'paid': paid, 'deadline': deadline})
        return liabilities

    def get_all_historical_liabilities(self):
        return [r[0] for r in self.conn.execute("SELECT DISTINCT subcategory FROM transactions WHERE type='liability_repayment' ORDER BY subcategory").fetchall()]

    # --- STATYSTYKI I BLOKADY ---
    def is_month_locked(self, month_str):
        return self.conn.execute("SELECT 1 FROM month_locks WHERE month_str=?", (month_str,)).fetchone() is not None

    def lock_month(self, month_str):
        self.conn.execute("INSERT OR IGNORE INTO month_locks VALUES (?)", (month_str,))
        self.conn.commit()

    def unlock_month(self, month_str):
        self.conn.execute("DELETE FROM month_locks WHERE month_str=?", (month_str,))
        self.conn.commit()

    def get_total_savings_cash_pln(self):
        from config import CASH_SAVINGS_NAME
        res = self.conn.execute("SELECT SUM(amount) FROM transactions WHERE type='savings' AND subcategory=?", (CASH_SAVINGS_NAME,)).fetchone()[0]
        return res if res else 0.0

    def get_net_balance_pln_before_date(self, date_limit_str):
        balance = 0.0
        for t_type, amt in self.conn.execute("SELECT type, amount FROM transactions WHERE date < ?", (date_limit_str,)).fetchall():
            if t_type == 'income': balance += amt
            elif t_type in ['expense', 'savings', 'liability_repayment']: balance -= amt
        return balance

    # --- ZAKUPY ---
    def create_shopping_list(self, name):
        created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.conn.execute("INSERT INTO shopping_lists (name, created_at, status) VALUES (?, ?, 'open')", (name, created))
        self.conn.commit()
        return cur.lastrowid

    def get_shopping_lists(self):
        return self.conn.execute("SELECT id, name, created_at, status FROM shopping_lists ORDER BY created_at DESC").fetchall()

    def add_shopping_item(self, list_id, product, quantity, store=""):
        self.conn.execute("INSERT INTO shopping_items (list_id, product_name, quantity, store) VALUES (?, ?, ?, ?)", (list_id, product, quantity, store))
        self.conn.commit()

    def get_shopping_items(self, list_id):
        return self.conn.execute("SELECT id, product_name, quantity, store FROM shopping_items WHERE list_id=? ORDER BY store ASC, product_name ASC", (list_id,))

    def delete_shopping_item(self, item_id):
        self.conn.execute("DELETE FROM shopping_items WHERE id=?", (item_id,))
        self.conn.commit()

    def update_shopping_item(self, item_id, p, q):
        self.conn.execute("UPDATE shopping_items SET product_name=?, quantity=? WHERE id=?", (p, q, item_id))
        self.conn.commit()

    def close_shopping_list(self, list_id):
        self.conn.execute("UPDATE shopping_lists SET status='closed' WHERE id=?", (list_id,))
        self.conn.commit()

    def delete_shopping_list(self, list_id):
        self.conn.execute("DELETE FROM shopping_items WHERE list_id=?", (list_id,))
        self.conn.execute("DELETE FROM shopping_lists WHERE id=?", (list_id,))
        self.conn.commit()

    # --- SKLEPY ---
    def add_shop(self, name):
        if name and name.strip():
            self.conn.execute("INSERT OR IGNORE INTO shops VALUES (?)", (name.strip(),))
            self.conn.commit()

    def get_shops(self):
        shops = [r[0] for r in self.conn.execute("SELECT name FROM shops ORDER BY name").fetchall()]
        return [""] + shops

    # --- HISTORIA TYGODNIOWA ---
    def set_weekly_limit_for_week(self, monday_date, amount, categories_list):
        cat_json = json.dumps(categories_list)
        self.conn.execute("INSERT OR REPLACE INTO weekly_history (monday_date, amount, categories) VALUES (?, ?, ?)", (monday_date, amount, cat_json))
        self.conn.commit()

    def get_weekly_limit_for_week(self, monday_date):
        cursor = self.conn.execute("SELECT amount, categories FROM weekly_history WHERE monday_date=?", (monday_date,))
        row = cursor.fetchone()
        if row:
            try: cats = json.loads(row[1])
            except: cats = []
            return True, row[0], cats
        return False, 0.0, []

    def is_weekly_system_enabled(self):
        cfg = self.get_config("weekly_limit_config")
        return cfg.get("enabled", False) if cfg else False

    def set_weekly_system_enabled(self, enabled):
        cfg = self.get_config("weekly_limit_config") or {}
        cfg["enabled"] = enabled
        self.save_config("weekly_limit_config", cfg)
