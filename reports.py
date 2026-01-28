import atexit

# --- MECHANIZM SPRZĄTANIA PLIKÓW TYMCZASOWYCH ---
PDF_FILES_TO_CLEAN = []

def cleanup_generated_files():
    """Usuwa tymczasowe pliki PDF wygenerowane podczas sesji."""
    import os
    for file_path in PDF_FILES_TO_CLEAN:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

atexit.register(cleanup_generated_files)

# --- GENERATOR RAPORTÓW FINANSOWYCH ---
class PDFReportGenerator:
    def __init__(self):
        self.font_name = "Helvetica"
        self.fonts_registered = False

    def register_system_font(self):
        """Rejestruje czcionki obsługujące polskie znaki."""
        if self.fonts_registered:
            return

        import os
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # Lista potencjalnych ścieżek do czcionek (Windows/Linux/macOS)
        font_candidates = [
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\tahoma.ttf",
            r"C:\Windows\Fonts\verdana.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/noto/NotoSans-Regular.ttf",
            "/Library/Fonts/Arial.ttf"
        ]

        found_font = None
        for path in font_candidates:
            if os.path.exists(path):
                found_font = path
                break

        if found_font:
            try:
                pdfmetrics.registerFont(TTFont('CustomFont', found_font))
                self.font_name = 'CustomFont'
            except Exception: pass

        self.fonts_registered = True

    def generate(self, filename, title, transactions, chart_img_buffer, liabilities_status=None):
        import io
        self.register_system_font() # Rejestracja dopiero przy generowaniu (szybki start)

        if liabilities_status is None: liabilities_status = []
        dummy = io.BytesIO()

        # Przebieg 1: Obliczenie liczby stron
        total_pages = self._create_pdf(dummy, title, transactions, chart_img_buffer, liabilities_status, count_only=True)
        # Przebieg 2: Generowanie właściwego pliku
        self._create_pdf(filename, title, transactions, chart_img_buffer, liabilities_status, total_pages=total_pages)

    def _create_pdf(self, output, title, transactions, chart_img_buffer, liabilities_status, count_only=False, total_pages=0):
        # Importy lokalne dla wydajności
        from datetime import datetime
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib.utils import ImageReader
        from config import _

        c = canvas.Canvas(output, pagesize=A4)
        width, height = A4
        page_num = 1
        # Nazwa techniczna musi pasować do bazy
        CASH_SAVINGS_NAME = "Oszczędności gotówka"

        incomes = {}
        expenses = {}
        savings_cash = 0.0
        savings_goals = 0.0
        liability_payments = {}

        total_inc = 0.0
        total_exp = 0.0
        total_lia = 0.0

        transactions.sort(key=lambda x: x[1])

        for row in transactions:
            t_type, t_cat, t_sub, t_amt = row[2], row[3], row[4], row[5]
            if t_type == "income":
                incomes[t_cat] = incomes.get(t_cat, 0.0) + t_amt
                total_inc += t_amt
            elif t_type == "expense":
                expenses[t_cat] = expenses.get(t_cat, 0.0) + t_amt
                total_exp += t_amt
            elif t_type == "savings":
                if t_sub == CASH_SAVINGS_NAME: savings_cash += t_amt
                else: savings_goals += t_amt
            elif t_type == "liability_repayment":
                liability_payments[t_sub] = liability_payments.get(t_sub, 0.0) + t_amt
                total_lia += t_amt

        # --- STRONA 1: PODSUMOWANIE ---
        y_pos = height - 2.5 * cm
        c.setFont(self.font_name, 24)
        c.drawString(2 * cm, y_pos, title)
        y_pos -= 0.8 * cm
        c.setFont(self.font_name, 10)
        c.drawString(2 * cm, y_pos, _("Data: {}").format(datetime.now().strftime('%Y-%m-%d %H:%M')))
        y_pos -= 1.5 * cm

        c.setFont(self.font_name, 12)
        c.drawString(2 * cm, y_pos, _("PRZYCHODY:"))
        y_pos -= 0.8 * cm

        data_inc = [[_("Źródło"), _("Kwota (PLN)")]]
        for cat, val in incomes.items():
            data_inc.append([cat, f"{val:.2f}"])
        data_inc.append([_("SUMA"), f"{total_inc:.2f}"])

        t_inc = Table(data_inc, colWidths=[8*cm, 4*cm])
        t_inc.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        w, h = t_inc.wrapOn(c, width, height)
        t_inc.drawOn(c, 2 * cm, y_pos - h)
        y_pos -= (h + 1.0 * cm)

        c.drawString(2 * cm, y_pos, _("WYDATKI:"))
        y_pos -= 0.8 * cm
        data_exp = [[_("Kategoria"), _("Kwota (PLN)")]]
        for cat, val in expenses.items():
            data_exp.append([cat, f"{val:.2f}"])
        data_exp.append([_("SUMA"), f"{total_exp:.2f}"])

        t_exp = Table(data_exp, colWidths=[8*cm, 4*cm])
        t_exp.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('BACKGROUND', (0, 0), (-1, 0), colors.firebrick),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        w, h = t_exp.wrapOn(c, width, height)

        # Sprawdzanie miejsca na stronie
        if y_pos - h < 3.5*cm:
            if not count_only: self.draw_footer(c, width, page_num, total_pages)
            c.showPage()
            page_num += 1
            y_pos = height - 3 * cm
            c.setFont(self.font_name, 12)

        t_exp.drawOn(c, 2 * cm, y_pos - h)
        y_pos -= (h + 1.5 * cm)

        if liability_payments:
            if y_pos < 6*cm:
                if not count_only: self.draw_footer(c, width, page_num, total_pages)
                c.showPage()
                page_num += 1
                y_pos = height - 3*cm
                c.setFont(self.font_name, 12)

            c.drawString(2 * cm, y_pos, _("SPŁATA ZOBOWIĄZAŃ (Miesiąc):"))
            y_pos -= 0.8 * cm

            debt_map = {d['name']: d['total'] - d['paid'] for d in liabilities_status}
            data_lia = [[_("Komu"), _("Wpłacono"), _("Pozostało")]]
            for who, amt in liability_payments.items():
                rem = debt_map.get(who, 0.0)
                data_lia.append([who, f"{amt:.2f}", f"{rem:.2f}"])
            data_lia.append([_("SUMA"), f"{total_lia:.2f}", ""])

            t_lia = Table(data_lia, colWidths=[6*cm, 4*cm, 4*cm])
            t_lia.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.6)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            w, h = t_lia.wrapOn(c, width, height)
            t_lia.drawOn(c, 2*cm, y_pos - h)
            y_pos -= (h + 1.5*cm)

        if y_pos < 5*cm:
            if not count_only: self.draw_footer(c, width, page_num, total_pages)
            c.showPage()
            page_num += 1
            y_pos = height - 3*cm
            c.setFont(self.font_name, 12)

        c.drawString(2 * cm, y_pos, _("Oszczędności (Gotówka): {:.2f} PLN").format(savings_cash))
        y_pos -= 0.6 * cm
        c.drawString(2 * cm, y_pos, _("Wpłaty na Cele: {:.2f} PLN").format(savings_goals))
        y_pos -= 0.6 * cm

        net = total_inc - total_exp - savings_cash - savings_goals - total_lia
        c.setFillColor(colors.black)
        c.setFont(self.font_name, 14)
        c.drawString(2 * cm, y_pos - 0.5*cm, _("Bilans miesiąca: {:.2f} PLN").format(net))

        if not count_only: self.draw_footer(c, width, page_num, total_pages)

        # --- STRONA 2+: SZCZEGÓŁY ---
        c.showPage()
        page_num += 1

        headers = [_("Data"), _("Typ"), _("Kategoria"), _("Opis"), _("Kwota")]
        col_widths = [2.5*cm, 2.5*cm, 4*cm, 6*cm, 2.5*cm]
        y_pos = height - 2.5 * cm
        c.setFont(self.font_name, 14)
        c.setFillColor(colors.black)
        c.drawString(2*cm, y_pos, _("REJESTR SZCZEGÓŁOWY"))
        y_pos -= 1.0 * cm

        style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
        ])

        data = [headers]
        for row in transactions:
            type_map = {
                'income': _('Wpływ'),
                'expense': _('Wydatek'),
                'savings': _('Oszcz.'),
                'liability_repayment': _('Spłata')
            }
            display_type = type_map.get(row[2], row[2])
            data.append([row[1], display_type, row[3], row[4][:35], f"{row[5]:.2f}"])

        # Paginacja tabeli
        ROWS_PER_PAGE = 37
        current_data = [data[0]]
        y_pos_start = height - 2.5 * cm - 1.0 * cm

        for i in range(1, len(data)):
            current_data.append(data[i])
            if len(current_data) - 1 >= ROWS_PER_PAGE:
                t = Table(current_data, colWidths=col_widths)
                t.setStyle(style)
                w, h = t.wrapOn(c, width, height)
                t.drawOn(c, 2*cm, y_pos_start - h)

                if not count_only: self.draw_footer(c, width, page_num, total_pages)
                c.showPage()
                page_num += 1

                current_data = [data[0]]
                y_pos_start = height - 2.0 * cm

        if len(current_data) > 1:
            t = Table(current_data, colWidths=col_widths)
            t.setStyle(style)
            w, h = t.wrapOn(c, width, height)
            t.drawOn(c, 2*cm, y_pos_start - h)
            if not count_only: self.draw_footer(c, width, page_num, total_pages)

        # --- OSTATNIA STRONA: WYKRES ---
        c.showPage()
        page_num += 1
        c.setFont(self.font_name, 16)
        c.drawString(2*cm, height - 3*cm, _("WIZUALIZACJA FINANSÓW"))

        if chart_img_buffer:
            img = ImageReader(chart_img_buffer)
            img_w, img_h = 16 * cm, 12 * cm
            c.drawImage(img, (width - img_w)/2, height - 16*cm, width=img_w, height=img_h, mask='auto')

        if not count_only: self.draw_footer(c, width, page_num, total_pages)
        c.save()
        return page_num

    def draw_footer(self, c, width, page_num, total_pages):
        from datetime import datetime
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from config import _, WERSJA, APPNAME

        c.setFont(self.font_name, 8)
        c.setFillColor(colors.gray)
        c.drawString(2 * cm, 1.5 * cm, _("Data: {}").format(datetime.now().strftime('%Y-%m-%d')))
        c.drawRightString(width - 2 * cm, 1.5 * cm, f" {APPNAME} {WERSJA} ")
        if total_pages > 0:
            c.drawCentredString(width / 2, 1.5 * cm, _("Strona {} z {}").format(page_num, total_pages))
        else:
            c.drawCentredString(width / 2, 1.5 * cm, _("Strona {}").format(page_num))

