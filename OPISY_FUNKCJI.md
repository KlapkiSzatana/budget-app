# Opisy funkcji

Poniżej znajduje się praktyczny opis funkcji i metod z katalogu `3.0_BETA`. Opisy odnoszą się do aktualnej wersji kodu po porządkach.

## `budget-app.py`

### `BudgetApp`

- `__init__`: Inicjuje okno główne, bazę danych, ustawienia aplikacji i buduje cały interfejs.
- `open_settings_dialog`: Otwiera okno ustawień i po zapisaniu odświeża widoczność modułów oraz dane.
- `apply_module_visibility`: Ukrywa lub pokazuje moduły i boczne panele zgodnie z konfiguracją użytkownika.
- `open_month_menu`: Buduje i wyświetla menu wyboru miesiąca.
- `open_year_menu`: Buduje i wyświetla menu wyboru roku na podstawie danych z bazy.
- `change_date_filter`: Zmienia aktywny miesiąc lub rok i przeładowuje widok.
- `change_week`: Przesuwa widok tygodniowy o wskazaną liczbę tygodni.
- `get_menu_style`: Zwraca wspólny arkusz stylów dla menu kontekstowych.
- `check_new_week_prompt`: Sprawdza, czy dla nowego tygodnia trzeba pokazać dialog konfiguracji limitu.
- `check_new_week_prompt.safe_startup_refresh`: Po pierwszej konfiguracji tygodnia bezpiecznie przełącza widok i odświeża dane startowe.
- `setup_top_bar`: Buduje górny pasek narzędzi z filtrami, modułami i skrótami akcji.
- `setup_top_bar._open_backup`: Otwiera dialog tworzenia i przywracania kopii zapasowej.
- `setup_top_bar._open_shopping`: Otwiera moduł list zakupów z paska górnego.
- `schedule_update`: Uruchamia opóźnione odświeżenie danych przez timer.
- `open_weekly_settings`: Otwiera ustawienia limitu tygodniowego dla aktywnego tygodnia.
- `open_weekly_settings.safe_delayed_update`: Po zamknięciu dialogu bezpiecznie przełącza widok i odświeża dane.
- `open_weekly_settings_safe`: Zatrzymuje timer odświeżania i otwiera ustawienia tygodniowe.
- `open_bills_manager`: Otwiera menedżer rachunków i po zamknięciu odświeża ekran główny.
- `setup_dashboard`: Buduje główny panel statystyk, kafelków i sekcji bocznych.
- `setup_weekly_ui`: Tworzy elementy interfejsu dla widoku tygodniowego.
- `check_weekly_bills`: Sprawdza rachunki przypadające na aktualny zakres tygodnia.
- `update_weekly_stats`: Przelicza i odświeża statystyki limitu tygodniowego.
- `_handle_any_category_click`: Obsługuje kliknięcie kategorii na wykresie lub w legendzie.
- `_clear_layout_safely`: Czyści layout z widżetów bez zostawiania osieroconych obiektów.
- `setup_buttons`: Buduje główne przyciski akcji aplikacji.
- `setup_table`: Konfiguruje tabelę rejestru transakcji.
- `keyPressEvent`: Obsługuje skróty klawiaturowe dla okna głównego.
- `open_context_menu`: Wyświetla menu kontekstowe dla tabeli transakcji.
- `preview_attachment`: Otwiera podgląd załącznika przypisanego do transakcji.
- `download_attachment`: Pozwala zapisać załącznik transakcji na dysk.
- `run_guide_with_confirm`: Potwierdza uruchomienie przewodnika i startuje onboarding.
- `setup_footer`: Buduje stopkę z wyszukiwarką, podsumowaniem i informacjami o wersji.
- `get_current_month_str`: Zwraca bieżący miesiąc w formacie używanym przez bazę.
- `update_monthly_label`: Aktualizuje etykietę pokazującą aktywny miesiąc i rok.
- `toggle_month_lock`: Blokuje lub odblokowuje edycję aktywnego miesiąca.
- `check_bills_notifications`: Wylicza liczbę nadchodzących rachunków i odświeża wskaźnik powiadomień.
- `open_account_history`: Otwiera historię operacji dla wybranego konta.
- `load_transactions`: Pobiera, filtruje i renderuje dane finansowe dla aktywnego widoku.
- `load_transactions.set_c`: Ustawia tekst i kolor pojedynczej komórki w tabeli transakcji.
- `load_transactions.get_arrow`: Wyznacza znak trendu przy porównywaniu bieżących i poprzednich wartości.
- `delete_selected_transaction`: Usuwa zaznaczone transakcje po potwierdzeniu użytkownika.
- `open_income_dialog`: Otwiera dialog dodawania przychodu.
- `open_expense_dialog`: Otwiera dialog dodawania wydatku.
- `open_savings_dialog`: Otwiera dialog operacji oszczędnościowych.
- `open_liabilities_dialog`: Otwiera dialog długu i zapisuje nowe zobowiązanie albo spłatę.
- `open_debtors_dialog`: Otwiera dialog dłużników i zapisuje pożyczkę albo zwrot.
- `update_debtors_display`: Odświeża panel aktywnych dłużników i ich postęp spłat.
- `filter_transactions_by_string`: Ustawia tekst wyszukiwania i odświeża listę transakcji.
- `delete_debtor`: Usuwa dłużnika z listy po potwierdzeniu.
- `open_transfer_dialog`: Otwiera dialog transferu środków między celami oszczędnościowymi.
- `open_new_goal_dialog`: Otwiera dialog tworzenia nowego celu oszczędnościowego.
- `open_edit_dialog`: Otwiera edycję aktualnie zaznaczonej transakcji.
- `save_transaction`: Waliduje dane z dialogu i zapisuje nową transakcję do bazy.
- `open_filter_dialog`: Otwiera menu filtrowania po kategoriach.
- `open_report_dialog`: Otwiera wybór raportu i okno zapisu pliku PDF.
- `gen_rep`: Przygotowuje dane raportowe i uruchamia generator PDF.
- `update_goals_display`: Odświeża listę celów oszczędnościowych i ich stan realizacji.
- `delete_goal_handler`: Obsługuje usuwanie celu oszczędnościowego.
- `update_liabilities_display`: Odświeża panel aktywnych zobowiązań i ich postęp spłat.
- `delete_liability`: Usuwa zobowiązanie z listy po potwierdzeniu.
- `export_selected_to_pdf`: Eksportuje zaznaczone transakcje i ich załączniki do jednego pliku PDF.
- `closeEvent`: Zapisuje stan okna, szerokości kolumn i ewentualnie wykonuje kopię zapasową przy zamknięciu.
- `auto_start_guide`: Decyduje, czy przewodnik ma wystartować automatycznie.
- `run_guide`: Uruchamia przewodnik po interfejsie.

