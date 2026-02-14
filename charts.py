import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class BudgetChart(FigureCanvas):
    def __init__(self, parent=None, width=4.0, height=3.0, dpi=100):
        from matplotlib.figure import Figure
        import sys
        import os
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('none')
        self.fig.patch.set_alpha(0.0)
        self.fig.subplots_adjust(left=0.0, right=1.0, top=0.9, bottom=0.0)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet("background: transparent;")

    def update_chart_pie_app(self, expenses_by_category, savings_amount, liability_amount, debtors_amount=0.0, title_text=None, text_color='#000000', highlight_cat=None):
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        from itertools import zip_longest
        from config import _

        if title_text is None: title_text = _("Struktura")
        self.figure.clear()
        ax = self.figure.add_axes([0.0, 0.0, 0.65, 1.0])

        raw_data = []
        for cat, amount in expenses_by_category.items():
            if amount > 0:
                # Domyślnie brak koloru (automat dobierze)
                col = None
                # Wymuszamy kolory dla specjalnych nazw
                if cat == _("Spłata Długu"): col = '#c0392b'  # Kolor dla długów

                raw_data.append({'label': cat, 'value': amount, 'color': col})

        if savings_amount > 0:
            raw_data.append({'label': _("Oszcz."), 'value': savings_amount, 'color': '#2874A6'})

        if liability_amount > 0:
            raw_data.append({'label': _("Moje Długi"), 'value': liability_amount, 'color': '#c0392b'})

        if debtors_amount > 0:
            raw_data.append({'label': _("Dłużnicy"), 'value': debtors_amount, 'color': '#d35400'})

        if not raw_data:
            ax.pie([1], colors=['#e0e0e0'], radius=0.65, startangle=90)
            ax.text(0, 0, _("Brak\ntransakcji"), ha='center', va='center', color=text_color, fontsize=9)
            ax.set_title(title_text, fontsize=9, color=text_color, pad=15)
            self.draw_idle()
            return

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
        base_colors = plt.get_cmap('tab20').colors
        colors = []
        for i, d in enumerate(interleaved_data):
            if d['color']: colors.append(d['color'])
            else: colors.append(base_colors[i % len(base_colors)])

        total = sum(vals)
        legend_labels = []
        for d in interleaved_data:
            pct = (d['value'] / total) * 100
            legend_labels.append(f"{d['label']} ({pct:.1f}%)")

        wedges, texts, autotexts = ax.pie(vals, startangle=90, radius=0.8, colors=colors, autopct='%1.1f%%', pctdistance=0.65, shadow=False)
        for t in autotexts:
            t.set_color('white'); t.set_fontsize(8); t.set_fontweight('bold')

        ax.set_title(title_text, fontsize=10, color=text_color, pad=10, weight='bold', y=0.90)

        has_summary = False
        if highlight_cat:
            selected_amt = 0.0
            if highlight_cat == _("Oszczędności") or highlight_cat == "Oszczędności": selected_amt = savings_amount
            elif highlight_cat == _("Spłata Długu") or highlight_cat == "Spłata Długu": selected_amt = liability_amount
            elif highlight_cat == _("Dłużnicy") or highlight_cat == "Dłużnicy": selected_amt = debtors_amount
            else: selected_amt = expenses_by_category.get(highlight_cat, 0.0)

            if selected_amt > 0:
                has_summary = True
                wedges.append(Rectangle((0,0), 1, 1, fill=False, edgecolor='none', visible=False))
                legend_labels.append(_("Na {}: {:.2f} zł").format(highlight_cat, selected_amt))

        leg = ax.legend(wedges, legend_labels, title=_("Kategorie (kliknij):"), loc="center left", bbox_to_anchor=(0.95, 0.5), frameon=False, alignment='left')
        plt.setp(leg.get_title(), color=text_color, fontsize=9)
        legend_texts = leg.get_texts()

        for text_item, data_item in zip(legend_texts, interleaved_data):
            raw_name = data_item['label']
            real_name = raw_name
            if raw_name == _("Oszcz."): real_name = _("Oszczędności")
            if raw_name == _("Moje Długi"): real_name = _("Spłata Długu")
            if raw_name == _("Dłużnicy"): real_name = _("Dłużnicy")
            text_item.set_gid(real_name)
            text_item.set_picker(True)
            if real_name == highlight_cat:
                text_item.set_color('#3498db'); text_item.set_weight('bold'); text_item.set_fontsize(10)
            else:
                text_item.set_color(text_color); text_item.set_fontsize(9)

        if has_summary:
            summary_item = legend_texts[-1]
            summary_item.set_color(text_color); summary_item.set_weight('bold'); summary_item.set_fontsize(9); summary_item.set_position((-40, 0))

        self.draw_idle()

    def update_chart_bar_pdf(self, expenses_by_category, savings_amount, liability_amount, total_income, title_text=None, text_color='#000000'):
        from config import _
        if title_text is None: title_text = _("Wydatki")
        if not self.fig.axes: ax = self.fig.add_subplot(111)
        else: ax = self.fig.axes[0]; ax.clear()

        self.fig.subplots_adjust(left=0.3, right=0.9, top=0.9, bottom=0.1)
        cats, vals, colors = [], [], []

        if total_income > 0:
            cats.append(_("PRZYCHODY")); vals.append(total_income); colors.append('#27ae60')

        sorted_items = sorted(expenses_by_category.items(), key=lambda x: x[1])
        for cat, amount in sorted_items:
            if amount > 0: cats.append(cat); vals.append(amount); colors.append('#e74c3c')

        if liability_amount > 0:
            cats.append(_("Spłata Długu")); vals.append(liability_amount); colors.append('#8e44ad')

        if savings_amount > 0:
            cats.append(_("Oszcz. Gotówka")); vals.append(savings_amount); colors.append('#2980b9')

        if not vals:
            ax.text(0.5, 0.5, _("Brak danych"), ha='center', va='center', color=text_color)
        else:
            bars = ax.barh(cats, vals, color=colors)
            ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
            ax.set_xlabel(_('Kwota (PLN)'), color=text_color)
            for bar in bars:
                width = bar.get_width()
                label_x_pos = width + (max(vals) * 0.01)
                ax.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{width:.2f}', va='center', color=text_color, fontsize=9)

        ax.set_title(title_text, fontsize=12, color=text_color)
        self.draw()

    def get_image_bytes(self):
        import io
        buf = io.BytesIO()
        self.fig.savefig(buf, format='png', transparent=False, facecolor='white', dpi=300)
        buf.seek(0)
        return buf
