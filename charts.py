import matplotlib
# Ustawienie backendu na QtAgg jest kluczowe dla integracji z PySide6
matplotlib.use('QtAgg')

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class BudgetChart(FigureCanvas):
    def __init__(self, parent=None, width=4.0, height=3.0, dpi=100):
        # Importy niezbędne do inicjalizacji instancji
        from matplotlib.figure import Figure
        import sys
        import os

        # Inicjalizacja figury
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # Ustawienia przezroczystości tła (ważne dla estetyki UI)
        self.fig.patch.set_facecolor('none')
        self.fig.patch.set_alpha(0.0)

        # Marginesy wykresu
        self.fig.subplots_adjust(left=0.0, right=1.0, top=0.9, bottom=0.0)

        super().__init__(self.fig)
        self.setParent(parent)
        # Styl arkusza stylów Qt dla widgetu
        self.setStyleSheet("background: transparent;")

    def update_chart_pie_app(self, expenses_by_category, savings_amount, liability_amount, title_text=None, text_color='#000000', highlight_cat=None):
        """
        Rysuje interaktywny wykres kołowy dla głównego dashboardu aplikacji.
        """
        # Importy lokalne dla tej metody
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        from itertools import zip_longest
        from config import _

        # Domyślna wartość tytułu (obsługa tłumaczenia)
        if title_text is None:
            title_text = _("Struktura")

        # 1. Czyścimy poprzedni wykres
        self.figure.clear()

        # 2. Definiujemy obszar wykresu wewnątrz figury
        ax = self.figure.add_axes([0.0, 0.0, 0.65, 1.0])

        # --- PRZYGOTOWANIE DANYCH ---
        raw_data = []
        for cat, amount in expenses_by_category.items():
            if amount > 0:
                raw_data.append({'label': cat, 'value': amount, 'color': None})

        if savings_amount > 0:
            raw_data.append({'label': _("Oszcz."), 'value': savings_amount, 'color': '#2874A6'})

        if liability_amount > 0:
            raw_data.append({'label': _("Długi"), 'value': liability_amount, 'color': '#8e44ad'})

        # Jeśli brak danych do wyświetlenia
        if not raw_data:
            ax.pie([1], colors=['#e0e0e0'], radius=0.65, startangle=90)
            ax.text(0, 0, _("Brak\ntransakcji"), ha='center', va='center', color=text_color, fontsize=9)
            ax.set_title(title_text, fontsize=9, color=text_color, pad=15)
            self.draw_idle()
            return

        # --- SORTOWANIE I MIESZANIE KOLORÓW ---
        # Sortujemy malejąco, a potem przeplatamy (interleave), żeby kolory były lepiej rozróżnialne
        raw_data.sort(key=lambda x: x['value'], reverse=True)
        interleaved_data = []
        mid = len(raw_data) // 2
        left = raw_data[:mid]
        right = raw_data[mid:]
        right = right[::-1]

        for l, r in zip_longest(left, right):
            if l: interleaved_data.append(l)
            if r: interleaved_data.append(r)

        vals = [d['value'] for d in interleaved_data]

        # Pobranie palety kolorów
        base_colors = plt.get_cmap('tab20').colors
        colors = []
        for i, d in enumerate(interleaved_data):
            if d['color']: colors.append(d['color'])
            else: colors.append(base_colors[i % len(base_colors)])

        total = sum(vals)

        # Etykiety do legendy
        legend_labels = []
        for d in interleaved_data:
            pct = (d['value'] / total) * 100
            legend_labels.append(f"{d['label']} ({pct:.1f}%)")

        # --- RYSOWANIE PIE CHART ---
        wedges, texts, autotexts = ax.pie(
            vals,
            startangle=90,
            radius=0.8,
            colors=colors,
            autopct='%1.1f%%',
            pctdistance=0.65,
            shadow=False
        )

        # Stylizacja procentów na wykresie
        for t in autotexts:
            t.set_color('white')
            t.set_fontsize(8)
            t.set_fontweight('bold')

        ax.set_title(title_text, fontsize=10, color=text_color, pad=10, weight='bold', y=0.90)

        # --- PODSUMOWANIE WYBRANEJ KATEGORII (Dynamiczne) ---
        has_summary = False
        if highlight_cat:
            selected_amt = 0.0

            # Logika mapowania nazw wyświetlanych na wartości
            if highlight_cat == _("Oszczędności") or highlight_cat == "Oszczędności":
                selected_amt = savings_amount
            elif highlight_cat == _("Spłata Długu") or highlight_cat == "Spłata Długu":
                selected_amt = liability_amount
            else:
                selected_amt = expenses_by_category.get(highlight_cat, 0.0)

            if selected_amt > 0:
                has_summary = True
                # Pusty element graficzny dla legendy (trik matplotlib)
                empty_handle = Rectangle((0,0), 1, 1, fill=False, edgecolor='none', visible=False)
                wedges.append(empty_handle)

                summary_text = _("Na {}: {:.2f} zł").format(highlight_cat, selected_amt)
                legend_labels.append(summary_text)

        # --- LEGENDA ---
        leg = ax.legend(
            wedges,
            legend_labels,
            title=_("Kategorie (kliknij):"),
            loc="center left",
            bbox_to_anchor=(0.95, 0.5),
            frameon=False,
            alignment='left'
        )

        plt.setp(leg.get_title(), color=text_color, fontsize=9)

        # --- KONFIGURACJA KLIKANIA (PICKER) ---
        legend_texts = leg.get_texts()

        for text_item, data_item in zip(legend_texts, interleaved_data):
            raw_name = data_item['label']
            real_name = raw_name

            # Mapowanie nazw skróconych na pełne dla logiki filtra
            if raw_name == _("Oszcz."): real_name = _("Oszczędności")
            if raw_name == _("Długi"): real_name = _("Spłata Długu")

            # Ustawiamy ID dla zdarzenia pick_event
            text_item.set_gid(real_name)
            text_item.set_picker(True)

            # Podświetlenie aktywnej kategorii w legendzie
            if real_name == highlight_cat:
                text_item.set_color('#3498db')
                text_item.set_weight('bold')
                text_item.set_fontsize(10)
            else:
                text_item.set_color(text_color)
                text_item.set_fontsize(9)

        # Styl ostatniego elementu (podsumowania), jeśli istnieje
        if has_summary:
            summary_item = legend_texts[-1]
            summary_item.set_color(text_color)
            summary_item.set_weight('bold')
            summary_item.set_fontsize(9)
            # Przesunięcie w lewo dla estetyki
            summary_item.set_position((-40, 0))

        self.draw_idle()

    def update_chart_bar_pdf(self, expenses_by_category, savings_amount, liability_amount, total_income, title_text=None, text_color='#000000'):
        """
        Rysuje wykres słupkowy poziomy (BarH) do wykorzystania w raporcie PDF.
        """
        from config import _

        if title_text is None:
            title_text = _("Wydatki")

        if not self.fig.axes:
            ax = self.fig.add_subplot(111)
        else:
            ax = self.fig.axes[0]
            ax.clear()

        # Ustawienia marginesów pod wydruk PDF
        self.fig.subplots_adjust(left=0.3, right=0.9, top=0.9, bottom=0.1)

        cats, vals, colors = [], [], []

        # Dodajemy Przychody (zielony)
        if total_income > 0:
            cats.append(_("PRZYCHODY"))
            vals.append(total_income)
            colors.append('#27ae60')

        # Dodajemy Wydatki (czerwone) - sortowane
        sorted_items = sorted(expenses_by_category.items(), key=lambda x: x[1])
        for cat, amount in sorted_items:
            if amount > 0:
                cats.append(cat)
                vals.append(amount)
                colors.append('#e74c3c')

        # Dodajemy Spłatę długów (fioletowy)
        if liability_amount > 0:
            cats.append(_("Spłata Długów"))
            vals.append(liability_amount)
            colors.append('#8e44ad')

        # Dodajemy Oszczędności (niebieski)
        if savings_amount > 0:
            cats.append(_("Oszcz. Gotówka"))
            vals.append(savings_amount)
            colors.append('#2980b9')

        if not vals:
            ax.text(0.5, 0.5, _("Brak danych"), ha='center', va='center', color=text_color)
        else:
            bars = ax.barh(cats, vals, color=colors)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_xlabel(_('Kwota (PLN)'), color=text_color)

            # Dodanie wartości liczbowych na końcach słupków
            for bar in bars:
                width = bar.get_width()
                label_x_pos = width + (max(vals) * 0.01)
                ax.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{width:.2f}', va='center', color=text_color, fontsize=9)

        ax.set_title(title_text, fontsize=12, color=text_color)
        self.draw()

    def get_image_bytes(self):
        """
        Zwraca bufor bajtów z obrazem wykresu (PNG), gotowy do wstawienia do PDF.
        """
        import io

        buf = io.BytesIO()
        # Zapisujemy z białym tłem, żeby w PDF wyglądało jak należy (nie przezroczyste)
        self.fig.savefig(buf, format='png', transparent=False, facecolor='white', dpi=300)
        buf.seek(0)
        return buf
