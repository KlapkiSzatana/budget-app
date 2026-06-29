package pl.klapkiszatana.budgetmobile;

import android.Manifest;
import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.BitmapFactory;
import android.os.Build;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public class BudgetReminderReceiver extends BroadcastReceiver {
    private static final String CHANNEL_ID = "budget_reminders";
    private static final int REQUEST_ALARM = 4201;
    private static final long MINUTE = 60L * 1000L;

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent == null ? null : intent.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(action) || Intent.ACTION_MY_PACKAGE_REPLACED.equals(action)) {
            schedule(context);
            return;
        }
        if (!prefs(context).getBoolean("notifications_master", true)) {
            return;
        }
        if (!canNotify(context)) {
            return;
        }
        createChannel(context);
        if (!isWithinNotifyWindow(context, System.currentTimeMillis())) {
            schedule(context);
            return;
        }

        File dbFile = new File(context.getFilesDir(), "budzet.db");
        if (!dbFile.isFile()) {
            schedule(context);
            return;
        }

        SQLiteDatabase db = null;
        boolean sent = false;
        try {
            db = SQLiteDatabase.openDatabase(dbFile.getAbsolutePath(), null, SQLiteDatabase.OPEN_READONLY);
            sent = checkSmartNotifications(context, db)
                    || checkBalance(context, db)
                    || checkBills(context, db)
                    || checkWeeklyLimit(context, db)
                    || checkGoals(context, db)
                    || checkDebts(context, db)
                    || checkDailyExpenseReminder(context, db)
                    || checkWeeklyBackup(context);
        } catch (Exception ignored) {
        } finally {
            if (db != null) {
                db.close();
            }
            setNextRoutine(context, sent ? 65 : 110);
            schedule(context);
        }
    }

    static void schedule(Context context) {
        SharedPreferences p = prefs(context);
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        PendingIntent pi = alarmIntent(context);
        if (manager == null || pi == null) {
            return;
        }
        if (!p.getBoolean("notifications_master", true)) {
            manager.cancel(pi);
            return;
        }
        manager.cancel(pi);
        long now = System.currentTimeMillis();
        long routineAt = p.getLong("next_routine_at", 0L);
        if (routineAt <= 0L) {
            routineAt = nextAllowedTime(context, now + 75 * MINUTE);
            p.edit().putLong("next_routine_at", routineAt).apply();
        }
        long smartAt = nextSmartTime(p);
        long triggerAt = smartAt > 0L ? Math.min(routineAt, smartAt) : routineAt;
        triggerAt = nextAllowedTime(context, Math.max(triggerAt, now + MINUTE));
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !manager.canScheduleExactAlarms()) {
                manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pi);
            } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                manager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pi);
            } else {
                manager.setExact(AlarmManager.RTC_WAKEUP, triggerAt, pi);
            }
        } catch (SecurityException ex) {
            manager.set(AlarmManager.RTC_WAKEUP, triggerAt, pi);
        }
    }

    static void sendTest(Context context) {
        if (!canNotify(context)) {
            return;
        }
        createChannel(context);
        notify(context, "BudżetApp", "Powiadomienia są włączone.");
    }

    static void scheduleAfterTransaction(Context context, String type) {
        if (!prefs(context).getBoolean("notifications_master", true)) {
            return;
        }
        long now = System.currentTimeMillis();
        SharedPreferences.Editor edit = prefs(context).edit();
        edit.putLong("smart_balance_at", nextAllowedTime(context, now + 30 * MINUTE));
        if ("expense".equals(type)) {
            edit.putLong("smart_expense_1_at", nextAllowedTime(context, now + 150 * MINUTE));
            edit.putLong("smart_expense_2_at", nextAllowedTime(context, now + 330 * MINUTE));
        }
        edit.apply();
        schedule(context);
    }

    private static PendingIntent alarmIntent(Context context) {
        Intent intent = new Intent(context, BudgetReminderReceiver.class);
        intent.setAction("pl.klapkiszatana.budgetmobile.REMINDERS");
        return PendingIntent.getBroadcast(
                context,
                REQUEST_ALARM,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
    }

    private static boolean checkSmartNotifications(Context context, SQLiteDatabase db) {
        SharedPreferences p = prefs(context);
        long now = System.currentTimeMillis();
        SharedPreferences.Editor edit = p.edit();
        if (p.getLong("smart_balance_at", 0L) > 0L && p.getLong("smart_balance_at", 0L) <= now
                && p.getBoolean("notify_balance", true)) {
            edit.remove("smart_balance_at").apply();
            notify(context, "Stan kont po wpisie", accountBalanceBody(db));
            return true;
        }
        if (p.getLong("smart_expense_1_at", 0L) > 0L && p.getLong("smart_expense_1_at", 0L) <= now
                && p.getBoolean("notify_daily_expenses", true)) {
            edit.remove("smart_expense_1_at").apply();
            notify(context, "Wydatki", "Jeśli doszły kolejne wydatki, dopisz je od razu.");
            return true;
        }
        if (p.getLong("smart_expense_2_at", 0L) > 0L && p.getLong("smart_expense_2_at", 0L) <= now
                && p.getBoolean("notify_daily_expenses", true)) {
            edit.remove("smart_expense_2_at").apply();
            notify(context, "Wydatki", "Krótka kontrola: czy wszystkie dzisiejsze wydatki są wpisane?");
            return true;
        }
        return false;
    }

    private static String accountBalanceBody(SQLiteDatabase db) {
        List<String> parts = new ArrayList<>();
        double total = 0.0;
        try (Cursor c = db.rawQuery("SELECT id, name, initial_balance FROM accounts ORDER BY id", null)) {
            while (c.moveToNext()) {
                long id = c.getLong(0);
                String name = c.getString(1);
                double balance = c.getDouble(2) + signedTransactionsForAccount(db, id);
                total += balance;
                parts.add(name + ": " + money(balance));
            }
        }
        String body = "Razem: " + money(total);
        if (!parts.isEmpty()) {
            body += "\n" + join(parts);
        }
        return body;
    }

    private static long nextSmartTime(SharedPreferences p) {
        long next = 0L;
        for (String key : new String[]{"smart_balance_at", "smart_expense_1_at", "smart_expense_2_at"}) {
            long value = p.getLong(key, 0L);
            if (value > 0L && (next == 0L || value < next)) {
                next = value;
            }
        }
        return next;
    }

    private static void setNextRoutine(Context context, boolean afterSent) {
        setNextRoutine(context, afterSent ? 65 : 110);
    }

    private static void setNextRoutine(Context context, int baseMinutes) {
        long jitter = Math.abs(System.currentTimeMillis() % 31L);
        long next = nextAllowedTime(context, System.currentTimeMillis() + (baseMinutes + jitter) * MINUTE);
        prefs(context).edit().putLong("next_routine_at", next).apply();
    }

    private static boolean isWithinNotifyWindow(Context context, long when) {
        int start = notifyStartHour(context);
        int end = notifyEndHour(context);
        if (start == end) {
            return true;
        }
        Calendar cal = Calendar.getInstance();
        cal.setTimeInMillis(when);
        int hour = cal.get(Calendar.HOUR_OF_DAY);
        if (start < end) {
            return hour >= start && hour < end;
        }
        return hour >= start || hour < end;
    }

    private static long nextAllowedTime(Context context, long desired) {
        if (isWithinNotifyWindow(context, desired)) {
            return desired;
        }
        int start = notifyStartHour(context);
        int end = notifyEndHour(context);
        if (start == end) {
            return desired;
        }
        Calendar cal = Calendar.getInstance();
        cal.setTimeInMillis(desired);
        int hour = cal.get(Calendar.HOUR_OF_DAY);
        if (start < end) {
            if (hour < start) {
                cal.set(Calendar.HOUR_OF_DAY, start);
            } else {
                cal.add(Calendar.DAY_OF_MONTH, 1);
                cal.set(Calendar.HOUR_OF_DAY, start);
            }
        } else {
            if (hour >= end && hour < start) {
                cal.set(Calendar.HOUR_OF_DAY, start);
            }
        }
        cal.set(Calendar.MINUTE, 0);
        cal.set(Calendar.SECOND, 0);
        cal.set(Calendar.MILLISECOND, 0);
        return cal.getTimeInMillis();
    }

    private static int notifyStartHour(Context context) {
        SharedPreferences p = prefs(context);
        return Math.max(0, Math.min(23, p.getInt("notify_start_hour", p.getInt("notify_hour", 8))));
    }

    private static int notifyEndHour(Context context) {
        return Math.max(0, Math.min(23, prefs(context).getInt("notify_end_hour", 18)));
    }

    private static boolean checkBalance(Context context, SQLiteDatabase db) {
        if (!prefs(context).getBoolean("notify_balance", true) || !onceToday(context, "balance")) {
            return false;
        }
        notify(context, "Stan kont", accountBalanceBody(db));
        return true;
    }

    private static boolean checkBills(Context context, SQLiteDatabase db) {
        if (!prefs(context).getBoolean("notify_bills", true)) {
            return false;
        }
        Calendar today = calendar(today());
        try (Cursor c = db.rawQuery("SELECT id, due_date, amount, description, IFNULL(is_recurring,0) " +
                "FROM pending_bills WHERE IFNULL(is_paid,0)=0", null)) {
            while (c.moveToNext()) {
                long id = c.getLong(0);
                String due = c.getString(1);
                long days = daysBetween(today, calendar(due));
                if (days < 0 || days > 7) {
                    continue;
                }
                String description = c.getString(3);
                double amount = c.getDouble(2);
                boolean recurring = c.getInt(4) == 1;
                if (!onceToday(context, "bill_" + id + "_" + days)) {
                    continue;
                }
                String when = days == 0 ? "Dzisiaj" : (days == 1 ? "Jutro" : "Za " + days + " dni");
                notify(context, recurring ? "Stały wydatek" : "Rachunek",
                        when + ": " + description + " " + money(amount) + ".");
                return true;
            }
        }
        return false;
    }

    private static boolean checkWeeklyLimit(Context context, SQLiteDatabase db) {
        if (!prefs(context).getBoolean("notify_weekly", true)) {
            return false;
        }
        WeeklyConfig cfg = weeklyConfig(db);
        if (!cfg.enabled || cfg.amount <= 0) {
            return false;
        }
        String start = weekStart(today());
        String end = addDays(start, 6);
        double spent = weeklySpent(db, start, end, cfg.categories);
        if (spent > cfg.amount && onceToday(context, "weekly_limit")) {
            notify(context, "Limit tygodniowy", "Przekroczono limit tygodniowy o " + money(spent - cfg.amount) + ".");
            return true;
        }
        return false;
    }

    private static boolean checkGoals(Context context, SQLiteDatabase db) {
        if (!prefs(context).getBoolean("notify_goals", true)) {
            return false;
        }
        try (Cursor c = db.rawQuery("SELECT id, name, target_amount FROM goals WHERE target_amount > 0", null)) {
            while (c.moveToNext()) {
                long id = c.getLong(0);
                String name = c.getString(1);
                double target = c.getDouble(2);
                double collected = scalar(db, "SELECT IFNULL(SUM(amount),0) FROM transactions " +
                        "WHERE type='goal_deposit' AND (ref_id=? OR (ref_id IS NULL AND subcategory=?))",
                        String.valueOf(id), name);
                double pct = target <= 0 ? 0 : collected / target * 100.0;
                if (pct >= 100.0 && onceEver(context, "goal_done_" + id)) {
                    notify(context, "Cel osiągnięty", "Cel \"" + name + "\" został osiągnięty!");
                    return true;
                } else if (pct >= 85.0 && pct < 100.0 && onceToday(context, "goal_close_" + id)) {
                    notify(context, "Cel prawie gotowy", "Brakuje jeszcze " + Math.round(100.0 - pct) + "% do celu \"" + name + "\".");
                    return true;
                }
            }
        }
        return false;
    }

    private static boolean checkDebts(Context context, SQLiteDatabase db) {
        if (!prefs(context).getBoolean("notify_debts", true)) {
            return false;
        }
        return checkDebtTable(context, db, "liabilities", "liability_repayment", "Termin spłaty długu",
                "Za %d dni termin spłaty długu \"%s\".")
                || checkDebtTable(context, db, "debtors", "debtor_repayment", "Dłużnik",
                "Dłużnik %s powinien oddać pieniądze za %d dni.");
    }

    private static boolean checkDebtTable(Context context, SQLiteDatabase db, String table, String type,
                                       String title, String pattern) {
        Calendar today = calendar(today());
        try (Cursor c = db.rawQuery("SELECT id, name, total_amount, deadline FROM " + table, null)) {
            while (c.moveToNext()) {
                long id = c.getLong(0);
                String name = c.getString(1);
                double total = c.getDouble(2);
                String deadline = c.getString(3);
                double paid = scalar(db, "SELECT IFNULL(SUM(amount),0) FROM transactions WHERE type=? AND ref_id=?",
                        type, String.valueOf(id));
                if (total - paid <= 0.01) {
                    continue;
                }
                long days = daysBetween(today, calendar(deadline));
                if (days < 0 || days > 7 || !onceToday(context, table + "_" + id + "_" + days)) {
                    continue;
                }
                String message = "debtors".equals(table)
                        ? String.format(Locale.ROOT, pattern, name, days)
                        : String.format(Locale.ROOT, pattern, days, name);
                if (days == 0) {
                    message = message.replace("Za 0 dni", "Dzisiaj");
                } else if (days == 1) {
                    message = message.replace("Za 1 dni", "Jutro");
                }
                notify(context, title, message);
                return true;
            }
        }
        return false;
    }

    private static boolean checkDailyExpenseReminder(Context context, SQLiteDatabase db) {
        if (!prefs(context).getBoolean("notify_daily_expenses", true) || !onceToday(context, "daily_expenses")) {
            return false;
        }
        double count = scalar(db, "SELECT COUNT(*) FROM transactions WHERE date=?", today());
        if (count < 1) {
            notify(context, "Wydatki", "Nie dodałeś dziś żadnych wydatków.");
            return true;
        }
        return false;
    }

    private static boolean checkWeeklyBackup(Context context) {
        if (!prefs(context).getBoolean("notify_backup", true)) {
            return false;
        }
        Calendar cal = Calendar.getInstance();
        if (cal.get(Calendar.DAY_OF_WEEK) == Calendar.MONDAY && onceToday(context, "weekly_backup")) {
            notify(context, "Kopia zapasowa", "Wykonaj kopię zapasową danych.");
            return true;
        }
        return false;
    }

    private static double signedTransactionsForAccount(SQLiteDatabase db, long accountId) {
        double balance = 0.0;
        try (Cursor c = db.rawQuery("SELECT type, amount FROM transactions WHERE account_id=?",
                new String[]{String.valueOf(accountId)})) {
            while (c.moveToNext()) {
                String type = c.getString(0);
                double amount = c.getDouble(1);
                balance += accountBalanceDelta(type, amount);
            }
        }
        return balance;
    }

    private static double accountBalanceDelta(String type, double amount) {
        if ("income".equals(type) || "debtor_repayment".equals(type)) {
            return amount;
        }
        if ("expense".equals(type)
                || "liability_repayment".equals(type)
                || "savings".equals(type)
                || "goal_deposit".equals(type)) {
            return -amount;
        }
        return 0.0;
    }

    private static WeeklyConfig weeklyConfig(SQLiteDatabase db) {
        WeeklyConfig cfg = new WeeklyConfig();
        String raw = config(db, "weekly_limit_config");
        if (raw == null) {
            return cfg;
        }
        try {
            JSONObject obj = new JSONObject(raw);
            cfg.enabled = obj.optBoolean("enabled", false);
            cfg.amount = obj.optDouble("amount", 0.0);
            JSONArray arr = obj.optJSONArray("categories");
            if (arr != null) {
                cfg.categories = new HashSet<>();
                for (int i = 0; i < arr.length(); i++) {
                    cfg.categories.add(arr.optString(i));
                }
            }
        } catch (Exception ignored) {
        }
        return cfg;
    }

    private static double weeklySpent(SQLiteDatabase db, String start, String end, Set<String> categories) {
        double total = 0.0;
        try (Cursor c = db.rawQuery("SELECT category, amount FROM transactions " +
                "WHERE type='expense' AND IFNULL(exclude_from_weekly,0)=0 AND date >= ? AND date <= ?",
                new String[]{start, end})) {
            while (c.moveToNext()) {
                if (categories == null || categories.contains(c.getString(0))) {
                    total += c.getDouble(1);
                }
            }
        }
        return total;
    }

    private static String config(SQLiteDatabase db, String key) {
        try (Cursor c = db.rawQuery("SELECT value FROM app_config WHERE key=?", new String[]{key})) {
            return c.moveToFirst() ? c.getString(0) : null;
        }
    }

    private static double scalar(SQLiteDatabase db, String sql, String... args) {
        try (Cursor c = db.rawQuery(sql, args)) {
            return c.moveToFirst() ? c.getDouble(0) : 0.0;
        }
    }

    private static boolean onceToday(Context context, String key) {
        String pref = "notified_" + key;
        String today = today();
        SharedPreferences p = prefs(context);
        if (today.equals(p.getString(pref, ""))) {
            return false;
        }
        p.edit().putString(pref, today).apply();
        return true;
    }

    private static boolean onceEver(Context context, String key) {
        String pref = "notified_" + key;
        SharedPreferences p = prefs(context);
        if (p.getBoolean(pref, false)) {
            return false;
        }
        p.edit().putBoolean(pref, true).apply();
        return true;
    }

    private static void notify(Context context, String title, String body) {
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) {
            return;
        }
        Intent open = new Intent(context, MainActivity.class);
        PendingIntent content = PendingIntent.getActivity(
                context,
                0,
                open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(context, CHANNEL_ID)
                : new Notification.Builder(context);
        builder.setSmallIcon(R.drawable.ic_notification)
                .setLargeIcon(BitmapFactory.decodeResource(context.getResources(), R.drawable.budget))
                .setColor(0xffc0392b)
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(new Notification.BigTextStyle().bigText(body))
                .setContentIntent(content)
                .setAutoCancel(true)
                .setPriority(Notification.PRIORITY_DEFAULT);
        manager.notify((int) (System.currentTimeMillis() & 0xfffffff), builder.build());
    }

    private static void createChannel(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return;
        }
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null || manager.getNotificationChannel(CHANNEL_ID) != null) {
            return;
        }
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "BudżetApp",
                NotificationManager.IMPORTANCE_DEFAULT
        );
        channel.setDescription("Przypomnienia budżetowe, rachunki, limity i cele.");
        manager.createNotificationChannel(channel);
    }

    private static boolean canNotify(Context context) {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU
                || context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(MainActivity.PREFS, Context.MODE_PRIVATE);
    }

    private static String today() {
        return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(new Date());
    }

    private static String weekStart(String date) {
        Calendar cal = calendar(date);
        int day = cal.get(Calendar.DAY_OF_WEEK);
        int delta = day == Calendar.SUNDAY ? -6 : Calendar.MONDAY - day;
        cal.add(Calendar.DAY_OF_MONTH, delta);
        return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(cal.getTime());
    }

    private static String addDays(String date, int days) {
        Calendar cal = calendar(date);
        cal.add(Calendar.DAY_OF_MONTH, days);
        return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(cal.getTime());
    }

    private static Calendar calendar(String date) {
        Calendar cal = Calendar.getInstance();
        try {
            Date parsed = new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).parse(date);
            if (parsed != null) {
                cal.setTime(parsed);
            }
        } catch (ParseException ignored) {
        }
        cal.set(Calendar.HOUR_OF_DAY, 0);
        cal.set(Calendar.MINUTE, 0);
        cal.set(Calendar.SECOND, 0);
        cal.set(Calendar.MILLISECOND, 0);
        return cal;
    }

    private static long daysBetween(Calendar start, Calendar end) {
        return (end.getTimeInMillis() - start.getTimeInMillis()) / (24L * 60L * 60L * 1000L);
    }

    private static String money(double value) {
        return String.format(Locale.ROOT, "%.2f zł", value);
    }

    private static String join(List<String> values) {
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < values.size(); i++) {
            if (i > 0) {
                out.append("\n");
            }
            out.append(values.get(i));
        }
        return out.toString();
    }

    private static class WeeklyConfig {
        boolean enabled;
        double amount;
        Set<String> categories;
    }
}
