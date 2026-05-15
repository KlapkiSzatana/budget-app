import copy
from datetime import datetime

class WhatIfSimulator:
    def __init__(self, forecaster):

        self.forecaster = forecaster
        self.base_predictions = None
        self.scenarios = []
        self.reset_scenarios()

    def load_current_state(self):

        self.base_predictions = self.forecaster.get_predictions()
        return self.base_predictions

    def reset_scenarios(self):

        self.scenarios = {
            "one_off_expenses": [],
            "one_off_income": [],
            "lifestyle_multiplier": 1.0,
            "recurring_changes": []
        }

    def add_one_off_expense(self, name, amount):

        self.scenarios["one_off_expenses"].append({"name": name, "amount": float(amount)})

    def add_one_off_income(self, name, amount):

        self.scenarios["one_off_income"].append({"name": name, "amount": float(amount)})

    def set_lifestyle_multiplier(self, percentage_change):

        self.scenarios["lifestyle_multiplier"] = 1.0 + (float(percentage_change) / 100.0)

    def add_recurring_change(self, name, amount_change):

        self.scenarios["recurring_changes"].append({"name": name, "change": float(amount_change)})

    def run_simulation(self):

        if not self.base_predictions:
            self.load_current_state()


        sim_data = copy.deepcopy(self.base_predictions)


        virtual_expenses = sum(item["amount"] for item in self.scenarios["one_off_expenses"])
        virtual_income = sum(item["amount"] for item in self.scenarios["one_off_income"])


        virtual_recurring_change = sum(item["change"] for item in self.scenarios["recurring_changes"])


        original_fut_spend = sim_data["fut_spend"]
        sim_data["fut_spend"] = original_fut_spend * self.scenarios["lifestyle_multiplier"]
        lifestyle_diff = sim_data["fut_spend"] - original_fut_spend



        old_projected = sim_data["projected_end_month"]
        sim_data["projected_end_month"] = (
            old_projected +
            virtual_income -
            virtual_expenses -
            virtual_recurring_change -
            lifestyle_diff
        )



        sim_data["health_score"] = self.forecaster._calculate_health_score(
            sim_data["projected_end_month"],
            self.forecaster._get_avg_past_months('income', 1)
        )



        virtual_current_balance = sim_data["current_balance"] + virtual_income - virtual_expenses


        virtual_daily_exp = sim_data["daily_avg"] * self.scenarios["lifestyle_multiplier"]


        virtual_bills = copy.deepcopy(self.forecaster.db.get_pending_bills())




        today_str = datetime.now().strftime("%Y-%m-%d")
        for rc in self.scenarios["recurring_changes"]:

            if rc["change"] > 0:
                virtual_bills.append([999, today_str, rc["change"], "Symulacja", rc["name"], 0, None])

            elif rc["change"] < 0:
                abs_change = abs(rc["change"])
                for b in virtual_bills:

                    if abs(b[2] - abs_change) < 5.0 or rc["name"].lower() in b[4].lower():
                        virtual_bills.remove(b)
                        break


        sim_data["days_to_zero"] = self.forecaster._calculate_days_to_zero(
            virtual_current_balance,
            virtual_daily_exp,
            virtual_bills
        )


        sim_data["simulation_summary"] = self._generate_simulation_summary(
            old_projected,
            sim_data["projected_end_month"],
            sim_data["days_to_zero"] - self.base_predictions["days_to_zero"]
        )

        return sim_data

    def _generate_simulation_summary(self, old_bal, new_bal, days_diff):

        diff = new_bal - old_bal
        summary = []

        if diff > 0:
            summary.append(f"🟢 <b>Zysk:</b> Ten scenariusz poprawi Twoje saldo na koniec miesiąca o <b>+{diff:.2f} zł</b>.")
        elif diff < 0:
            summary.append(f"🔴 <b>Koszt:</b> Ten scenariusz obniży Twoje saldo na koniec miesiąca o <b>{diff:.2f} zł</b>.")
        else:
            summary.append("⚪ <b>Bez zmian:</b> Ten scenariusz nie wpływa bezpośrednio na saldo końcowe.")

        if days_diff > 0:
            summary.append(f"🛡️ <b>Bezpieczeństwo:</b> Twój margines przeżycia bez wpływów wydłuży się o <b>+{days_diff} dni</b>.")
        elif days_diff < 0:
            summary.append(f"⚠️ <b>Ryzyko:</b> Osiągniesz stan 0 zł na kontach o <b>{abs(days_diff)} dni szybciej</b> niż normalnie.")

        return " ".join(summary)