### `HardcodedSystemTranslator`

- `__init__`: Ładuje ręczną mapę tłumaczeń dla tekstów systemowych Qt.
- `translate`: Zwraca polski odpowiednik tekstu systemowego albo pusty ciąg.

## `config.py`

- `_`: Funkcja tłumacząca oparta o `gettext` albo prosty fallback zwracający przekazany tekst.
- `setup_crash_handlers`: Włącza obsługę crashy i globalny handler wyjątków Pythona.
- `global_exception_handler`: Loguje nieobsłużony wyjątek i próbuje pokazać użytkownikowi okno błędu.
- `save_table_widths`: Zapisuje szerokości kolumn tabeli do pliku JSON.
- `load_table_widths`: Odczytuje zapisane szerokości kolumn tabeli.

## `database.py`

### `DatabaseManager`

- `__init__`: Otwiera bazę danych, przygotowuje katalog załączników i uruchamia migracje startowe.
- `create_tables`: Tworzy brakujące tabele oraz wykonuje podstawowe migracje schematu.
- `initialize_config`: Wypełnia domyślną konfigurację aplikacji, jeśli jeszcze nie istnieje.
- `get_config`: Odczytuje wartość konfiguracyjną z tabeli `app_config`.
- `save_config`: Zapisuje konfigurację w formacie JSON.
- `get_config_bool`: Odczytuje konfigurację i zwraca ją jako wartość logiczną.
- `set_config`: Zapisuje prostą wartość konfiguracyjną bez dodatkowej obróbki JSON.
- `get_weekly_config`: Zwraca globalną konfigurację limitu tygodniowego.
- `run_fix_savings_names`: Naprawia stare nazwy podkategorii oszczędności w transakcjach.
- `update_goals_table_structure`: Dodaje brakującą kolumnę `default_account_id` do tabeli celów.
- `_copy_with_progress`: Kopiuje plik porcjami i raportuje postęp.
- `perform_backup`: Tworzy kopię zapasową ZIP z bazą danych i załącznikami.
- `_cleanup_backups`: Usuwa najstarsze kopie zapasowe ponad limit.
- `restore_database`: Przywraca bazę i załączniki z pliku kopii oraz uruchamia migracje po odtworzeniu.
- `add_transaction`: Zapisuje nową transakcję i opcjonalnie jej załącznik.
- `transfer_savings`: Rejestruje atomowy transfer oszczędności pomiędzy kontami.
- `update_transaction`: Aktualizuje dane istniejącej transakcji i ewentualnie podmienia załącznik.
- `delete_transaction`: Usuwa transakcję i powiązany plik załącznika.
- `get_all_transactions`: Zwraca wszystkie transakcje w kolejności od najnowszych.
- `get_year_transactions`: Zwraca transakcje z wybranego roku.
- `get_transaction_by_id`: Pobiera pojedynczą transakcję po identyfikatorze.
- `get_expenses_in_range`: Sumuje wydatki w przedziale dat, opcjonalnie po wybranych kategoriach.
- `add_person`: Dodaje osobę do słownika przychodów.
- `add_category`: Dodaje kategorię i aktualizuje konfigurację tygodniową.
- `delete_category_safe`: Bezpiecznie usuwa kategorię, przenosząc stare wpisy do `Inne`.
- `get_people`: Zwraca listę osób z tabeli słownikowej.
- `get_categories`: Zwraca listę kategorii wydatków.
- `add_goal`: Dodaje nowy cel oszczędnościowy.
- `delete_goal`: Usuwa cel oszczędnościowy.
- `get_goals`: Zwraca nazwy wszystkich celów.
- `get_goals_progress_simple`: Zwraca uproszczone dane o postępie realizacji celów.
- `add_liability`: Dodaje nowe zobowiązanie i zwraca jego identyfikator.
- `delete_liability`: Usuwa zobowiązanie.
- `get_liabilities_list`: Zwraca nazwy aktywnych zobowiązań z niespłaconym saldem.
- `get_liabilities_status`: Zwraca pełny stan zobowiązań wraz z sumą spłat.
- `add_debtor`: Dodaje nowego dłużnika i zwraca jego identyfikator.
- `delete_debtor`: Usuwa dłużnika.
- `get_debtors_list`: Zwraca nazwy aktywnych dłużników.
- `get_debtors_status`: Zwraca pełny stan dłużników wraz z kwotami zwrotów.
- `get_all_historical_liabilities`: Zbiera historyczne nazwy długów i dłużników z transakcji.
- `is_month_locked`: Sprawdza, czy wskazany miesiąc jest zablokowany do edycji.
- `lock_month`: Blokuje miesiąc.
- `unlock_month`: Zdejmuje blokadę miesiąca.
- `get_total_savings_cash_pln`: Sumuje wszystkie operacje oszczędnościowe w bazie.
- `get_net_balance_pln_before_date`: Liczy bilans netto przed wskazaną datą.
- `create_shopping_list`: Tworzy nową listę zakupów i zwraca jej identyfikator.
- `get_shopping_lists`: Zwraca archiwum list zakupów.
- `add_shopping_item`: Dodaje produkt do listy zakupów.
- `get_shopping_items`: Zwraca wszystkie produkty należące do wskazanej listy.
- `delete_shopping_item`: Usuwa pojedynczy produkt z listy zakupów.
- `update_shopping_item`: Aktualizuje nazwę i ilość produktu na liście zakupów.
- `close_shopping_list`: Oznacza listę zakupów jako zamkniętą.
- `delete_shopping_list`: Usuwa listę zakupów wraz z jej pozycjami.
- `add_shop`: Dodaje sklep do słownika sklepów.
- `get_shops`: Zwraca listę sklepów do podpowiedzi w dialogach.
- `set_weekly_limit_for_week`: Zapisuje limit tygodniowy i listę kategorii dla konkretnego tygodnia.
- `get_weekly_limit_for_week`: Odczytuje limit tygodniowy zapisany dla konkretnego tygodnia.
- `is_weekly_system_enabled`: Sprawdza, czy system limitu tygodniowego jest włączony globalnie.
- `set_weekly_system_enabled`: Włącza lub wyłącza system tygodniowy w konfiguracji.
- `get_pending_bills`: Zwraca nieopłacone rachunki oczekujące.
- `add_pending_bill`: Dodaje rachunek do listy oczekujących płatności.
- `mark_bill_paid`: Oznacza rachunek jako zapłacony.
- `delete_pending_bill`: Usuwa rachunek z listy.
- `toggle_bill_recurring`: Zmienia flagę cykliczności rachunku.
- `get_available_years`: Zwraca lata obecne w historii transakcji.
- `get_savings_total_for_subcat`: Sumuje oszczędności zapisane dla konkretnego celu.
- `get_attachment`: Odczytuje plik załącznika przypisany do transakcji.
- `get_active_liabilities_detailed`: Zwraca szczegółową listę aktywnych zobowiązań i pozostałych kwot.
- `get_active_debtors_detailed`: Zwraca szczegółową listę aktywnych dłużników i pozostałych kwot.
- `add_account`: Dodaje konto finansowe z kolorem interfejsu.
- `get_accounts`: Zwraca wszystkie konta wraz z kolorami.
- `delete_account`: Usuwa konto i przenosi jego transakcje na konto główne.
- `get_account_history`: Zwraca historię operacji dla wskazanego konta i zakresu dat.
- `is_module_enabled`: Sprawdza stan modułu w tabeli `modules`.
- `set_module_state`: Zapisuje stan aktywności modułu.
- `get_account_balance`: Liczy saldo konta z uwzględnieniem typu operacji i opcjonalnej daty granicznej.
- `update_account_color`: Zmienia kolor przypisany do konta.

