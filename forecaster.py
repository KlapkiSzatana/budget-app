import sqlite3
import random
from datetime import datetime, timedelta

class FinanceForecaster:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_predictions(self):
        today = datetime.now().date()


        start_of_month_str = today.replace(day=1).strftime("%Y-%m-%d")
        end_of_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        end_of_month_str = end_of_month.strftime("%Y-%m-%d")

        days_left = (end_of_month - today).days


        last_month_income = self._get_avg_past_months('income', 1)
        income_this_month = self._get_current_month_total_by_type('income')
        expected_remaining_income = max(0.0, last_month_income - income_this_month)

        total_estimated_income = income_this_month + expected_remaining_income


        expenses_only = self._get_current_month_total_by_type('expense')
        liability_repayments = self._get_current_month_total_by_type('liability_repayment')
        debtor_repayments = self._get_current_month_total_by_type('debtor_repayment')

        expenses_this_month = expenses_only + liability_repayments + debtor_repayments


        last_month_expenses_total = self._get_avg_past_months('expense', 1)
        last_month_paid_bills = self._get_paid_bills_for_past_months(1)
        last_month_lifestyle_only = max(0.0, last_month_expenses_total - last_month_paid_bills)

        daily_avg_lifestyle = last_month_lifestyle_only / 30
        future_lifestyle_spend = daily_avg_lifestyle * days_left


        expenses_3m = self._get_avg_past_months('expense', 3)
        paid_bills_3m = self._get_paid_bills_for_past_months(3)
        lifestyle_3m = max(0.0, expenses_3m - paid_bills_3m)
        daily_avg_3m = lifestyle_3m / 30


        all_pending_bills = self.db.get_pending_bills()
        actual_this_month_bills = [
            b for b in all_pending_bills
            if start_of_month_str <= b[1] <= end_of_month_str
        ]
        total_pending_bills = sum(b[2] for b in actual_this_month_bills)


        projected_end_month = total_estimated_income - expenses_this_month - future_lifestyle_spend - total_pending_bills

        current_balance = self.db.get_total_balance_all_accounts()


        days_to_zero = self._calculate_days_to_zero(current_balance, daily_avg_3m, actual_this_month_bills)


        cat_forecasts = self._get_category_forecasts_data()


        alerts_hard, alerts_tips = self._get_expanded_alerts(
            cat_forecasts, projected_end_month, total_pending_bills,
            current_balance, expected_remaining_income, future_lifestyle_spend
        )

        return {
            "daily_avg": daily_avg_lifestyle,
            "projected_end_month": projected_end_month,
            "health_score": self._calculate_health_score(projected_end_month, last_month_income),
            "category_forecasts": cat_forecasts[:8],
            "days_to_zero": days_to_zero,
            "current_balance": current_balance,
            "total_pending_bills": total_pending_bills,
            "exp_inc": expected_remaining_income,
            "fut_spend": future_lifestyle_spend,
            "ai_alerts_hard": alerts_hard,
            "ai_alerts_tips": alerts_tips
        }

    def _get_avg_past_months(self, t_type='expense', months=1):
        today = datetime.now().date()
        first_day_this_month = today.replace(day=1)

        temp = first_day_this_month
        for _ in range(months):
            temp = (temp - timedelta(days=1)).replace(day=1)
        start_date = temp

        query = f"""
            SELECT SUM(amount)
            FROM transactions
            WHERE type = ?
            AND type NOT IN ('savings', 'savings_migration', 'goal_deposit')
            AND category NOT LIKE '%Migracja%'
            AND amount < 10000
            AND date >= ?
            AND date < ?
        """
        res = self.db.conn.execute(query, (t_type, start_date.strftime("%Y-%m-%d"), first_day_this_month.strftime("%Y-%m-%d"))).fetchone()

        val = res[0] if res[0] is not None else 0.0
        return val / months

    def _get_paid_bills_for_past_months(self, months=1):
        today = datetime.now().date()
        first_day_this_month = today.replace(day=1)

        temp = first_day_this_month
        for _ in range(months):
            temp = (temp - timedelta(days=1)).replace(day=1)
        start_date = temp

        query = """
            SELECT SUM(amount)
            FROM transactions
            WHERE type = 'expense'
            AND category IN ('Opłaty', 'Rachunki', 'Stałe opłaty', 'Media', 'Czynsz')
            AND category NOT LIKE '%Migracja%'
            AND date >= ?
            AND date < ?
        """
        res = self.db.conn.execute(query, (start_date.strftime("%Y-%m-%d"), first_day_this_month.strftime("%Y-%m-%d"))).fetchone()
        val = res[0] if res[0] is not None else 0.0
        return val / months

    def _get_category_averages_past_months(self, months=3):
        today = datetime.now().date()
        first_day_this_month = today.replace(day=1)

        temp = first_day_this_month
        for _ in range(months):
            temp = (temp - timedelta(days=1)).replace(day=1)
        start_date = temp

        query = f"""
            SELECT category, SUM(amount) / {months}
            FROM transactions
            WHERE type = 'expense'
            AND category NOT LIKE '%Migracja%'
            AND category NOT LIKE '%Oszczędności%'
            AND date >= ? AND date < ?
            GROUP BY category
        """
        rows = self.db.conn.execute(query, (start_date.strftime("%Y-%m-%d"), first_day_this_month.strftime("%Y-%m-%d"))).fetchall()
        return {row[0]: row[1] for row in rows}

    def _get_category_spending_current_month(self):
        m_str = datetime.now().strftime("%Y-%m")
        query = "SELECT category, SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ? GROUP BY category"
        rows = self.db.conn.execute(query, (f"{m_str}%",)).fetchall()
        return {row[0]: row[1] for row in rows}

    def _get_category_forecasts_data(self):
        current_spend = self._get_category_spending_current_month()
        past_avgs = self._get_category_averages_past_months(3)

        forecasts = []
        for cat, val in current_spend.items():
            avg = past_avgs.get(cat, 0)
            if avg > 0:
                risk_pct = (val / avg) * 100
                forecasts.append({
                    'name': cat,
                    'current': val,
                    'predicted': avg,
                    'risk': int(risk_pct)
                })
        forecasts.sort(key=lambda x: x['risk'], reverse=True)
        return forecasts

    def _calculate_days_to_zero(self, balance, daily_exp, bills):
        if balance <= 0: return 0
        if daily_exp <= 0 and not bills: return 999
        temp_balance = balance
        today = datetime.now().date()

        for day_idx in range(1, 365):
            temp_balance -= daily_exp
            current_date_sim = today + timedelta(days=day_idx)
            date_str_sim = current_date_sim.strftime("%Y-%m-%d")

            for b in bills:
                if b[1] == date_str_sim:
                    temp_balance -= b[2]

            if temp_balance <= 0:
                return day_idx
        return 999

    def _get_current_month_total_by_type(self, t_type):
        m_str = datetime.now().strftime("%Y-%m")
        cursor = self.db.conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE type=? AND date LIKE ?", (t_type, f"{m_str}%")
        )
        return cursor.fetchone()[0] or 0.0

    def _calculate_health_score(self, projected_bal, avg_income):
        if avg_income <= 0: return 0
        if projected_bal <= 0: return max(5, int(20 + (projected_bal / 100)))
        ratio = projected_bal / avg_income
        if ratio > 0.30: return 98
        if ratio > 0.15: return 85
        return 50

    def _get_expanded_alerts(self, cat_forecasts, projected_bal, bills, balance, exp_inc, fut_spend):
        alerts_hard = []
        now = datetime.now()
        m_str = now.strftime("%Y-%m")


        expenses_only = self.db.conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ?", (f"{m_str}%",)
        ).fetchone()[0] or 0.0

        liability_repayments = self.db.conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE type='liability_repayment' AND date LIKE ?", (f"{m_str}%",)
        ).fetchone()[0] or 0.0

        debtor_repayments = self.db.conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE type='debtor_repayment' AND date LIKE ?", (f"{m_str}%",)
        ).fetchone()[0] or 0.0

        real_expenses_this_month = expenses_only + liability_repayments + debtor_repayments


        alerts_hard.append(
            f"🔍 <b>Analiza:</b> Masz na kontach {balance:.0f} zł. Dotychczasowe wpływy: {self._get_current_month_total_by_type('income'):.0f} zł (spodziewane jeszcze {exp_inc:.0f} zł). "
            f"Wydane w tym miesiącu (wraz ze spłatami długów): <b>{real_expenses_this_month:.0f} zł</b>. "
            f"Do końca miesiąca wydasz jeszcze ok. {fut_spend + bills:.0f} zł (w tym {bills:.0f} zł na rachunki)."
        )


        this_week_since = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        prev_week_since = (now - timedelta(days=14)).strftime("%Y-%m-%d")

        this_week_sum = self.db.conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE type='expense' AND date >= ?", (this_week_since,)
        ).fetchone()[0] or 0.0

        prev_week_sum = self.db.conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE type='expense' AND date >= ? AND date < ?",
            (prev_week_since, this_week_since)
        ).fetchone()[0] or 0.0

        if prev_week_sum > 0:
            diff = ((this_week_sum - prev_week_sum) / prev_week_sum) * 100
            alerts_hard.append(
                f"📊 <b>Statystyka:</b> Wydatki są o <b>{abs(diff):.1f}% {'niższe' if diff < 0 else 'wyższe'}</b> niż w zeszłym tygodniu."
            )


        savings_total = self.db.get_total_savings_cash_pln()
        avg_exp = self._get_avg_past_months('expense', 3)
        if avg_exp > 0:
            months_covered = savings_total / avg_exp
            alerts_hard.append(f"💰 <b>Poduszka:</b> Oszczędności starczą na <b>{months_covered:.1f}</b> msc życia.")



        mix_pool = []
        m_str_this = now.strftime("%Y-%m")
        m_str_last = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

        def query_sum(q, params=()):
            try:
                return self.db.conn.execute(q, params).fetchone()[0] or 0.0
            except Exception:
                return 0.0

        def query_val(q, params=()):
            try:
                res = self.db.conn.execute(q, params).fetchone()
                return res[0] if res else None
            except Exception:
                return None



        avg_groceries_with_sweets = query_val("""
            SELECT AVG(amount) FROM transactions
            WHERE type='expense' AND category LIKE '%Zakupy%'
            AND (details LIKE '%słodycze%' OR details LIKE '%chipsy%' OR details LIKE '%czekolada%' OR details LIKE '%cola%')
        """)
        avg_groceries_clean = query_val("""
            SELECT AVG(amount) FROM transactions
            WHERE type='expense' AND category LIKE '%Zakupy%'
            AND NOT (details LIKE '%słodycze%' OR details LIKE '%chipsy%' OR details LIKE '%czekolada%' OR details LIKE '%cola%')
        """)
        if avg_groceries_with_sweets and avg_groceries_clean and avg_groceries_with_sweets > avg_groceries_clean:
            diff_pct = ((avg_groceries_with_sweets - avg_groceries_clean) / avg_groceries_clean) * 100
            mix_pool.append(
                f"🍩 <b>Nawyk zakupowy:</b> Gdy na Twoim paragonie lądują <b>słodycze lub chipsy</b>, łączny koszt koszyka "
                f"rośnie statystycznie o <b>{diff_pct:.1f}%</b> (średnio {avg_groceries_with_sweets:.0f} zł vs {avg_groceries_clean:.0f} zł). "
                f"Spróbuj ograniczyć słodkie przekąski, a Twój budżet spożywczy odetchnie!"
            )


        avg_orlen_with_extras = query_val("""
            SELECT AVG(amount) FROM transactions
            WHERE type='expense' AND (details LIKE '%Orlen%' OR category LIKE '%Auto%' OR category LIKE '%Samochód%')
            AND (details LIKE '%snus%' OR details LIKE '%snusy%' OR details LIKE '%hotdog%' OR details LIKE '%kawa%' OR details LIKE '%fajki%')
        """)
        avg_orlen_clean = query_val("""
            SELECT AVG(amount) FROM transactions
            WHERE type='expense' AND (details LIKE '%Orlen%' OR category LIKE '%Auto%' OR category LIKE '%Samochód%')
            AND NOT (details LIKE '%snus%' OR details LIKE '%snusy%' OR details LIKE '%hotdog%' OR details LIKE '%kawa%' OR details LIKE '%fajki%')
        """)
        if avg_orlen_with_extras and avg_orlen_clean and avg_orlen_with_extras > avg_orlen_clean:
            diff_money = avg_orlen_with_extras - avg_orlen_clean
            mix_pool.append(
                f"⛽ <b>Nawyk na stacji:</b> Wizyty na stacji benzynowej, podczas których kupujesz <b>snusy, kawę lub hot-dogi</b>, "
                f"kosztują Cię średnio o <b>{diff_money:.2f} zł więcej</b> niż samo tankowanie. Rozważ zakup snusów kartonem przez internet, by uniknąć marży stacyjnej!"
            )


        zabka_sweets_snus = query_sum("""
            SELECT SUM(amount) FROM transactions
            WHERE type='expense' AND (details LIKE '%Zabka%' OR details LIKE '%Żabka%')
            AND (details LIKE '%snus%' OR details LIKE '%snusy%' OR details LIKE '%słodycze%' OR details LIKE '%cola%' OR details LIKE '%chipsy%')
        """)
        if zabka_sweets_snus > 50:
            mix_pool.append(
                f"🏪 <b>Drobne pokusy:</b> W tym miesiącu wydałeś już <b>{zabka_sweets_snus:.2f} zł</b> w Żabce na "
                f"<b>snusy, napoje lub słodycze</b>. Te drobne, codzienne przyjemności najszybciej uciekają z portfela bez śladu."
            )


        orlen_mix_check = query_sum("""
            SELECT SUM(amount) FROM transactions
            WHERE type='expense' AND (details LIKE '%Orlen%' OR category LIKE '%Auto%')
            AND details LIKE '%gaz%' AND (details LIKE '%snus%' OR details LIKE '%snusy%')
        """)
        if orlen_mix_check > 0:
            mix_pool.append(
                f"🚗 <b>Orlen (Gaz + Snusy):</b> Twój opis transakcji zdradza, że łączysz tankowanie <b>Gazu</b> ze sprawunkiem <b>Snusów</b> "
                f"na stacji. Pamiętaj, że stacje paliw zarabiają najwięcej na wysokich marżach produktów sklepowych!"
            )


        since_90_days = (now - timedelta(days=90)).strftime("%Y-%m-%d")
        try:
            popular_descriptions_rows = self.db.conn.execute("""
                SELECT details, COUNT(*) as cnt, SUM(amount) as total
                FROM transactions
                WHERE type='expense'
                AND date > ?
                AND details IS NOT NULL
                AND details != ''
                AND details NOT LIKE '%Migracja%'
                AND details NOT LIKE '%Przelew%'
                GROUP BY details
                ORDER BY cnt DESC
                LIMIT 5
            """, (since_90_days,)).fetchall()
        except Exception:
            popular_descriptions_rows = []

        for details, count, total in popular_descriptions_rows:
            this_month_desc_total = query_sum(
                "SELECT SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ? AND details = ?",
                (f"{m_str_this}%", details)
            )
            if this_month_desc_total > 0:
                mix_pool.append(
                    f"🛒 <b>Analiza sklepowa:</b> Na <b>{details}</b> wydałeś w tym miesiącu już <b>{this_month_desc_total:.2f} zł</b> "
                    f"(łącznie {count} transakcji w ostatnich 90 dniach). Czy te koszty były w pełni zaplanowane?"
                )


        try:
            categories_list = [r[0] for r in self.db.conn.execute("SELECT name FROM categories").fetchall()]
        except Exception:
            categories_list = []

        for cat in categories_list:
            this_m = query_sum(
                "SELECT SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ? AND category = ?",
                (f"{m_str_this}%", cat)
            )
            last_m = query_sum(
                "SELECT SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ? AND category = ?",
                (f"{m_str_last}%", cat)
            )

            if last_m > 50:
                diff_pct = ((this_m - last_m) / last_m) * 100
                if abs(diff_pct) >= 15:
                    trend = "więcej" if diff_pct > 0 else "mniej"
                    mix_pool.append(
                        f"📊 <b>Analiza kategorii:</b> W kategorii <b>{cat}</b> wydałeś o <b>{abs(diff_pct):.1f}% {trend}</b> "
                        f"niż w zeszłym miesiącu ({this_m:.0f} zł vs {last_m:.0f} zł)."
                    )


        weekend_sum = query_sum(
            "SELECT SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ? AND (strftime('%w', date) = '0' OR strftime('%w', date) = '6')",
            (f"{m_str_this}%",)
        )
        if weekend_sum > 0:
            total_month_exp = query_sum("SELECT SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ?", (f"{m_str_this}%",))
            if total_month_exp > 0:
                wk_pct = (weekend_sum / total_month_exp) * 100
                if wk_pct > 40:
                    mix_pool.append(
                        f"🍻 <b>Weekendowy drenaż:</b> Weekendowe transakcje generują aż <b>{wk_pct:.1f}%</b> wszystkich kosztów w tym miesiącu ({weekend_sum:.0f} zł). "
                        f"Zaplanuj maks. budżet na piątkowy wieczór, by uniknąć syndromu pustego portfela."
                    )


        day_of_month = now.day
        local_start_of_month_str = now.replace(day=1).strftime("%Y-%m-%d")
        expenses_until_now_this_m = query_sum(
            "SELECT SUM(amount) FROM transactions WHERE type='expense' AND date >= ? AND date <= ?",
            (local_start_of_month_str, now.strftime("%Y-%m-%d"))
        )
        last_month_start_str = (now.replace(day=1) - timedelta(days=1)).replace(day=1).strftime("%Y-%m-%d")
        last_month_same_day_str = (now.replace(day=1) - timedelta(days=1)).replace(day=day_of_month).strftime("%Y-%m-%d")
        expenses_until_now_last_m = query_sum(
            "SELECT SUM(amount) FROM transactions WHERE type='expense' AND date >= ? AND date <= ?",
            (last_month_start_str, last_month_same_day_str)
        )
        if expenses_until_now_last_m > 0:
            diff = ((expenses_until_now_this_m - expenses_until_now_last_m) / expenses_until_now_last_m) * 100
            trend = "szybciej" if diff > 0 else "wolniej"
            mix_pool.append(
                f"📈 <b>Tempo wydatków:</b> Do {day_of_month} dnia miesiąca wydajesz o <b>{abs(diff):.1f}% {trend}</b> "
                f"niż w zeszłym miesiącu o tej samej porze."
            )


        tips = [
            "🧠 <b>Zasada 24h:</b> Przed zakupem czegoś powyżej 150 zł odczekaj pełną dobę. Emocje opadną i często zrezygnujesz.",
            "🔋 <b>Subskrypcje:</b> Raz na kwartał zrób audyt subskrypcji. Często płacimy za usługi, z których w ogóle nie korzystamy.",
            "🛒 <b>Lista zakupów:</b> Chodzenie do sklepu bez listy kosztuje średnio 20% więcej przez impulsywne zachcianki.",
            "🍽️ <b>Meal Prep:</b> Zaplanowanie posiłków na 3 dni w przód dramatycznie zmniejsza ilość marnowanego jedzenia.",
            "🚲 <b>Zasada 3km:</b> Jeśli cel pokrycia drogi jest bliżej niż 3 km, idź pieszo lub jedź rowerem. To darmowe paliwo i zdrowie.",
            "📉 <b>Małe kroki:</b> Zaokrąglaj każdą wydaną kwotę do pełnych dych i przelewaj końcówki na oszczędnościowe.",
            "🔌 <b>Standby:</b> Urządzenia w trybie czuwania potrafią wygenerować w roku zauważalną kwotę na rachunku za prąd.",
            "📦 <b>Duże paczki:</b> Produkty chemii domowej kupuj w dużych opakowaniach online. Cena za litr/kg bywa o połowę niższa.",
            "📅 <b>Dzień bez wydatków:</b> Ustal jeden dzień w tygodniu, w którym nie wydasz ani jednej złotówki. Buduje to świetną dyscyplinę.",
            "🛍️ <b>Pozorny zysk:</b> Promocja '-30%' to nie oszczędność, jeśli rzecz nie była Ci potrzebna. Wtedy po prostu wydałeś 70% ceny."
        ]

        mix_pool.extend(tips)


        cryptogen = random.SystemRandom()
        alerts_tips = cryptogen.sample(mix_pool, min(1, len(mix_pool)))

        return alerts_hard, alerts_tips

    def get_what_if_advice(self, simulated_amount, selected_category="Inne", lifestyle_change_pct=0):

        advice = []
        now = datetime.now()
        m_str_this = now.strftime("%Y-%m")


        def query_sum(q, params=()):
            try:
                return self.db.conn.execute(q, params).fetchone()[0] or 0.0
            except Exception:
                return 0.0


        last_month_income = self._get_avg_past_months('income', 1)
        income_this_month = self._get_current_month_total_by_type('income')
        expected_remaining_income = max(0.0, last_month_income - income_this_month)
        total_estimated_income = income_this_month + expected_remaining_income

        expenses_only = self._get_current_month_total_by_type('expense')
        liability_repayments = self._get_current_month_total_by_type('liability_repayment')
        debtor_repayments = self._get_current_month_total_by_type('debtor_repayment')
        expenses_this_month = expenses_only + liability_repayments + debtor_repayments


        last_month_expenses_total = self._get_avg_past_months('expense', 1)
        last_month_paid_bills = self._get_paid_bills_for_past_months(1)
        last_month_lifestyle_only = max(0.0, last_month_expenses_total - last_month_paid_bills)

        daily_avg_lifestyle = last_month_lifestyle_only / 30


        end_of_month_date = ((now.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)).date()
        days_left = max(1, (end_of_month_date - now.date()).days)

        normal_future_spend = daily_avg_lifestyle * days_left
        modified_future_spend = normal_future_spend * (1 + (lifestyle_change_pct / 100.0))
        lifestyle_difference = normal_future_spend - modified_future_spend

        safety_threshold = max(1000.0, last_month_income * 0.15)


        if simulated_amount <= 0:
            if lifestyle_change_pct < 0:
                advice.append(
                    f"🎉 <b>Generujesz oszczędności!</b> Zmniejszając codzienne wydatki o <b>{abs(lifestyle_change_pct)}%</b>, "
                    f"do końca miesiąca zachowasz w portfelu dodatkowe <b>{lifestyle_difference:.0f} zł</b>."
                )
                advice.append(
                    f"💡 <b>Rekomendacja:</b> Te zaoszczędzone <b>{lifestyle_difference:.0f} zł</b> możesz bezpiecznie "
                    f"odłożyć, przeznaczyć na nadprogramowe wydatki w kategorii <b>{selected_category}</b> lub nadpłacić długi."
                )
            elif lifestyle_change_pct > 0:
                cost_of_lifestyle = abs(lifestyle_difference)
                advice.append(
                    f"⚠️ <b>Luźniejszy budżet:</b> Podkręcenie codziennych kosztów o <b>{lifestyle_change_pct}%</b> "
                    f"będzie kosztować Twój portfel dodatkowe <b>{cost_of_lifestyle:.0f} zł</b> do końca miesiąca."
                )




                if cost_of_lifestyle < 100:
                    sweets_or_coffee = query_sum("""
                        SELECT SUM(amount) FROM transactions
                        WHERE type='expense' AND date LIKE ?
                        AND (details LIKE '%słodycze%' OR details LIKE '%cola%' OR details LIKE '%kawa%')
                    """, (f"{m_str_this}%",))
                    if sweets_or_coffee > 10:
                        advice.append(
                            f"🍩 <b>Jak to zrównoważyć (Mikro-cięcia):</b> Aby pokryć ten mały wzrost kosztów, "
                            f"wystarczy zrezygnować z kilku słodyczy, coli czy kawy na mieście (wydałeś na nie w tym msc już {sweets_or_coffee:.0f} zł)."
                        )


                elif 100 <= cost_of_lifestyle < 350:
                    convenience_spend = query_sum("""
                        SELECT SUM(amount) FROM transactions
                        WHERE type='expense' AND date LIKE ?
                        AND (details LIKE '%Zabka%' OR details LIKE '%Żabka%' OR details LIKE '%Express%')
                    """, (f"{m_str_this}%",))
                    if convenience_spend > 30:
                        advice.append(
                            f"🏪 <b>Jak to zrównoważyć (Szybkie zakupy):</b> W tym miesiącu w sklepach convenience (Żabka/Express) "
                            f"poszło już {convenience_spend:.0f} zł. Ograniczenie tych szybkich, droższych sprawunków pokryje tę różnicę bezboleśnie."
                        )


                elif 350 <= cost_of_lifestyle < 700:
                    dining_out = query_sum("""
                        SELECT SUM(amount) FROM transactions
                        WHERE type='expense' AND date LIKE ?
                        AND (category LIKE '%Restauracje%' OR category LIKE '%Jedzenie na mieście%' OR details LIKE '%Pyszne%')
                    """, (f"{m_str_this}%",))
                    if dining_out > 100:
                        advice.append(
                            f"🍔 <b>Jak to zrównoważyć (Gastro):</b> Zamawianie jedzenia na dowóz kosztowało Cię już {dining_out:.0f} zł. "
                            f"Zastąpienie zaledwie 3-4 wyjść gotowaniem w domu całkowicie zrównoważy ten luźniejszy budżet."
                        )


                elif 700 <= cost_of_lifestyle < 1000:
                    top_cat_row = self.db.conn.execute(
                        "SELECT category, SUM(amount) as s FROM transactions WHERE type='expense' AND date LIKE ? GROUP BY category ORDER BY s DESC LIMIT 1",
                        (f"{m_str_this}%",)
                    ).fetchone()
                    if top_cat_row:
                        top_cat, top_cat_sum = top_cat_row[0], top_cat_row[1]
                        advice.append(
                            f"📉 <b>Jak to zrównoważyć (Cięcie kategorii):</b> Taki wzrost wymaga kontrataku. Twoja liderująca kategoria to "
                            f"<b>{top_cat}</b> ({top_cat_sum:.0f} zł). Musisz przyciąć ją o 15% do końca miesiąca, by zamknąć tę lukę."
                        )


                else:
                    advice.append(
                        f"🛑 <b>Ostrzeżenie Prognozy (Próg krytyczny):</b> Planujesz zwiększyć codzienne wydatki o ponad <b>1000 zł</b> "
                        f"({cost_of_lifestyle:.0f} zł do końca miesiąca). Próba zrównoważenia tego samym zaciskaniem pasa "
                        f"w innych kategoriach drastycznie obniży Twój komfort życia i po prostu <b>nie dasz tak rady na dłuższą metę</b>."
                    )
                    advice.append(
                        f"💼 <b>Rekomendacja dochodowa:</b> Zamiast szukać ekstremalnych oszczędności na jedzeniu czy paliwie, "
                        f"aby utrzymać taki standard życia bez naruszania oszczędności, <b>musisz pomyśleć o dodatkowym wpływie gotówki</b> "
                        f"(np. nadgodziny, premia, dodatkowe zlecenie freelancera)."
                    )


                    unhealthy_spend = query_sum("""
                        SELECT SUM(amount) FROM transactions
                        WHERE type='expense' AND date LIKE ?
                        AND (details LIKE '%snus%' OR details LIKE '%snusy%' OR details LIKE '%fajki%' OR details LIKE '%papierosy%')
                    """, (f"{m_str_this}%",))
                    if unhealthy_spend > 80:
                        advice.append(
                            f"🚭 <i>* Dodatkowo: Ograniczenie snusów/papierosów (wydane już {unhealthy_spend:.0f} zł) "
                            f"pomoże zbić chociaż część tego deficytu.</i>"
                        )
            else:

                pass
            return advice


        new_projected_end = (total_estimated_income - expenses_this_month) - modified_future_spend - simulated_amount

        if new_projected_end < safety_threshold:
            shortage = safety_threshold - new_projected_end
            msg = (
                f"⚠️ <b>Zagrożenie poduszki:</b> Ten zakup obniży Twoje saldo na koniec miesiąca do <b>{new_projected_end:.0f} zł</b>. "
                f"Aby sfinansować ten zakup i zachować bezpieczny zapas, <b>musisz zabezpieczyć dodatkowy wpływ (np. zlecenie, nadgodziny) w kwocie min. {shortage:.0f} zł</b>."
            )
            if lifestyle_change_pct < 0:
                msg += (
                    f"<br><br><i>* Dobra decyzja! Dzięki temu, że przyciąłeś codzienne koszty suwakiem o {abs(lifestyle_change_pct)}%, "
                    f"kwota dodatkowego wpływu, którą musisz zdobyć, <b>zmniejszyła się aż o {lifestyle_difference:.0f} zł</b>!</i>"
                )
            advice.append(msg)
        else:
            advice.append(
                f"✅ <b>Bezpieczny zakup:</b> Nawet po tym wydatku Twoje prognozowane saldo na koniec miesiąca "
                f"({new_projected_end:.0f} zł) pozostanie powyżej nienaruszalnego zapasu. Masz zielone światło!"
            )




        if simulated_amount < 150:
            sweets_or_coffee = query_sum("""
                SELECT SUM(amount) FROM transactions
                WHERE type='expense' AND date LIKE ?
                AND (details LIKE '%słodycze%' OR details LIKE '%cola%' OR details LIKE '%kawa%' OR details LIKE '%przekąski%')
            """, (f"{m_str_this}%",))
            if sweets_or_coffee > 20:
                advice.append(
                    f"☕ <b>Jak to zrównoważyć (Mikro-cięcia):</b> Ten wydatek jest stosunkowo niewielki. "
                    f"Wystarczy, że zrezygnujesz z kilku słodyczy lub kaw na mieście (wydałeś na nie w tym msc już {sweets_or_coffee:.0f} zł), "
                    f"a ten zakup sfinansuje się sam!"
                )


        elif 150 <= simulated_amount < 1000:
            dining_out = query_sum("""
                SELECT SUM(amount) FROM transactions
                WHERE type='expense' AND date LIKE ?
                AND (category LIKE '%Restauracje%' OR category LIKE '%Jedzenie na mieście%' OR details LIKE '%Pyszne%' OR details LIKE '%Uber%')
            """, (f"{m_str_this}%",))
            if dining_out > 100:
                pct_covered = min(100.0, (dining_out / simulated_amount) * 100)
                advice.append(
                    f"🍔 <b>Jak to zrównoważyć (Gastro):</b> Wyjścia na miasto i dostawy jedzenia kosztowały Cię "
                    f"w tym miesiącu już <b>{dining_out:.0f} zł</b>. Przygotowanie kilku posiłków w domu "
                    f"pozwoli pokryć nawet do <b>{pct_covered:.0f}%</b> ceny tego zakupu."
                )

            sub_spend = query_sum("SELECT SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ? AND (category LIKE '%Subskrypcje%' OR details LIKE '%Netflix%' OR details LIKE '%Spotify%')", (f"{m_str_this}%",))
            if sub_spend > 50:
                advice.append(
                    f"🎬 <b>Jak to zrównoważyć (Subskrypcje):</b> Na rozrywkę i subskrypcje wydajesz obecnie {sub_spend:.0f} zł/msc. "
                    f"Zawieszenie choćby jednej platformy, z której rzadziej korzystasz, da natychmiastowy zwrot części kosztów."
                )


        else:
            top_cat_row = self.db.conn.execute(
                "SELECT category, SUM(amount) as s FROM transactions WHERE type='expense' AND date LIKE ? GROUP BY category ORDER BY s DESC LIMIT 1",
                (f"{m_str_this}%",)
            ).fetchone()
            if top_cat_row:
                top_cat, top_cat_sum = top_cat_row[0], top_cat_row[1]
                potential_saving = top_cat_sum * 0.20
                if potential_saving > 50:
                    pct_covered = min(100.0, (potential_saving / simulated_amount) * 100)
                    advice.append(
                        f"📉 <b>Gdzie uciąć koszty?</b> Twoja najdroższa kategoria to "
                        f"<b>{top_cat}</b> ({top_cat_sum:.0f} zł). Jeśli wprowadzisz tam dyscyplinę i obetniesz koszty o <b>20%</b>, "
                        f"odzyskasz <b>{potential_saving:.0f} zł</b>, co sfinansuje <b>{pct_covered:.0f}%</b> tego zakupu."
                    )

            unhealthy_spend = query_sum("""
                SELECT SUM(amount) FROM transactions
                WHERE type='expense' AND date LIKE ?
                AND (details LIKE '%snus%' OR details LIKE '%snusy%' OR details LIKE '%fajki%' OR details LIKE '%papierosy%')
            """, (f"{m_str_this}%",))
            if unhealthy_spend > 100:
                pct_covered = min(100.0, (unhealthy_spend / simulated_amount) * 100)
                advice.append(
                    f"🚭 <b>Fundusz tytoniowy:</b> Wydatki na snusy i papierosy w tym miesiącu to już <b>{unhealthy_spend:.0f} zł</b>. "
                    f"Ograniczenie ich sfinansuje aż <b>{pct_covered:.0f}%</b> planowanego kosztu!"
                )


            months_needed = int(simulated_amount / (last_month_income * 0.10)) if last_month_income > 0 else 5
            months_needed = max(2, months_needed)
            monthly_saving = simulated_amount / months_needed

            advice.append(
                f"🏛️ <b>Jak to sfinansować (Oszczędzanie celowe):</b> Zakup na kwotę <b>{simulated_amount:.0f} zł</b> "
                f"to duże obciążenie. Rozważ założenie <b>Celu Oszczędnościowego</b> i odkładanie po <b>{monthly_saving:.0f} zł</b> "
                f"przez <b>{months_needed} msc</b>, zamiast drenować całe konto w jednym miesiącu."
            )
            advice.append(
                f"💳 <b>Alternatywa (Raty 0%):</b> Jeśli zakup jest pilny, rozważ wyłącznie "
                f"<b>raty 0%</b> rozbite na min. 6-10 miesięcy. Pozwoli to zbić miesięczne obciążenie budżetu "
                f"do bezpiecznych, nieodczuwalnych ~{simulated_amount/10:.0f} zł/msc."
            )

        return advice

    def _get_spending_days_analysis(self):
        since = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        res = self.db.conn.execute("""
            SELECT strftime('%w', date) as d, AVG(amount)
            FROM transactions WHERE type='expense' AND date > ? GROUP BY d
        """, (since,)).fetchall()
        if not res: return None, None
        processed = [(6 if int(d)==0 else int(d)-1, a) for d, a in res]
        return min(processed, key=lambda x: x[1])[0], max(processed, key=lambda x: x[1])[0]