# --- GENERATOR LISTY ZAKUPÓW ---
class ShoppingPDFGenerator:
    def __init__(self):
        self.font_name = "Helvetica"
        self._register_polish_font()

    def _register_polish_font(self):
        import os
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]

        for path in candidates:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont('CustomFont', path))
                    self.font_name = 'CustomFont'
                    return
                except Exception: continue

    def generate(self, filename, list_name, items):
        """items: lista krotek (produkt, ilosc, sklep)"""
        from collections import defaultdict
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from config import _

        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        LABEL_OTHER = _("POZOSTAŁE")

        grouped_items = defaultdict(list)
        for prod, qty, store in items:
            key = store if store and store.strip() else LABEL_OTHER
            grouped_items[key].append((prod, qty))

        sorted_stores = sorted([k for k in grouped_items.keys() if k != LABEL_OTHER])
        if LABEL_OTHER in grouped_items:
            sorted_stores.append(LABEL_OTHER)

        margin_left = 1.0 * cm
        margin_right = 1.0 * cm
        margin_top = 1.0 * cm
        margin_bottom = 1.5 * cm

        usable_width = width - margin_left - margin_right
        col_width = usable_width / 4
        col_gap = 0.2 * cm
        effective_col_width = col_width - col_gap

        y_top = height - margin_top

        # Nagłówek główny
        c.setFont(self.font_name, 10)
        header_text = list_name.upper()
        text_w = c.stringWidth(header_text, self.font_name, 10)

        col_1_center = margin_left + (effective_col_width / 2)
        c.drawString(col_1_center - (text_w / 2), y_top, header_text)
        c.line(col_1_center - (text_w / 2), y_top - 2, col_1_center + (text_w / 2), y_top - 2)

        y_start_list = y_top - 0.8 * cm
        current_y = y_start_list
        current_col = 0
        row_height = 0.5 * cm
        header_height = 0.6 * cm
        box_size = 8
        dot_width = c.stringWidth(".", self.font_name, 9)

        def check_space(needed_height):
            nonlocal current_y, current_col
            if current_y - needed_height < margin_bottom:
                current_col += 1
                current_y = y_start_list
                if current_col > 3:
                    c.showPage()
                    c.setFont(self.font_name, 9)
                    current_col = 0
                    current_y = height - margin_top
                return True
            return False

        for store_name in sorted_stores:
            store_items = grouped_items[store_name]
            check_space(header_height + row_height + 0.2*cm)

            col_x_start = margin_left + (current_col * col_width)

            # Nagłówek sklepu
            c.setFont(self.font_name, 9)
            c.drawString(col_x_start, current_y - 0.3*cm, store_name.upper())
            sw = c.stringWidth(store_name.upper(), self.font_name, 9)
            c.setLineWidth(0.5)
            c.line(col_x_start, current_y - 0.35*cm, col_x_start + sw, current_y - 0.35*cm)

            current_y -= (header_height + 0.15 * cm)

            # Produkty
            c.setFont(self.font_name, 9)
            for prod_raw, qty_raw in store_items:
                check_space(row_height)
                col_x_start = margin_left + (current_col * col_width)
                col_x_end = col_x_start + effective_col_width

                prod_text = prod_raw.upper()
                qty_text = qty_raw.lower()

                # Kwadracik
                c.setLineWidth(1)
                c.rect(col_x_end - box_size, current_y, box_size, box_size, fill=0)

                # Ilość
                qty_w = c.stringWidth(qty_text, self.font_name, 9)
                qty_x = col_x_end - box_size - 4
                c.drawRightString(qty_x, current_y + 1, qty_text)

                # Produkt + kropki
                max_text_width = qty_x - col_x_start - 5
                display_prod = prod_text
                while c.stringWidth(display_prod, self.font_name, 9) > max_text_width and len(display_prod) > 0:
                    display_prod = display_prod[:-1]

                c.drawString(col_x_start, current_y + 1, display_prod)

                prod_end_x = col_x_start + c.stringWidth(display_prod, self.font_name, 9) + 2
                qty_start_x = qty_x - qty_w - 2
                if qty_start_x > prod_end_x:
                    space = qty_start_x - prod_end_x
                    if space > 0:
                        num_dots = int(space / dot_width)
                        c.drawString(prod_end_x, current_y + 1, "." * num_dots)

                current_y -= row_height

            current_y -= 0.1 * cm

        c.save()