## `dialogs.py`

### `ProcessingDialog`

- `__init__`: Tworzy prosty modalny dialog z paskiem postępu.

### `BackupDialog`

- `__init__`: Buduje okno zarządzania kopiami zapasowymi.
- `load_config`: Wczytuje ustawienia backupu do formularza.
- `save_config`: Zapisuje ustawienia backupu z formularza.
- `select_path`: Otwiera wybór katalogu dla kopii zapasowych.
- `create_now`: Uruchamia tworzenie kopii zapasowej i pokazuje postęp.
- `create_now.update_pbar`: Aktualizuje pasek postępu podczas tworzenia backupu.
- `restore_now`: Przywraca bazę z wybranego pliku kopii i restartuje aplikację.
- `restore_now.update_pbar`: Aktualizuje pasek postępu podczas odtwarzania backupu.
- `closeEvent`: Przed zamknięciem zapisuje aktualną konfigurację backupu.

### `WeeklyLimitDialog`

- `__init__`: Buduje dialog konfiguracji limitu tygodniowego dla konkretnego tygodnia.
- `toggle_inputs`: Włącza lub wyłącza pola formularza zależnie od stanu systemu tygodniowego.
- `load_settings`: Wczytuje zapisane limity i zaznaczone kategorie.
- `select_all`: Zaznacza wszystkie kategorie na liście.
- `deselect_all`: Odznacza wszystkie kategorie na liście.
- `save_and_close`: Zapisuje ustawienia tygodniowe i zamyka dialog.

### `IncomeDialog`

- `__init__`: Buduje formularz dodawania przychodu.
- `select_attachment`: Wczytuje plik potwierdzenia do nowego przychodu.
- `get_data`: Zbiera i zwraca dane formularza przychodu.

### `AddExpenseDialog`

- `__init__`: Buduje formularz dodawania wydatku.
- `select_attachment`: Wczytuje załącznik do wydatku.
- `add_c`: Dodaje nową kategorię wydatków z poziomu dialogu.
- `del_c`: Usuwa wybraną kategorię wydatków w bezpieczny sposób.
- `get_data`: Zbiera i zwraca dane formularza wydatku.

### `AddGoalDialog`

- `__init__`: Buduje formularz tworzenia celu oszczędnościowego.
- `accept`: Waliduje pola celu przed zamknięciem dialogu.
- `get_data`: Zwraca nazwę celu, kwotę docelową i konto domyślne.

### `SavingsTransferDialog`

- `__init__`: Buduje dialog przenoszenia oszczędności między kontami.
- `get_data`: Zwraca dane transferu oszczędności.

### `AddSavingsDialog`

- `__init__`: Buduje formularz wpłaty lub wypłaty oszczędności.
- `select_attachment`: Wczytuje załącznik do operacji oszczędnościowej.
- `add_g`: Otwiera tworzenie nowego celu i odświeża listę celów.
- `migrate_savings`: Otwiera dialog migracji oszczędności między kontami i zapisuje transfer.
- `get_data`: Zbiera i zwraca dane operacji oszczędnościowej.

### `TransferDialog`

- `__init__`: Buduje formularz przesunięcia środków między celami oszczędnościowymi.
- `get_data`: Zwraca źródło, cel, kwotę i konto transferu.

### `LiabilitiesDialog`

- `__init__`: Buduje dialog dodawania zobowiązania albo rejestracji jego spłaty.
- `select_attachment`: Wczytuje załącznik do operacji na zobowiązaniu.
- `toggle_mode`: Przełącza formularz między trybem nowego długu a spłaty.
- `refresh_combo`: Ładuje listę aktywnych zobowiązań do spłaty.
- `accept`: Waliduje formularz przed zatwierdzeniem.
- `get_data`: Zwraca dane nowego zobowiązania albo spłaty.

### `DebtorsDialog`

- `__init__`: Buduje dialog dodawania dłużnika albo rejestracji zwrotu.
- `select_attachment`: Wczytuje załącznik do operacji na dłużniku.
- `toggle_mode`: Przełącza formularz między pożyczeniem pieniędzy a zwrotem.
- `refresh_combo`: Ładuje listę aktywnych dłużników.
- `accept`: Waliduje dane dialogu przed zapisaniem.
- `get_data`: Zwraca dane nowego dłużnika albo zwrotu długu.

### `FilterDialog`

- `__init__`: Buduje prosty dialog filtrowania po kategorii.
- `accept`: Zapisuje wybraną kategorię filtra i zamyka dialog.

### `ReportSelectionDialog`

- `__init__`: Buduje dialog wyboru raportu miesięcznego lub rocznego.
- `accept`: Przekształca wybór użytkownika do formatu używanego przez generator raportów.

### `EditDialog`

- `__init__`: Buduje formularz edycji istniejącej transakcji.
- `select_attachment`: Wczytuje nowy załącznik do edytowanej transakcji.
- `get_data`: Zwraca dane po edycji transakcji.

### `BillsManagerDialog`

- `__init__`: Buduje okno zarządzania oczekującymi rachunkami.
- `load_data`: Ładuje tabelę rachunków z bazy.
- `add_bill`: Dodaje nowy rachunek do listy oczekujących płatności.
- `pay_bill`: Oznacza rachunek jako opłacony i zapisuje transakcję wydatku.
- `delete_bill`: Usuwa wybrany rachunek.

### `BillPaymentConfirmDialog`

- `__init__`: Buduje dialog potwierdzenia płatności rachunku z wyborem konta.
- `select_attachment`: Wczytuje potwierdzenie zapłaty jako załącznik.
- `get_data`: Zwraca szczegóły płatności, załącznik i konto źródłowe.

### `GuideArrow`

- `__init__`: Tworzy graficzny wskaźnik używany przez przewodnik po aplikacji.
- `set_direction`: Ustawia kierunek grotu strzałki.
- `paintEvent`: Rysuje strzałkę na przezroczystym widżecie.

### `GuideBubble`

- `__init__`: Tworzy dymek przewodnika z tekstem, paskiem postępu i strzałką.
- `update_progress`: Odsuwa przewodnik do kolejnego kroku po upływie czasu.
- `show`: Pokazuje dymek i jego strzałkę.
- `close`: Zamyka dymek oraz strzałkę.
- `deleteLater`: Odkłada usunięcie dymka i strzałki.
- `move_to_target`: Ustawia dymek przy wskazanym elemencie interfejsu.

### `AppGuide`

- `__init__`: Definiuje kroki przewodnika po aplikacji.
- `start`: Resetuje indeks kroku i uruchamia przewodnik od początku.
- `show_step`: Wyświetla aktualny krok przewodnika.
- `next_step`: Przechodzi do kolejnego kroku przewodnika.
- `stop_guide`: Zatrzymuje przewodnik i czyści jego elementy.

### `AccountHistoryDialog`

- `__init__`: Buduje okno historii operacji dla pojedynczego konta.
- `load_history`: Ładuje transakcje konta zgodnie z ustawionymi filtrami.

## `reports.py`

- `cleanup_generated_files`: Usuwa pliki tymczasowe PDF zapamiętane na czas sesji.

### `PDFReportGenerator`

- `__init__`: Inicjuje generator raportu PDF i stan rejestracji fontów.
- `register_system_font`: Szuka systemowej czcionki z polskimi znakami i rejestruje ją w ReportLab.
- `generate`: Buduje pełny raport finansowy PDF z podsumowaniami i rejestrem transakcji.
- `_get_table_style`: Zwraca styl tabel dla sekcji raportu.
- `_add_footer`: Rysuje stopkę raportu na każdej stronie.

### `ShoppingPDFGenerator`

- `__init__`: Inicjuje generator PDF dla list zakupów.
- `_register_polish_font`: Rejestruje czcionkę obsługującą polskie znaki.
- `generate`: Buduje wielokolumnowy PDF z listą zakupów pogrupowaną po sklepach.
- `generate.check_space`: Przełącza kolumnę lub stronę, gdy zabraknie miejsca na kolejne pozycje.

## `settings_dialog.py`

### `SettingsDialog`

- `__init__`: Buduje okno ustawień modułów i zarządzania kontami.
- `refresh_accounts`: Odświeża tabelę kont i ich kolorów.
- `change_account_color`: Otwiera wybór koloru i zapisuje zmianę dla konta.
- `add_account_action`: Dodaje nowe konto na podstawie danych z formularza.
- `save_and_close`: Zapisuje ustawienia modułów i zamyka dialog.

## `shopping.py`

### `ShoppingHistoryDialog`

- `__init__`: Buduje okno archiwum list zakupów.
- `load_lists`: Wczytuje listy zakupów do tabeli archiwum.
- `show_preview`: Pokazuje podgląd pozycji z aktualnie wybranej listy.
- `open_selected`: Zatwierdza otwarcie wybranej listy zakupów.
- `close_selected_list`: Oznacza wybraną listę jako zamkniętą.
- `delete_selected`: Trwale usuwa wybraną listę zakupów.

### `ShoppingListDialog`

- `__init__`: Buduje główne okno listy zakupów.
- `refresh_shops`: Odświeża słownik sklepów w polu wyboru.
- `_ensure_list_exists`: Tworzy listę zakupów w bazie, jeśli jeszcze nie istnieje.
- `load_items`: Ładuje pozycje bieżącej listy do tabeli.
- `add_item`: Dodaje nowy produkt do listy zakupów.
- `delete_item`: Usuwa zaznaczony produkt z listy.
- `_force_status_update`: Zmienia status listy bezpośrednio w bazie.
- `print_list`: Generuje PDF listy zakupów i otwiera go w systemie.
- `send_email`: Tworzy wiadomość e-mail z treścią listy zakupów.
- `finalize_list`: Kończy pracę z listą i oznacza ją jako zamkniętą.
- `open_history`: Otwiera archiwum i pozwala wskazać listę do ponownej edycji.
