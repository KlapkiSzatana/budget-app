package pl.klapkiszatana.budgetmobile;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.AlarmManager;
import android.app.DatePickerDialog;
import android.Manifest;
import android.content.ActivityNotFoundException;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.view.WindowManager;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;
import android.provider.OpenableColumns;
import android.text.Editable;
import android.text.InputType;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.TextWatcher;
import android.text.method.DigitsKeyListener;
import android.text.style.ForegroundColorSpan;
import android.util.Base64;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.ViewGroup;
import android.view.Window;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.view.animation.DecelerateInterpolator;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.AutoCompleteTextView;
import android.widget.MultiAutoCompleteTextView;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URL;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Date;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

public class MainActivity extends Activity {
    private static final int REQUEST_ATTACH = 31;
    private static final int REQUEST_EDIT_ATTACH = 33;
    private static final int REQUEST_IMPORT_BACKUP = 32;
    private static final int REQUEST_NOTIFICATIONS = 41;
    private static final long MAX_ATTACHMENT_BYTES = 20L * 1024L * 1024L;
    private static final long MAX_SYNC_ATTACHMENT_BYTES = 512L * 1024L * 1024L;
    private static final int MAX_SYNC_BODY_BYTES = 32 * 1024 * 1024;
    static final String PREFS = "budget_mobile_prefs";
    static final String EXTRA_OPEN_SCREEN = "pl.klapkiszatana.budgetmobile.OPEN_SCREEN";
    static final String ACTION_OPEN_SCREEN = "pl.klapkiszatana.budgetmobile.action.OPEN_SCREEN";
    private static final String[] SCREEN_ORDER = {
            "home", "add", "transactions", "goals", "debts", "bills", "shopping", "settings"
    };

    private static final int RED = Color.rgb(192, 57, 43);
    private static final int GREEN = Color.rgb(39, 174, 96);
    private static final int BLUE = Color.rgb(41, 128, 185);
    private static final int ORANGE = Color.rgb(211, 84, 0);
    private static final int PURPLE = Color.rgb(142, 68, 173);
    private int TEXT = Color.rgb(36, 49, 58);
    private int MUTED = Color.rgb(111, 125, 135);
    private int BORDER = Color.rgb(189, 195, 199);
    private int SURFACE = Color.rgb(246, 247, 249);
    private int WHITE = Color.rgb(255, 255, 255);

    private BudgetDb db;
    private MobileSyncServer mobileSyncServer;
    private ScrollView scroll;
    private LinearLayout root;
    private LinearLayout tabs;
    private FrameLayout body;
    private HorizontalScrollView tabScroll;
    private Button startTabButton;
    private LinearLayout content;
    private LinearLayout transactionListContainer;
    private ProgressBar refreshIndicator;
    private String currentScreen = "home";
    private String pendingTransactionSearch = "";
    private int currentYear;
    private int currentMonth;
    private final Set<Long> expandedTransactions = new HashSet<>();
    private final Set<String> expandedHomeGroups = new HashSet<>();
    private AttachmentDraft selectedAttachment;
    private AttachmentDraft pendingEditAttachment;
    private TextView pendingEditAttachmentText;
    private boolean pendingEditHadAttachment;
    private final Handler uiHandler = new Handler(Looper.getMainLooper());
    private Runnable searchRunnable;
    private String pendingScrollTag;
    private boolean screenTransitionRunning;
    private boolean refreshRunning;
    private float touchDownX;
    private float touchDownY;
    private int touchMode;
    private boolean touchAllowsPullRefresh;

    private Spinner txTypeSpinner;
    private Spinner txAccountSpinner;
    private Spinner txPickerSpinner;
    private EditText txDateInput;
    private EditText txCustomInput;
    private EditText txSubInput;
    private EditText txDetailsInput;
    private EditText txAmountInput;
    private CheckBox txExcludeWeekly;
    private TextView txAttachmentText;
    private Button txAddPickerValueButton;
    private EditText transactionSearchInput;

    private long selectedShoppingListId = -1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        applySystemPalette();

        getWindow().setSoftInputMode(
                WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE
        );

        applySystemBars();
        Calendar now = Calendar.getInstance();
        currentYear = now.get(Calendar.YEAR);
        currentMonth = now.get(Calendar.MONTH) + 1;

        db = new BudgetDb(this);
        db.open();
        startMobileSyncServer();
        setContentView(buildShell());
        installKeyboardVisibilityWatcher();
        ensureNotificationPermission();
        BudgetReminderReceiver.schedule(this);
        showScreen(screenFromIntent(getIntent()));
    }

    @Override
    protected void onDestroy() {
        stopMobileSyncServer();
        if (db != null) {
            db.close();
        }
        super.onDestroy();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        showScreen(screenFromIntent(intent));
    }

    @Override
    public boolean dispatchTouchEvent(MotionEvent event) {
        if (event != null && event.getAction() == MotionEvent.ACTION_DOWN) {
            View focused = getCurrentFocus();
            if (focused instanceof EditText && isTouchOutsideView(focused, event)) {
                hideKeyboard(focused);
                focused.clearFocus();
            }
        }
        return super.dispatchTouchEvent(event);
    }

    private boolean isTouchOutsideView(View view, MotionEvent event) {
        return !isTouchInsideView(view, event);
    }

    private boolean isTouchInsideView(View view, MotionEvent event) {
        if (view == null || event == null || !view.isShown()) {
            return false;
        }
        Rect bounds = new Rect();
        int[] location = new int[2];
        view.getLocationOnScreen(location);
        bounds.set(location[0], location[1], location[0] + view.getWidth(), location[1] + view.getHeight());
        return bounds.contains((int) event.getRawX(), (int) event.getRawY());
    }

    private void hideKeyboard(View view) {
        InputMethodManager imm = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
        if (imm != null) {
            imm.hideSoftInputFromWindow(view.getWindowToken(), 0);
        }
    }

    private void applySystemPalette() {
        boolean dark = (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)
                == Configuration.UI_MODE_NIGHT_YES;
        if (dark) {
            TEXT = Color.rgb(232, 236, 240);
            MUTED = Color.rgb(164, 174, 183);
            BORDER = Color.rgb(76, 86, 96);
            SURFACE = Color.rgb(19, 23, 28);
            WHITE = Color.rgb(31, 37, 43);
        } else {
            TEXT = Color.rgb(36, 49, 58);
            MUTED = Color.rgb(111, 125, 135);
            BORDER = Color.rgb(189, 195, 199);
            SURFACE = Color.rgb(246, 247, 249);
            WHITE = Color.rgb(255, 255, 255);
        }
    }

    private void applySystemBars() {
        Window window = getWindow();
        window.setStatusBarColor(SURFACE);
        window.setNavigationBarColor(SURFACE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            boolean dark = (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)
                    == Configuration.UI_MODE_NIGHT_YES;
            int flags = dark ? 0 : View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
            if (!dark && Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                flags |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            }
            window.getDecorView().setSystemUiVisibility(flags);
        }
    }

    private void ensureNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQUEST_NOTIFICATIONS);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_NOTIFICATIONS
                && grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            BudgetReminderReceiver.schedule(this);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null || data.getData() == null) {
            return;
        }

        if (requestCode == REQUEST_ATTACH) {
            attachFromUri(data.getData());
        } else if (requestCode == REQUEST_EDIT_ATTACH) {
            attachEditFromUri(data.getData());
        } else if (requestCode == REQUEST_IMPORT_BACKUP) {
            Uri uri = data.getData();
            new AlertDialog.Builder(this)
                    .setTitle("Import bazy")
                    .setMessage("Import zastąpi lokalną bazę w telefonie. Eksport z telefonu przed importem jest dobrym pomysłem.")
                    .setPositiveButton("Importuj", (d, w) -> importBackup(uri))
                    .setNegativeButton("Anuluj", null)
                    .show();
        }
    }

    private View buildShell() {
        LinearLayout shell = new LinearLayout(this);
        shell.setOrientation(LinearLayout.VERTICAL);
        shell.setBackgroundColor(SURFACE);
        shell.setPadding(dp(14), getStatusBarHeight() + dp(8), dp(14), dp(20));

        LinearLayout header = hbox();
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(0, 0, 0, dp(8));

        ImageView icon = new ImageView(this);
        icon.setImageResource(getResources().getIdentifier("budget", "drawable", getPackageName()));
        LinearLayout.LayoutParams iconParams = new LinearLayout.LayoutParams(dp(44), dp(44));
        header.addView(icon, iconParams);

        LinearLayout titleBox = vbox();
        titleBox.setPadding(dp(12), 0, 0, 0);
        titleBox.addView(text("BudżetApp Mobile", 22, RED, true));
        titleBox.addView(text("Zarządzanie Budżetem Domowym", 12, MUTED, false));
        header.addView(titleBox, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));

        Button sync = smallButton("SYNC", BLUE);
        sync.setOnClickListener(v -> confirmSync());
        header.addView(sync);
        shell.addView(header);

        body = new FrameLayout(this);
        scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setSmoothScrollingEnabled(true);
        scroll.setFocusable(true);
        scroll.setFocusableInTouchMode(true);
        scroll.setClipToPadding(false);
        scroll.setBackgroundColor(SURFACE);
        scroll.setOnTouchListener((v, event) -> handleScrollTouch(event));

        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(0, 0, 0, dp(120));
        scroll.addView(root, new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        ));

        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(0, 0, 0, dp(12));
        root.addView(content);

        body.addView(scroll, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
        ));

        refreshIndicator = new ProgressBar(this, null, android.R.attr.progressBarStyleSmall);
        refreshIndicator.setIndeterminate(true);
        refreshIndicator.setAlpha(0.0f);
        refreshIndicator.setVisibility(View.GONE);
        FrameLayout.LayoutParams refreshParams = new FrameLayout.LayoutParams(dp(36), dp(36));
        refreshParams.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        refreshParams.topMargin = dp(6);
        body.addView(refreshIndicator, refreshParams);

        shell.addView(body, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1
        ));

        LinearLayout bottomNav = hbox();
        bottomNav.setGravity(Gravity.CENTER_VERTICAL);
        bottomNav.setPadding(0, dp(8), 0, dp(10));
        startTabButton = smallButton("Start", GREEN);
        bottomNav.addView(startTabButton);

        tabScroll = new HorizontalScrollView(this);
        tabScroll.setHorizontalScrollBarEnabled(false);
        tabs = new LinearLayout(this);
        tabs.setOrientation(LinearLayout.HORIZONTAL);
        tabScroll.addView(tabs);
        bottomNav.addView(tabScroll, new LinearLayout.LayoutParams(
                0,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                1
        ));
        shell.addView(bottomNav);

        return shell;
    }

    private String screenFromIntent(Intent intent) {
        if (intent == null || Intent.ACTION_MAIN.equals(intent.getAction())) {
            return "home";
        }
        String screen = ACTION_OPEN_SCREEN.equals(intent.getAction())
                ? intent.getStringExtra(EXTRA_OPEN_SCREEN)
                : null;
        return screenIndex(screen) >= 0 ? screen : "home";
    }

    private void showScreen(String screen) {
        showScreen(screen, true);
    }

    private void showScreen(String screen, boolean scrollTop) {
        currentScreen = screen;
        selectedAttachment = null;
        if (scroll != null) {
            scroll.animate().cancel();
            scroll.setAlpha(1.0f);
            scroll.setTranslationX(0.0f);
            scroll.setTranslationY(0.0f);
            scroll.setScaleX(1.0f);
            scroll.setScaleY(1.0f);
        }
        if (content != null) {
            content.animate().cancel();
            content.setAlpha(1.0f);
            content.setTranslationX(0.0f);
            content.removeAllViews();
        }
        buildTabs();
        renderCurrentScreen();
        finishScreenRender(scrollTop);
    }

    private void renderCurrentScreen() {
        if ("home".equals(currentScreen)) {
            buildHome();
        } else if ("add".equals(currentScreen)) {
            buildAddTransaction();
        } else if ("transactions".equals(currentScreen)) {
            buildTransactions();
        } else if ("goals".equals(currentScreen)) {
            buildGoals();
        } else if ("debts".equals(currentScreen)) {
            buildDebts();
        } else if ("bills".equals(currentScreen)) {
            buildBills();
        } else if ("shopping".equals(currentScreen)) {
            buildShopping();
        } else {
            buildSettings();
        }
    }

    private void finishScreenRender(boolean scrollTop) {
        String targetTag = pendingScrollTag;
        pendingScrollTag = null;
        if (targetTag != null) {
            scroll.post(() -> scrollToTaggedView(targetTag));
        } else if (scrollTop) {
            scroll.post(() -> scroll.smoothScrollTo(0, 0));
        }
    }

    private void buildTabs() {
        configureTab(startTabButton, "Start", "home", GREEN);
        tabs.removeAllViews();
        addTab("+", "add", RED);
        addTab("Transakcje", "transactions", BLUE);
        addTab("Cele", "goals", PURPLE);
        addTab("Długi", "debts", ORANGE);
        addTab("Rachunki", "bills", RED);
        addTab("Zakupy", "shopping", GREEN);
        addTab("Ustawienia", "settings", MUTED);
        tabs.post(this::scrollActiveTabIntoView);
    }

    private void addTab(String label, String screen, int color) {
        Button btn = smallButton(label, color);
        configureTab(btn, label, screen, color);
        btn.setTag("tab:" + screen);
        tabs.addView(btn);
    }

    private void configureTab(Button btn, String label, String screen, int color) {
        if (btn == null) {
            return;
        }
        btn.setText(label);
        btn.setTextColor(screen.equals(currentScreen) ? WHITE : color);
        btn.setBackground(screen.equals(currentScreen) ? fill(color, dp(6)) : outline(color));
        btn.setOnClickListener(v -> switchScreen(screen));
    }

    private void switchScreen(String screen) {
        if (screen == null || screen.equals(currentScreen)) {
            showScreen(currentScreen);
            return;
        }
        int direction = screenIndex(screen) >= currentScreenIndex() ? 1 : -1;
        showScreenWithSlide(screen, direction);
    }

    private void scrollActiveTabIntoView() {
        if (tabScroll == null || tabs == null) {
            return;
        }
        if ("home".equals(currentScreen)) {
            tabScroll.smoothScrollTo(0, 0);
            return;
        }
        View active = tabs.findViewWithTag("tab:" + currentScreen);
        if (active == null) {
            return;
        }
        int target = Math.max(0, active.getLeft() - dp(16));
        tabScroll.smoothScrollTo(target, 0);
    }

    private void installKeyboardVisibilityWatcher() {
        final View decor = getWindow().getDecorView();
        decor.getViewTreeObserver().addOnGlobalLayoutListener(() -> {
            Rect visible = new Rect();
            decor.getWindowVisibleDisplayFrame(visible);
            int hidden = decor.getRootView().getHeight() - visible.bottom;
            View focused = getCurrentFocus();
            if (hidden > dp(120) && focused instanceof EditText) {
                ensureFieldVisible(focused);
            }
        });
    }

    private void scrollToTaggedView(String tag) {
        if (scroll == null || content == null || tag == null) {
            return;
        }
        View target = content.findViewWithTag(tag);
        if (target == null) {
            return;
        }
        int[] scrollLoc = new int[2];
        int[] targetLoc = new int[2];
        scroll.getLocationOnScreen(scrollLoc);
        target.getLocationOnScreen(targetLoc);
        int delta = targetLoc[1] - scrollLoc[1] - dp(12);
        scroll.smoothScrollBy(0, delta);
    }

    private void navigateBySwipe(int delta) {
        int idx = 0;
        for (int i = 0; i < SCREEN_ORDER.length; i++) {
            if (SCREEN_ORDER[i].equals(currentScreen)) {
                idx = i;
                break;
            }
        }
        int next = Math.max(0, Math.min(SCREEN_ORDER.length - 1, idx + delta));
        if (next != idx) {
            showScreenWithSlide(SCREEN_ORDER[next], delta);
        }
    }

    private boolean handleScrollTouch(MotionEvent event) {
        if (content == null || root == null || screenTransitionRunning) {
            return false;
        }

        int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            touchDownX = event.getX();
            touchDownY = event.getY();
            touchMode = 0;
            touchAllowsPullRefresh = canStartPullRefresh(event);
            content.animate().cancel();
            root.animate().cancel();
            if (refreshIndicator != null) {
                refreshIndicator.animate().cancel();
            }
            return false;
        }

        float dx = event.getX() - touchDownX;
        float dy = event.getY() - touchDownY;
        float absX = Math.abs(dx);
        float absY = Math.abs(dy);
        int slop = Math.max(ViewConfiguration.get(this).getScaledTouchSlop(), dp(10));

        if (action == MotionEvent.ACTION_MOVE) {
            if (touchMode == 0) {
                if (absX > Math.max(dp(22), slop * 1.35f) && absX > absY * 1.15f) {
                    touchMode = 1;
                    scroll.requestDisallowInterceptTouchEvent(true);
                } else if (touchAllowsPullRefresh
                        && dy > Math.max(dp(54), slop * 4)
                        && absY > absX * 1.65f
                        && scroll.getScrollY() == 0) {
                    touchMode = 2;
                    scroll.requestDisallowInterceptTouchEvent(true);
                }
            }

            if (touchMode == 1) {
                updateHorizontalDrag(dx);
                return true;
            }
            if (touchMode == 2) {
                updateRefreshPull(Math.max(0, dy));
                return true;
            }
            return false;
        }

        if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
            if (touchMode == 1) {
                finishHorizontalDrag(dx);
                touchMode = 0;
                scroll.requestDisallowInterceptTouchEvent(false);
                return true;
            }
            if (touchMode == 2) {
                finishRefreshPull(Math.max(0, dy));
                touchMode = 0;
                scroll.requestDisallowInterceptTouchEvent(false);
                return true;
            }
            touchMode = 0;
        }
        return false;
    }

    private boolean canStartPullRefresh(MotionEvent event) {
        if (scroll == null || scroll.getScrollY() != 0) {
            return false;
        }
        if ("transactions".equals(currentScreen) && isTouchInsideView(transactionListContainer, event)) {
            return false;
        }
        return event.getY() <= Math.max(dp(180), scroll.getHeight() * 0.32f);
    }

    private void updateHorizontalDrag(float dx) {
        int idx = currentScreenIndex();
        boolean atStart = idx == 0 && dx > 0;
        boolean atEnd = idx == SCREEN_ORDER.length - 1 && dx < 0;
        float width = Math.max(1.0f, scroll == null ? 1.0f : scroll.getWidth());
        float maxDrag = (atStart || atEnd) ? dp(62) : width * 0.42f;
        float resistance = (atStart || atEnd) ? 0.30f : 0.78f;
        float drag = Math.min(Math.abs(dx) * resistance, maxDrag);
        View page = scroll != null ? scroll : content;
        page.setTranslationX(Math.copySign(drag, dx));
        page.setAlpha(1.0f - Math.min(0.16f, drag / width * 0.55f));
        float scale = 1.0f - Math.min(0.025f, drag / width * 0.05f);
        page.setScaleX(scale);
        page.setScaleY(scale);
    }

    private void finishHorizontalDrag(float dx) {
        int width = Math.max(1, content.getWidth());
        int direction = dx < 0 ? 1 : -1;
        int idx = currentScreenIndex();
        int next = Math.max(0, Math.min(SCREEN_ORDER.length - 1, idx + direction));
        float threshold = Math.min(dp(82), Math.max(dp(52), width * 0.12f));
        if (next != idx && Math.abs(dx) >= threshold) {
            showScreenWithSlide(SCREEN_ORDER[next], direction);
        } else {
            View page = scroll != null ? scroll : content;
            page.animate()
                    .translationX(0)
                    .alpha(1.0f)
                    .scaleX(1.0f)
                    .scaleY(1.0f)
                    .setDuration(190)
                    .setInterpolator(new DecelerateInterpolator(1.8f))
                    .start();
        }
    }

    private int currentScreenIndex() {
        return screenIndex(currentScreen);
    }

    private int screenIndex(String screen) {
        for (int i = 0; i < SCREEN_ORDER.length; i++) {
            if (SCREEN_ORDER[i].equals(screen)) {
                return i;
            }
        }
        return 0;
    }

    private void showScreenWithSlide(String screen, int direction) {
        if (screenTransitionRunning || content == null || scroll == null || body == null) {
            return;
        }
        if (screen == null || screen.equals(currentScreen)) {
            showScreen(currentScreen);
            return;
        }
        int width = Math.max(1, body.getWidth());
        if (width <= 0) {
            showScreen(screen);
            return;
        }
        screenTransitionRunning = true;
        ScrollView oldScroll = scroll;
        LinearLayout oldRoot = root;
        LinearLayout oldContent = content;

        ScrollView nextScroll = new ScrollView(this);
        nextScroll.setFillViewport(true);
        nextScroll.setSmoothScrollingEnabled(true);
        nextScroll.setFocusable(true);
        nextScroll.setFocusableInTouchMode(true);
        nextScroll.setClipToPadding(false);
        nextScroll.setBackgroundColor(SURFACE);
        nextScroll.setOnTouchListener((v, event) -> handleScrollTouch(event));

        LinearLayout nextRoot = new LinearLayout(this);
        nextRoot.setOrientation(LinearLayout.VERTICAL);
        nextRoot.setPadding(0, 0, 0, dp(120));
        nextScroll.addView(nextRoot, new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        ));

        LinearLayout nextContent = new LinearLayout(this);
        nextContent.setOrientation(LinearLayout.VERTICAL);
        nextContent.setPadding(0, 0, 0, dp(12));
        nextRoot.addView(nextContent);

        int insertIndex = refreshIndicator == null ? body.getChildCount() : body.indexOfChild(refreshIndicator);
        if (insertIndex < 0) {
            insertIndex = body.getChildCount();
        }
        body.addView(nextScroll, insertIndex, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
        ));

        scroll = nextScroll;
        root = nextRoot;
        content = nextContent;
        currentScreen = screen;
        selectedAttachment = null;
        buildTabs();
        renderCurrentScreen();

        String targetTag = pendingScrollTag;
        pendingScrollTag = null;
        nextScroll.scrollTo(0, 0);

        float incomingOffset = direction * width * 0.86f;
        nextScroll.setTranslationX(incomingOffset);
        nextScroll.setAlpha(0.72f);
        nextScroll.setScaleX(0.975f);
        nextScroll.setScaleY(0.975f);

        float outgoingOffset = -direction * width * 0.28f;
        DecelerateInterpolator incoming = new DecelerateInterpolator(1.9f);
        DecelerateInterpolator outgoing = new DecelerateInterpolator(1.55f);

        oldScroll.animate()
                .translationX(outgoingOffset)
                .alpha(0.0f)
                .scaleX(0.955f)
                .scaleY(0.955f)
                .setDuration(245)
                .setInterpolator(outgoing)
                .start();

        nextScroll.animate()
                .translationX(0)
                .alpha(1.0f)
                .scaleX(1.0f)
                .scaleY(1.0f)
                .setDuration(330)
                .setInterpolator(incoming)
                .withEndAction(() -> {
                    body.removeView(oldScroll);
                    oldScroll.animate().cancel();
                    oldScroll.setAlpha(1.0f);
                    oldScroll.setTranslationX(0.0f);
                    oldScroll.setScaleX(1.0f);
                    oldScroll.setScaleY(1.0f);
                    screenTransitionRunning = false;
                    if (targetTag != null) {
                        nextScroll.post(() -> scrollToTaggedView(targetTag));
                    }
                })
                .start();
    }

    private void refreshCurrentScreenBySwipe() {
        if (refreshRunning || screenTransitionRunning) {
            return;
        }
        refreshRunning = true;
        showScreen(currentScreen);
        toast("Wszystko aktualne");
        resetRefreshPull();
        refreshRunning = false;
    }

    private void updateRefreshPull(float dy) {
        float pull = Math.min(Math.max(0.0f, dy - dp(28)) * 0.36f, dp(88));
        root.setTranslationY(pull);
        if (refreshIndicator != null) {
            refreshIndicator.setVisibility(View.VISIBLE);
            refreshIndicator.setAlpha(Math.min(1.0f, pull / Math.max(1, dp(58))));
        }
    }

    private void finishRefreshPull(float dy) {
        if (dy >= dp(156)) {
            refreshCurrentScreenBySwipe();
        } else {
            resetRefreshPull();
        }
    }

    private void resetRefreshPull() {
        root.animate().translationY(0).setDuration(120).start();
        if (refreshIndicator != null) {
            refreshIndicator.animate()
                    .alpha(0.0f)
                    .setDuration(120)
                    .withEndAction(() -> refreshIndicator.setVisibility(View.GONE))
                    .start();
        }
    }

    private void confirmSync() {
        new AlertDialog.Builder(this)
                .setTitle("SYNC")
                .setMessage("czy chcesz synchronizować?")
                .setPositiveButton("Tak", (dialog, which) -> {
                    String url = prefs().getString("sync_url", "");
                    if (url == null || url.trim().isEmpty()) {
                        toast("Ustaw adres PC w Ustawieniach");
                        showScreen("settings");
                        return;
                    }
                    syncWithPc(url);
                })
                .setNegativeButton("Nie", null)
                .show();
    }

    private void buildHome() {
        LinearLayout month = hbox();
        month.setGravity(Gravity.CENTER_VERTICAL);
        Button prevButton = smallButton("<", MUTED);
        Button nextButton = smallButton(">", MUTED);
        TextView title = text(monthTitle(), 20, TEXT, true);
        title.setGravity(Gravity.CENTER);
        prevButton.setOnClickListener(v -> {
            changeMonth(-1);
            showScreen("home");
        });
        nextButton.setOnClickListener(v -> {
            changeMonth(1);
            showScreen("home");
        });
        month.addView(prevButton);
        month.addView(title, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        month.addView(nextButton);
        content.addView(month);

        List<Tx> all = db.getTransactions(null, null);
        String monthPrefix = monthPrefix();
        double income = 0.0;
        double expenses = 0.0;
        double savings = 0.0;
        double debtorReturns = 0.0;
        Map<String, Double> expenseByCat = new LinkedHashMap<>();
        Map<String, List<Tx>> expenseRowsByCat = new LinkedHashMap<>();
        Map<String, Double> debtorReturnsByName = new LinkedHashMap<>();
        Map<String, List<Tx>> debtorReturnRows = new LinkedHashMap<>();
        Map<String, Double> liabilityPaymentsByName = new LinkedHashMap<>();
        Map<String, List<Tx>> liabilityPaymentRows = new LinkedHashMap<>();

        for (Tx tx : all) {
            if (!tx.date.startsWith(monthPrefix)) {
                continue;
            }
            if ("income".equals(tx.type)) {
                income += tx.amount;
            } else if ("debtor_repayment".equals(tx.type)) {
                debtorReturns += tx.amount;
                addToMap(debtorReturnsByName, tx.subcategory, tx.amount);
                addToListMap(debtorReturnRows, tx.subcategory, tx);
            } else if ("expense".equals(tx.type)) {
                expenses += tx.amount;
                addToMap(expenseByCat, tx.category, tx.amount);
                addToListMap(expenseRowsByCat, tx.category, tx);
            } else if ("liability_repayment".equals(tx.type)) {
                String key = "Spłata: " + tx.subcategory;
                expenses += tx.amount;
                addToMap(expenseByCat, key, tx.amount);
                addToListMap(expenseRowsByCat, key, tx);
                addToMap(liabilityPaymentsByName, tx.subcategory, tx.amount);
                addToListMap(liabilityPaymentRows, tx.subcategory, tx);
            } else if ("savings".equals(tx.type) || "savings_migration".equals(tx.type)) {
                savings += tx.amount;
            } else if ("goal_deposit".equals(tx.type)) {
                expenses += tx.amount;
            }
        }

        double totalBalance = db.totalBalanceAllAccounts();
        LinearLayout grid = new LinearLayout(this);
        grid.setOrientation(LinearLayout.VERTICAL);
        content.addView(grid);
        grid.addView(metricCard("Saldo łączne", money(totalBalance), totalBalance >= 0 ? GREEN : RED));
        grid.addView(metricCard("Wpływy", money(income + debtorReturns), GREEN));
        grid.addView(metricCard("Wydatki", money(expenses), RED));
        grid.addView(metricCard("Oszczędności", money(db.totalCashSavings()), BLUE));

        content.addView(sectionTitle("Konta"));
        LinearLayout accountsBox = card();
        double prevTotal = 0.0;
        String firstDayOfMonth = monthPrefix() + "-01";
        for (Account acc : db.getAccounts()) {
            TextView row = text(acc.name + ": " + money(db.accountBalance(acc.id)), 15, parseColor(acc.color, TEXT), true);
            row.setPadding(0, dp(4), 0, dp(4));
            accountsBox.addView(row);
            prevTotal += db.accountBalanceBefore(acc.id, firstDayOfMonth);
        }
        TextView prev = text("Z poprzedniego miesiąca: " + money(prevTotal), 13, MUTED, true);
        prev.setPadding(0, dp(8), 0, dp(2));
        accountsBox.addView(prev);
        content.addView(accountsBox);

        buildWeeklySummary();
        buildBillAlerts();
        buildHomeQuickActions();

        content.addView(sectionTitle("Największe wydatki"));
        LinearLayout topBox = card();
        List<Map.Entry<String, Double>> expensesSorted = new ArrayList<>(expenseByCat.entrySet());
        expensesSorted.sort((a, b) -> Double.compare(b.getValue(), a.getValue()));
        if (expensesSorted.isEmpty()) {
            topBox.addView(text("Brak wydatków w tym miesiącu.", 14, MUTED, false));
        } else {
            int max = Math.min(6, expensesSorted.size());
            for (int i = 0; i < max; i++) {
                Map.Entry<String, Double> e = expensesSorted.get(i);
                addExpandableSummaryRow(topBox, "expense:" + e.getKey(), e.getKey(), e.getValue(),
                        expenses <= 0 ? 1 : expenses, RED, expenseRowsByCat.get(e.getKey()));
            }
        }
        content.addView(topBox);

        buildCompactGoals();
        buildCompactDebts();
    }

    private void buildHomeQuickActions() {
        LinearLayout quick = hbox();
        quick.addView(actionButton("Dodaj wpis", RED, v -> showScreen("add")),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        quick.addView(actionButton("Transakcje", BLUE, v -> showScreen("transactions")),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        content.addView(quick);
    }

    private void buildWeeklySummary() {
        if (!db.isWeeklyEnabled()) {
            return;
        }
        String start = weekStart(today());
        String end = addDays(start, 6);
        double limit = db.weeklyAmount();
        Map<String, Double> cats = db.weeklySpendingByCategory(start, end, db.weeklyCategories());
        double spent = 0.0;
        for (double value : cats.values()) {
            spent += value;
        }
        double remaining = limit - spent;

        content.addView(sectionTitle("Limit tygodnia"));
        LinearLayout box = card();
        box.addView(twoCol(start + " - " + end, "Limit: " + money(limit), TEXT, BLUE));
        box.addView(progressLine(spent, limit <= 0 ? 1 : limit, remaining < 0 ? RED : GREEN));
        box.addView(text("Wydano: " + money(spent), 13, RED, true));
        box.addView(text(remaining < 0 ? "Przekroczono: " + money(Math.abs(remaining)) : "Pozostało: " + money(remaining),
                15, remaining < 0 ? RED : GREEN, true));

        List<Map.Entry<String, Double>> sorted = new ArrayList<>(cats.entrySet());
        sorted.sort((a, b) -> Double.compare(b.getValue(), a.getValue()));
        int max = Math.min(5, sorted.size());
        for (int i = 0; i < max; i++) {
            Map.Entry<String, Double> e = sorted.get(i);
            box.addView(twoCol(e.getKey(), money(e.getValue()), MUTED, RED));
        }
        if (sorted.isEmpty()) {
            box.addView(text("Brak wydatków w tym tygodniu.", 13, MUTED, false));
        }
        content.addView(box);
    }

    private void buildExpandableTransactionGroups(String title, String prefix, Map<String, Double> totals,
                                                  Map<String, List<Tx>> rowsByKey, int color) {
        if (totals.isEmpty()) {
            return;
        }
        content.addView(sectionTitle(title));
        LinearLayout box = card();
        List<Map.Entry<String, Double>> sorted = new ArrayList<>(totals.entrySet());
        sorted.sort((a, b) -> Double.compare(b.getValue(), a.getValue()));
        double total = 0.0;
        for (double value : totals.values()) {
            total += value;
        }
        for (Map.Entry<String, Double> e : sorted) {
            addExpandableSummaryRow(box, prefix + e.getKey(), safeLabel(e.getKey()), e.getValue(),
                    total <= 0 ? 1 : total, color, rowsByKey.get(e.getKey()));
        }
        content.addView(box);
    }

    private void addExpandableSummaryRow(LinearLayout box, String groupId, String label, double value,
                                         double total, int color, List<Tx> rows) {
        String marker = expandedHomeGroups.contains(groupId) ? "▲ " : "▼ ";
        TextView row = twoCol(marker + label, money(value), TEXT, color);
        row.setTag(groupId);
        row.setClickable(true);
        row.setOnClickListener(v -> {
            if (expandedHomeGroups.contains(groupId)) {
                expandedHomeGroups.remove(groupId);
            } else {
                expandedHomeGroups.add(groupId);
            }
            pendingScrollTag = groupId;
            showScreen("home", false);
        });
        box.addView(row);
        box.addView(progressLine(value, total, color));
        if (expandedHomeGroups.contains(groupId)) {
            addMiniTransactionRows(box, rows);
        }
    }

    private void addMiniTransactionRows(LinearLayout box, List<Tx> rows) {
        if (rows == null || rows.isEmpty()) {
            box.addView(text("Brak transakcji.", 13, MUTED, false));
            return;
        }
        rows.sort((a, b) -> compareTransactionsBySyncOrder(b, a));
        for (Tx tx : rows) {
            String desc = tx.subcategory == null || tx.subcategory.trim().isEmpty() ? tx.category : tx.subcategory;
            TextView line = text("  " + tx.date + " | " + desc + " | " + money(tx.amount), 13, MUTED, false);
            line.setPadding(0, dp(2), 0, dp(2));
            box.addView(line);
        }
    }

    private void buildBillAlerts() {
        List<Bill> bills = db.getPendingBills();
        List<String> alerts = new ArrayList<>();
        String today = today();
        Calendar base = calendarFrom(today);

        for (Bill bill : bills) {
            long days = daysBetween(base, calendarFrom(bill.dueDate));
            if (days < 0) {
                alerts.add("Po terminie " + Math.abs(days) + " dni: " + bill.description + " (" + money(bill.amount) + ")");
            } else if (days == 0) {
                alerts.add("Dzisiaj: " + bill.description + " (" + money(bill.amount) + ")");
            } else if (days <= 7) {
                alerts.add("Za " + days + " dni: " + bill.description + " (" + money(bill.amount) + ")");
            }
        }

        if (alerts.isEmpty()) {
            return;
        }

        content.addView(sectionTitle("Rachunki na radarze"));
        LinearLayout box = card();
        for (String alert : alerts) {
            box.addView(text(alert, 14, RED, true));
        }
        content.addView(box);
    }

    private void buildCompactGoals() {
        List<Goal> goals = db.getGoals();
        if (goals.isEmpty()) {
            return;
        }
        content.addView(sectionTitle("Cele"));
        LinearLayout box = card();
        for (Goal goal : goals) {
            double collected = db.goalTotal(goal);
            box.addView(twoCol(goal.name, money(collected) + " / " + money(goal.target), TEXT, BLUE));
            box.addView(progressLine(collected, goal.target, BLUE));
        }
        content.addView(box);
    }

    private void buildCompactDebts() {
        List<Debt> liabilities = db.getDebts("liabilities");
        List<Debt> debtors = db.getDebts("debtors");
        content.addView(sectionTitle("Długi i dłużnicy"));
        LinearLayout box = card();
        int activeRows = 0;
        for (Debt d : liabilities) {
            double rem = d.total - d.paid;
            if (rem > 0.01) {
                box.addView(twoCol("Do spłaty: " + d.name, money(rem), TEXT, ORANGE));
                box.addView(progressLine(d.paid, d.total, ORANGE));
                activeRows++;
            }
        }
        for (Debt d : debtors) {
            double rem = d.total - d.paid;
            if (rem > 0.01) {
                box.addView(twoCol("Ma oddać: " + d.name, money(rem), TEXT, BLUE));
                box.addView(progressLine(d.paid, d.total, BLUE));
                activeRows++;
            }
        }
        if (activeRows == 0) {
            box.addView(text("Brak aktywnych długów i dłużników.", 14, MUTED, false));
        }
        content.addView(box);

        LinearLayout actions = hbox();
        actions.addView(actionButton("Dodaj zobowiązanie", ORANGE, v -> showDebtForm("liabilities")),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        actions.addView(actionButton("Dodaj dłużnika", BLUE, v -> showDebtForm("debtors")),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        content.addView(actions);
    }

    private void showDebtForm(String table) {
        pendingScrollTag = debtFormTag(table);
        showScreen("debts");
    }

    private String debtFormTag(String table) {
        return "debt-form:" + table;
    }

    private void buildAddTransaction() {
        content.addView(sectionTitle("Nowy wpis"));
        LinearLayout form = card();

        txTypeSpinner = spinner(list(
                "Wydatek", "Przychód", "Oszczędności +", "Oszczędności -",
                "Wpłata na cel", "Wypłata z celu", "Spłata długu", "Zwrot od dłużnika"
        ));
        form.addView(label("Typ"));
        form.addView(txTypeSpinner);

        txDateInput = input("RRRR-MM-DD", today());
        attachDatePicker(txDateInput);
        form.addView(label("Data"));
        form.addView(txDateInput);

        txAccountSpinner = accountSpinner();
        form.addView(label("Konto"));
        form.addView(txAccountSpinner);

        txPickerSpinner = spinner(new ArrayList<>());
        form.addView(label("Kategoria / cel / dług"));
        LinearLayout pickerRow = hbox();
        pickerRow.addView(txPickerSpinner, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        txAddPickerValueButton = smallButton("+", BLUE);
        txAddPickerValueButton.setMinWidth(dp(52));
        txAddPickerValueButton.setContentDescription("Dodaj kategorię");
        txAddPickerValueButton.setOnClickListener(v -> showAddPickerValueDialog());
        pickerRow.addView(txAddPickerValueButton);
        form.addView(pickerRow);

        txCustomInput = input("", "");
        txCustomInput.setVisibility(View.GONE);

        txSubInput = input("Opis, sklep albo źródło", "");
        txSubInput.setSingleLine(true);
        form.addView(label("Opis krótki"));
        form.addView(txSubInput);

        txDetailsInput = expenseDetailsInput("Szczegóły", "");
        txDetailsInput.setMinLines(3);
        txDetailsInput.setGravity(Gravity.TOP | Gravity.START);
        form.addView(label("Szczegóły"));
        form.addView(txDetailsInput);

        txAmountInput = input("0.00", "");
        configureAmountInput(txAmountInput, false);
        form.addView(label("Kwota"));
        form.addView(txAmountInput);

        txExcludeWeekly = new CheckBox(this);
        txExcludeWeekly.setText("Pomiń w limicie tygodniowym");
        txExcludeWeekly.setTextColor(TEXT);
        form.addView(txExcludeWeekly);

        txAttachmentText = text("Załącznik: brak", 13, MUTED, false);
        form.addView(txAttachmentText);
        LinearLayout attButtons = hbox();
        attButtons.addView(actionButton("Załącz plik", BLUE, v -> chooseAttachment()),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        attButtons.addView(actionButton("Usuń", MUTED, v -> {
            selectedAttachment = null;
            updateAttachmentLabel();
        }), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        form.addView(attButtons);

        Button save = actionButton("Zapisz", RED, v -> saveTransactionFromForm());
        form.addView(save);
        content.addView(form);

        txTypeSpinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                refreshTransactionPicker();
            }
            @Override public void onNothingSelected(AdapterView<?> parent) {}
        });
        refreshTransactionPicker();
    }

    private void refreshTransactionPicker() {
        if (txTypeSpinner == null) {
            return;
        }
        String type = txTypeSpinner.getSelectedItem().toString();
        List<String> values;
        txSubInput.setVisibility(View.VISIBLE);
        txExcludeWeekly.setVisibility("Wydatek".equals(type) ? View.VISIBLE : View.GONE);
        if (txAddPickerValueButton != null) {
            txAddPickerValueButton.setVisibility(View.GONE);
        }

        if ("Przychód".equals(type)) {
            values = db.getPeople();
            txSubInput.setHint("Źródło, np. Wypłata");
            refreshAutocomplete(txSubInput);
            if (txAddPickerValueButton != null) {
                txAddPickerValueButton.setVisibility(View.VISIBLE);
                txAddPickerValueButton.setContentDescription("Dodaj źródło");
            }
        } else if ("Wydatek".equals(type)) {
            values = db.getCategories();
            txSubInput.setHint("Sklep / opis");
            refreshAutocomplete(txSubInput);
            if (txAddPickerValueButton != null) {
                txAddPickerValueButton.setVisibility(View.VISIBLE);
                txAddPickerValueButton.setContentDescription("Dodaj kategorię");
            }
        } else if (type.contains("cel")) {
            values = goalNames();
            txSubInput.setVisibility(View.GONE);
        } else if ("Spłata długu".equals(type)) {
            values = debtNames(db.getDebts("liabilities"), true);
            txSubInput.setVisibility(View.GONE);
        } else if ("Zwrot od dłużnika".equals(type)) {
            values = debtNames(db.getDebts("debtors"), true);
            txSubInput.setVisibility(View.GONE);
        } else {
            values = list("Oszczędności");
            txSubInput.setHint("Opcjonalnie: cel oszczędności");
            refreshAutocomplete(txSubInput);
        }
        setSpinnerValues(txPickerSpinner, values);
    }

    private void showAddPickerValueDialog() {
        if (txTypeSpinner == null || txPickerSpinner == null) {
            return;
        }
        String type = txTypeSpinner.getSelectedItem() == null ? "" : txTypeSpinner.getSelectedItem().toString();
        boolean income = "Przychód".equals(type);
        boolean expense = "Wydatek".equals(type);
        if (!income && !expense) {
            return;
        }

        LinearLayout form = vbox();
        form.setPadding(dp(16), dp(8), dp(16), 0);
        EditText name = input(income ? "Nazwa źródła" : "Nazwa kategorii", "");
        name.setSingleLine(true);
        form.addView(name);

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle(income ? "Nowe źródło" : "Nowa kategoria")
                .setView(form)
                .setPositiveButton("Dodaj", null)
                .setNegativeButton("Anuluj", null)
                .create();
        dialog.setOnShowListener(d -> {
            dialog.getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
                String value = name.getText().toString().trim();
                if (value.isEmpty()) {
                    toast("Wpisz nazwę");
                    return;
                }
                if (income) {
                    db.addPerson(value);
                } else {
                    db.addCategory(value);
                }
                refreshTransactionPicker();
                selectSpinnerValue(txPickerSpinner, value);
                dialog.dismiss();
            });
            name.requestFocus();
        });
        dialog.show();
    }

    private void saveTransactionFromForm() {
        String uiType = txTypeSpinner.getSelectedItem().toString();
        String date = txDateInput.getText().toString().trim();
        if (!isDate(date)) {
            toast("Data musi mieć format RRRR-MM-DD");
            return;
        }
        if (db.isMonthLocked(date.substring(0, 7))) {
            toast("Ten miesiąc jest zamknięty");
            return;
        }

        double amount = parseAmount(txAmountInput.getText().toString());
        if (amount <= 0.0) {
            toast("Wpisz poprawną kwotę");
            return;
        }

        Account account = selectedAccount(txAccountSpinner);
        Object selectedObj = txPickerSpinner.getSelectedItem();
        String selected = selectedObj == null ? "" : selectedObj.toString();
        String shortDesc = txSubInput.getText().toString().trim();
        String details = txDetailsInput.getText().toString().trim();
        byte[] attachment = selectedAttachment == null ? null : selectedAttachment.data;

        String dbType;
        String category;
        String subcategory;
        Long refId = null;
        int exclude = txExcludeWeekly.isChecked() ? 1 : 0;

        if ("Przychód".equals(uiType)) {
            dbType = "income";
            category = selected;
            subcategory = shortDesc.isEmpty() ? "Wpływ" : shortDesc;
            db.addPerson(category);
        } else if ("Wydatek".equals(uiType)) {
            dbType = "expense";
            category = selected;
            subcategory = shortDesc;
            db.addCategory(category);
        } else if ("Oszczędności +".equals(uiType) || "Oszczędności -".equals(uiType)) {
            dbType = "savings";
            category = "Oszczędności";
            subcategory = "Oszczędności";
            if ("Oszczędności -".equals(uiType)) {
                amount = -amount;
            }
        } else if ("Wpłata na cel".equals(uiType) || "Wypłata z celu".equals(uiType)) {
            Goal goal = selectedGoalByName(selected);
            if (goal == null) {
                toast("Najpierw dodaj cel");
                return;
            }
            dbType = "goal_deposit";
            category = "Cele";
            subcategory = goal.name;
            refId = goal.id;
            if ("Wypłata z celu".equals(uiType)) {
                amount = -amount;
            }
        } else if ("Spłata długu".equals(uiType)) {
            Debt debt = selectedDebtFromLabel(db.getDebts("liabilities"), selected);
            if (debt == null) {
                toast("Najpierw dodaj dług");
                return;
            }
            dbType = "liability_repayment";
            category = "Spłata Długu";
            subcategory = debt.name;
            refId = debt.id;
        } else {
            Debt debt = selectedDebtFromLabel(db.getDebts("debtors"), selected);
            if (debt == null) {
                toast("Najpierw dodaj dłużnika");
                return;
            }
            dbType = "debtor_repayment";
            category = "Zwrot od Dłużnika";
            subcategory = debt.name;
            refId = debt.id;
        }

        db.addTransaction(date, dbType, category, subcategory, amount, exclude, details, attachment, account.id, refId);
        scheduleAfterFinancialChange(dbType);
        selectedAttachment = null;
        toast("Zapisano");
        showScreen("transactions");
    }

    private void buildTransactions() {
        LinearLayout month = hbox();
        month.setGravity(Gravity.CENTER_VERTICAL);
        Button prev = smallButton("<", MUTED);
        Button next = smallButton(">", MUTED);
        TextView title = text(monthTitle(), 19, TEXT, true);
        title.setGravity(Gravity.CENTER);
        prev.setOnClickListener(v -> {
            changeMonth(-1);
            buildTransactionsRefresh();
        });
        next.setOnClickListener(v -> {
            changeMonth(1);
            buildTransactionsRefresh();
        });
        month.addView(prev);
        month.addView(title, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        month.addView(next);
        content.addView(month);

        transactionSearchInput = input(
                "Szukaj: sklep, kategoria, kwota, data",
                pendingTransactionSearch
        );
        String initialSearch = pendingTransactionSearch;
        pendingTransactionSearch = "";
        transactionSearchInput.setSingleLine(true);
        transactionSearchInput.setText(initialSearch);
        transactionSearchInput.setTextSize(16);
        transactionSearchInput.setMinHeight(dp(56));
        transactionSearchInput.setImeOptions(EditorInfo.IME_ACTION_SEARCH);
        transactionSearchInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                addTransactionList();
                return true;
            }
            return false;
        });
        transactionSearchInput.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                pendingTransactionSearch = s.toString();
                scheduleTransactionSearchRefresh();
            }
            @Override public void afterTextChanged(Editable s) {}
        });
        content.addView(transactionSearchInput);
        Button newTransaction = actionButton("Nowa transakcja", RED, v -> showScreen("add"));
        content.addView(newTransaction);
        Button cashTransfer = actionButton("Migracja kasy", BLUE, v -> showAccountTransferDialog());
        content.addView(cashTransfer);

        Button lock = actionButton(db.isMonthLocked(monthPrefix()) ? "Odblokuj miesiąc" : "Zamknij miesiąc", ORANGE, v -> {
            if (db.isMonthLocked(monthPrefix())) {
                db.unlockMonth(monthPrefix());
            } else {
                db.lockMonth(monthPrefix());
            }
            buildTransactionsRefresh();
        });
        content.addView(lock);

        transactionListContainer = vbox();
        content.addView(transactionListContainer);
        addTransactionList();
    }

    private void buildTransactionsRefresh() {
        if (transactionSearchInput != null) {
            pendingTransactionSearch = transactionSearchInput.getText().toString();
        }
        content.removeAllViews();
        buildTransactions();
    }

    private void addTransactionList() {
        String query = transactionSearchInput == null ? "" : transactionSearchInput.getText().toString().trim();
        if (transactionListContainer != null) {
            transactionListContainer.removeAllViews();
        }
        LinearLayout target = transactionListContainer == null ? content : transactionListContainer;
        List<Tx> rows;

        if (query.isEmpty()) {
            rows = db.getTransactions(monthPrefix(), "");
        } else {
            rows = db.getTransactions(null, query);
        }
        rows = visibleTransactionRows(rows);
        target.addView(sectionTitle("Lista transakcji"));

        if (rows.isEmpty()) {
            LinearLayout box = card();
            box.addView(text("Brak transakcji dla wybranego widoku.", 14, MUTED, false));
            target.addView(box);
            return;
        }

        for (Tx tx : rows) {
            addTransactionCard(target, tx);
        }
    }

    private List<Tx> visibleTransactionRows(List<Tx> rows) {
        List<Tx> visible = new ArrayList<>();
        for (Tx tx : rows) {
            if (!"savings_migration".equals(tx.type) && !"account_transfer".equals(tx.type)) {
                visible.add(tx);
            }
        }
        return visible;
    }

    private void showAccountTransferDialog() {
        List<Account> accounts = db.getAccounts();
        if (accounts.size() < 2) {
            toast("Dodaj najpierw drugie konto w ustawieniach");
            return;
        }
        LinearLayout form = vbox();
        form.setPadding(dp(16), dp(8), dp(16), 0);
        Spinner from = accountSpinner();
        Spinner to = accountSpinner();
        if (to.getCount() > 1) {
            to.setSelection(1);
        }
        EditText amount = input("Kwota", "");
        configureAmountInput(amount, false);
        EditText details = input("Szczegóły techniczne", "");
        form.addView(label("Z konta")); form.addView(from);
        form.addView(label("Na konto")); form.addView(to);
        form.addView(label("Kwota")); form.addView(amount);
        form.addView(label("Szczegóły")); form.addView(details);

        new AlertDialog.Builder(this)
                .setTitle("Migracja kasy")
                .setView(form)
                .setPositiveButton("Przenieś", (d, w) -> {
                    Account source = selectedAccount(from);
                    Account target = selectedAccount(to);
                    double value = parseAmount(amount.getText().toString());
                    if (source.id == target.id || value <= 0) {
                        toast("Wybierz dwa różne konta i kwotę");
                        return;
                    }
                    if (!db.transferAccounts(source.id, target.id, value, details.getText().toString().trim())) {
                        toast("Nie udało się przenieść środków");
                        return;
                    }
                    buildTransactionsRefresh();
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }

    private void addTransactionCard(LinearLayout parent, Tx tx) {
        LinearLayout card = card();
        card.setPadding(dp(12), dp(10), dp(12), dp(10));
        Account acc = db.accountById(tx.accountId);
        int amountColor = transactionAmountColor(tx);

        LinearLayout top = hbox();
        top.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout left = vbox();
        left.addView(text(tx.date + "  " + typeLabel(tx.type), 13, MUTED, true));
        left.addView(text(tx.category + (tx.subcategory.isEmpty() ? "" : " / " + tx.subcategory), 15, TEXT, true));
        left.addView(text((acc == null ? "Konto ?" : acc.name) + (tx.hasAttachment ? " | załącznik" : ""), 12, MUTED, false));
        top.addView(left, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        TextView amount = text(money(tx.amount), 17, amountColor, true);
        amount.setGravity(Gravity.RIGHT);
        top.addView(amount);
        card.addView(top);

        boolean expanded = expandedTransactions.contains(tx.id);
        if (expanded) {
            if (!tx.details.isEmpty()) {
                TextView details = text(tx.details, 13, TEXT, false);
                details.setPadding(0, dp(8), 0, dp(4));
                card.addView(details);
            }
            LinearLayout buttons = hbox();
            buttons.addView(actionButton("Edytuj", BLUE, v -> showEditTransactionDialog(tx)),
                    new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            buttons.addView(actionButton("Usuń", RED, v -> confirmDeleteTransaction(tx)),
                    new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            if (tx.hasAttachment) {
                buttons.addView(actionButton("Plik", GREEN, v -> openAttachment(tx)),
                        new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            }
            card.addView(buttons);
        }

        card.setOnClickListener(v -> {
            if (expandedTransactions.contains(tx.id)) {
                expandedTransactions.remove(tx.id);
            } else {
                expandedTransactions.add(tx.id);
            }
            buildTransactionsRefresh();
        });
        parent.addView(card);
    }

    private void showEditTransactionDialog(Tx tx) {
        pendingEditAttachment = null;
        pendingEditHadAttachment = tx.hasAttachment;
        LinearLayout form = vbox();
        form.setPadding(dp(16), dp(8), dp(16), 0);
        EditText date = input("Data", tx.date);
        attachDatePicker(date);
        Spinner account = accountSpinner();
        selectAccount(account, tx.accountId);
        EditText category = input("Kategoria", tx.category);
        EditText sub = input("Opis", tx.subcategory);
        EditText amount = input("Kwota", formatRaw(tx.amount));
        configureAmountInput(amount, true);
        EditText details = input("Szczegóły", tx.details);
        details.setMinLines(3);
        pendingEditAttachmentText = text("", 13, MUTED, false);
        updateEditAttachmentLabel();
        form.addView(label("Data")); form.addView(date);
        form.addView(label("Konto")); form.addView(account);
        form.addView(label("Kategoria")); form.addView(category);
        form.addView(label("Opis")); form.addView(sub);
        form.addView(label("Kwota")); form.addView(amount);
        form.addView(label("Szczegóły")); form.addView(details);
        form.addView(label("Załącznik"));
        form.addView(pendingEditAttachmentText);
        form.addView(actionButton(tx.hasAttachment ? "Zmień załącznik" : "Dodaj załącznik", GREEN, v -> chooseEditAttachment()));

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Edytuj transakcję")
                .setView(form)
                .setPositiveButton("Zapisz", (dlg, which) -> {
                    String d = date.getText().toString().trim();
                    if (!isDate(d)) {
                        toast("Niepoprawna data");
                        return;
                    }
                    double amt = parseAmount(amount.getText().toString());
                    Account acc = selectedAccount(account);
                    db.updateTransaction(tx.id, d, category.getText().toString().trim(),
                            sub.getText().toString().trim(), amt, details.getText().toString().trim(), acc.id,
                            pendingEditAttachment == null ? null : pendingEditAttachment.data);
                    pendingEditAttachment = null;
                    buildTransactionsRefresh();
                })
                .setNegativeButton("Anuluj", null)
                .create();
        dialog.setOnDismissListener(d -> {
            pendingEditAttachment = null;
            pendingEditAttachmentText = null;
            pendingEditHadAttachment = false;
        });
        dialog.show();
    }

    private void confirmDeleteTransaction(Tx tx) {
        new AlertDialog.Builder(this)
                .setTitle("Usuń transakcję")
                .setMessage(tx.date + "\n" + tx.category + " / " + tx.subcategory + "\n" + money(tx.amount))
                .setPositiveButton("Usuń", (d, w) -> {
                    db.deleteTransaction(tx.id);
                    expandedTransactions.remove(tx.id);
                    buildTransactionsRefresh();
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }

    private void buildGoals() {
        content.addView(sectionTitle("Cele i oszczędności"));
        LinearLayout add = card();
        EditText name = input("Nazwa celu", "");
        EditText target = input("Kwota celu", "");
        configureAmountInput(target, false);
        Spinner account = accountSpinner();
        add.addView(label("Nowy cel")); add.addView(name);
        add.addView(label("Kwota")); add.addView(target);
        add.addView(label("Domyślne konto")); add.addView(account);
        add.addView(actionButton("Dodaj cel", PURPLE, v -> {
            String n = name.getText().toString().trim();
            double t = parseAmount(target.getText().toString());
            if (n.isEmpty() || t <= 0) {
                toast("Podaj nazwę i kwotę celu");
                return;
            }
            if (!db.addGoal(n, t, selectedAccount(account).id)) {
                toast("Taki cel już istnieje");
                return;
            }
            showScreen("goals");
        }));
        content.addView(add);

        List<Goal> goals = db.getGoals();
        if (goals.isEmpty()) {
            content.addView(infoCard("Brak celów. Dodaj pierwszy i karm go wpłatami z ekranu +."));
        } else {
            for (Goal goal : goals) {
                addGoalCard(goal);
            }
        }

        content.addView(sectionTitle("Transfer oszczędności"));
        LinearLayout transfer = card();
        Spinner from = spinner(savingsBuckets());
        Spinner to = spinner(savingsBuckets());
        Spinner acc = accountSpinner();
        EditText amt = input("Kwota", "");
        configureAmountInput(amt, false);
        transfer.addView(label("Z")); transfer.addView(from);
        transfer.addView(label("Do")); transfer.addView(to);
        transfer.addView(label("Konto")); transfer.addView(acc);
        transfer.addView(label("Kwota")); transfer.addView(amt);
        transfer.addView(actionButton("Przenieś", BLUE, v -> {
            String s = from.getSelectedItem().toString();
            String t = to.getSelectedItem().toString();
            double a = parseAmount(amt.getText().toString());
            if (s.equals(t) || a <= 0) {
                toast("Wybierz różne miejsca i kwotę");
                return;
            }
            Account selected = selectedAccount(acc);
            db.addTransaction(today(), "savings", "Oszczędności", s, -a, 0,
                    "Transfer do: " + t, null, selected.id, null);
            db.addTransaction(today(), "savings", "Oszczędności", t, a, 0,
                    "Transfer z: " + s, null, selected.id, null);
            showScreen("goals");
        }));
        content.addView(transfer);
    }

    private void addGoalCard(Goal goal) {
        LinearLayout card = card();
        double collected = db.goalTotal(goal);
        card.addView(twoCol(goal.name, money(collected) + " / " + money(goal.target), TEXT, PURPLE));
        card.addView(progressLine(collected, goal.target, PURPLE));
        LinearLayout buttons = hbox();
        buttons.addView(actionButton("Wpłać", BLUE, v -> goalOperation(goal, true)),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        buttons.addView(actionButton("Wypłać", GREEN, v -> goalOperation(goal, false)),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        buttons.addView(actionButton("Usuń", RED, v -> confirmDeleteGoal(goal)),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        card.addView(buttons);
        content.addView(card);
    }

    private void goalOperation(Goal goal, boolean deposit) {
        amountDialog(deposit ? "Wpłata na cel" : "Wypłata z celu", goal.name, deposit ? BLUE : GREEN, (amount, details, accountId) -> {
            double signed = deposit ? amount : -amount;
            db.addTransaction(today(), "goal_deposit", "Cele", goal.name, signed, 0, details, null, accountId, goal.id);
            showScreen("goals");
        });
    }

    private void confirmDeleteGoal(Goal goal) {
        new AlertDialog.Builder(this)
                .setTitle("Usuń cel")
                .setMessage(goal.name)
                .setPositiveButton("Usuń", (d, w) -> {
                    db.deleteGoal(goal.id);
                    showScreen("goals");
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }

    private void buildDebts() {
        content.addView(sectionTitle("Moje długi"));
        buildDebtAddForm("liabilities");
        int activeLiabilities = 0;
        for (Debt debt : db.getDebts("liabilities")) {
            if (debt.remaining() > 0.01) {
                addDebtCard(debt, "liabilities");
                activeLiabilities++;
            }
        }
        if (activeLiabilities == 0) {
            content.addView(infoCard("Brak aktywnych długów."));
        }

        content.addView(sectionTitle("Dłużnicy"));
        buildDebtAddForm("debtors");
        int activeDebtors = 0;
        for (Debt debt : db.getDebts("debtors")) {
            if (debt.remaining() > 0.01) {
                addDebtCard(debt, "debtors");
                activeDebtors++;
            }
        }
        if (activeDebtors == 0) {
            content.addView(infoCard("Brak aktywnych dłużników."));
        }
    }

    private void buildDebtAddForm(String table) {
        boolean debtor = "debtors".equals(table);
        LinearLayout form = card();
        form.setTag(debtFormTag(table));
        EditText name = input(debtor ? "Kto ma oddać?" : "Komu wiszę?", "");
        EditText amount = input("Kwota", "");
        configureAmountInput(amount, false);
        EditText deadline = input("Termin RRRR-MM-DD", today());
        attachDatePicker(deadline);
        Spinner account = accountSpinner();
        form.addView(label(debtor ? "Nowy dłużnik" : "Nowe zobowiązanie"));
        form.addView(name);
        form.addView(label(debtor ? "Płacę z konta" : "Konto"));
        form.addView(account);
        form.addView(label("Kwota")); form.addView(amount);
        form.addView(label("Termin")); form.addView(deadline);
        form.addView(actionButton(debtor ? "Dodaj dłużnika" : "Dodaj dług", debtor ? BLUE : ORANGE, v -> {
            String n = name.getText().toString().trim();
            double a = parseAmount(amount.getText().toString());
            String d = deadline.getText().toString().trim();
            if (n.isEmpty() || a <= 0 || !isDate(d)) {
                toast("Uzupełnij nazwę, kwotę i datę");
                return;
            }
            long id = db.addDebt(table, n, a, d);
            if (debtor) {
                Account acc = selectedAccount(account);
                db.addTransaction(today(), "expense", "Pożyczki", n, a, 0, "", null, acc.id, id);
                scheduleAfterFinancialChange("expense");
            } else {
                BudgetReminderReceiver.refreshTasks(this);
            }
            showScreen("debts");
        }));
        content.addView(form);
    }

    private void addDebtCard(Debt debt, String table) {
        boolean debtor = "debtors".equals(table);
        double remaining = debt.remaining();
        LinearLayout card = card();
        card.addView(twoCol(debt.name, money(remaining) + " z " + money(debt.total), TEXT, remaining > 0 ? RED : GREEN));
        card.addView(text("Termin: " + debt.deadline + " | spłacono: " + money(debt.paid), 12, MUTED, false));
        card.addView(progressLine(debt.paid, debt.total, debtor ? BLUE : ORANGE));
        LinearLayout buttons = hbox();
        buttons.addView(actionButton(debtor ? "Zwrot" : "Spłać", debtor ? BLUE : ORANGE, v -> {
            amountDialog(debtor ? "Zwrot od dłużnika" : "Spłata długu", debt.name, debtor ? BLUE : ORANGE, (amount, details, accountId) -> {
                String type = debtor ? "debtor_repayment" : "liability_repayment";
                db.addTransaction(today(), type,
                        debtor ? "Zwrot od Dłużnika" : "Spłata Długu",
                        debt.name, amount, 0, details, null, accountId, debt.id);
                scheduleAfterFinancialChange(type);
                showScreen("debts");
            });
        }), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        buttons.addView(actionButton("Historia", BLUE, v -> {
            expandedTransactions.clear();
            pendingTransactionSearch = debt.name;
            showScreen("transactions");
        }), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        buttons.addView(actionButton("Usuń", RED, v -> confirmDeleteDebt(debt, table)),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        card.addView(buttons);
        content.addView(card);
    }

    private void confirmDeleteDebt(Debt debt, String table) {
        new AlertDialog.Builder(this)
                .setTitle("Usuń")
                .setMessage(debt.name + "\nHistoria transakcji zostanie.")
                .setPositiveButton("Usuń", (d, w) -> {
                    db.deleteDebt(table, debt.id);
                    BudgetReminderReceiver.refreshTasks(this);
                    showScreen("debts");
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }

    private void buildShopping() {
        content.addView(sectionTitle("Lista zakupów"));
        List<ShoppingListData> lists = db.getShoppingLists();
        if (selectedShoppingListId < 0 && !lists.isEmpty()) {
            for (ShoppingListData list : lists) {
                if ("open".equals(list.status)) {
                    selectedShoppingListId = list.id;
                    break;
                }
            }
            if (selectedShoppingListId < 0) {
                selectedShoppingListId = lists.get(0).id;
            }
        }

        LinearLayout create = card();
        EditText name = input("Nazwa listy", defaultShoppingListName());
        create.addView(name);
        create.addView(actionButton("Nowa lista", GREEN, v -> {
            String n = name.getText().toString().trim();
            if (n.isEmpty()) {
                toast("Podaj nazwę listy");
                return;
            }
            selectedShoppingListId = db.createShoppingList(n);
            showScreen("shopping");
        }));
        content.addView(create);

        if (!lists.isEmpty()) {
            HorizontalScrollView listScroll = new HorizontalScrollView(this);
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            listScroll.addView(row);
            for (ShoppingListData list : lists) {
                Button b = smallButton(list.name, list.id == selectedShoppingListId ? GREEN : MUTED);
                b.setTextColor(list.id == selectedShoppingListId ? WHITE : MUTED);
                b.setBackground(list.id == selectedShoppingListId ? fill(GREEN, dp(6)) : outline(MUTED));
                b.setOnClickListener(v -> {
                    selectedShoppingListId = list.id;
                    showScreen("shopping");
                });
                row.addView(b);
            }
            content.addView(listScroll);
        }

        if (selectedShoppingListId < 0) {
            content.addView(infoCard("Utwórz listę i wrzucaj produkty sklepami. Na telefonie to jest szybkie, nie ceremonialne."));
            return;
        }

        ShoppingListData selected = db.shoppingListById(selectedShoppingListId);
        if (selected == null) {
            selectedShoppingListId = -1;
            showScreen("shopping");
            return;
        }

        LinearLayout addItem = card();
        addItem.addView(text(selected.name + ("closed".equals(selected.status) ? " (zamknięta)" : ""), 18, TEXT, true));
        AutoCompleteTextView store = new AutoCompleteTextView(this);
        store.setHint("Sklep");
        styleTextInput(store);
        store.setSingleLine(true);
        store.setAdapter(new ArrayAdapter<>(
                this,
                android.R.layout.simple_dropdown_item_1line,
                db.getShops()
        ));
        store.setThreshold(0);
        store.setOnClickListener(v -> store.showDropDown());
        store.setOnFocusChangeListener((v, hasFocus) -> {
            if (hasFocus) {
                store.showDropDown();
                ensureFieldVisible(v);
            }
        });

        AutoCompleteTextView product = new AutoCompleteTextView(this);
        product.setHint("Produkt");
        styleTextInput(product);
        product.setSingleLine(true);
        product.setAdapter(new ArrayAdapter<>(
                this,
                android.R.layout.simple_dropdown_item_1line,
                db.getProducts()
        ));
        product.setThreshold(0);
        product.setOnClickListener(v -> product.showDropDown());
        product.setOnFocusChangeListener((v, hasFocus) -> {
            if (hasFocus) {
                product.showDropDown();
                ensureFieldVisible(v);
            }
        });

        EditText qty = input("Ilość domyślna", "1 szt.");
        qty.setSingleLine(true);
        EditText quickProducts = input("Produkty - każdy w nowej linii", "");
        quickProducts.setMinLines(3);
        quickProducts.setGravity(Gravity.TOP | Gravity.START);
        addItem.addView(label("Sklep")); addItem.addView(store);
        addItem.addView(label("Ilość")); addItem.addView(qty);
        addItem.addView(label("Szybkie wpisywanie"));
        addItem.addView(quickProducts);
        addItem.addView(actionButton("Dodaj wpisane", GREEN, v -> {
            int added = addShoppingLines(
                    selectedShoppingListId,
                    quickProducts.getText().toString(),
                    qty.getText().toString().trim(),
                    store.getText().toString().trim()
            );
            if (added < 1) {
                toast("Wpisz produkty");
                return;
            }
            toast("Dodano: " + added);
            showScreen("shopping");
        }));

        addItem.addView(label("Pojedynczy produkt")); addItem.addView(product);
        addItem.addView(actionButton("Dodaj produkt", BLUE, v -> {
            String shopName = store.getText().toString().trim();
            String productName = product.getText().toString().trim();

            if (addShoppingProduct(selectedShoppingListId, productName, qty.getText().toString().trim(), shopName)) {
                showScreen("shopping");
            } else {
                toast("Wpisz produkt");
            }

        }));
        content.addView(addItem);

        Map<String, List<ShoppingItem>> grouped = new LinkedHashMap<>();
        for (ShoppingItem item : db.getShoppingItems(selectedShoppingListId)) {
            String key = item.store == null || item.store.isEmpty() ? "Inne" : item.store;
            if (!grouped.containsKey(key)) {
                grouped.put(key, new ArrayList<>());
            }
            grouped.get(key).add(item);
        }

        if (grouped.isEmpty()) {
            content.addView(infoCard("Lista jest pusta."));
        } else {
            for (Map.Entry<String, List<ShoppingItem>> entry : grouped.entrySet()) {
                LinearLayout box = card();
                box.addView(text(entry.getKey(), 16, BLUE, true));
                for (ShoppingItem item : entry.getValue()) {
                    LinearLayout line = hbox();
                    CheckBox cb = new CheckBox(this);
                    cb.setChecked(item.checked);
                    cb.setText(item.product + " (" + item.quantity + ")");
                    cb.setTextColor(item.checked ? MUTED : TEXT);
                    cb.setOnCheckedChangeListener((buttonView, isChecked) -> db.setShoppingItemChecked(item.id, isChecked));
                    line.addView(cb, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
                    Button del = smallButton("x", RED);
                    del.setOnClickListener(v -> {
                        db.deleteShoppingItem(item.id);
                        showScreen("shopping");
                    });
                    line.addView(del);
                    box.addView(line);
                }
                content.addView(box);
            }
        }

        LinearLayout actions = hbox();
        actions.addView(actionButton("Udostępnij", BLUE, v -> shareShoppingList(selectedShoppingListId)),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        actions.addView(actionButton("Zamknij", ORANGE, v -> {

            if (!db.shoppingListHasItems(selectedShoppingListId)) {
                toast("Lista jest pusta");
                return;
            }

            db.closeShoppingList(selectedShoppingListId);
            showScreen("shopping");

        }), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        actions.addView(actionButton("Usuń", RED, v -> confirmDeleteShoppingList(selectedShoppingListId)),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        content.addView(actions);
    }

    private boolean addShoppingProduct(long listId, String productName, String quantity, String shopName) {
        String safeProduct = productName == null ? "" : productName.trim();
        if (safeProduct.isEmpty()) {
            return false;
        }
        String safeShop = shopName == null ? "" : shopName.trim();
        String safeQty = quantity == null || quantity.trim().isEmpty() ? "1 szt." : quantity.trim();
        db.addShop(safeShop);
        db.addProduct(safeProduct);
        db.addShoppingItem(listId, safeProduct, safeQty, safeShop);
        return true;
    }

    private int addShoppingLines(long listId, String rawLines, String defaultQty, String defaultShop) {
        int added = 0;
        String[] lines = String.valueOf(rawLines == null ? "" : rawLines).split("\\r?\\n");
        for (String rawLine : lines) {
            String line = rawLine.trim();
            if (line.isEmpty()) {
                continue;
            }
            String[] parts = line.split("[,;|]", 3);
            String productName = parts[0].trim();
            String quantity = parts.length > 1 && !parts[1].trim().isEmpty() ? parts[1].trim() : defaultQty;
            String shopName = parts.length > 2 && !parts[2].trim().isEmpty() ? parts[2].trim() : defaultShop;
            if (addShoppingProduct(listId, productName, quantity, shopName)) {
                added++;
            }
        }
        return added;
    }

    private void confirmDeleteShoppingList(long id) {
        new AlertDialog.Builder(this)
                .setTitle("Usuń listę")
                .setPositiveButton("Usuń", (d, w) -> {
                    db.deleteShoppingList(id);
                    selectedShoppingListId = -1;
                    showScreen("shopping");
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }

    private void shareShoppingList(long id) {
        ShoppingListData list = db.shoppingListById(id);
        if (list == null) {
            return;
        }
        Map<String, List<ShoppingItem>> grouped = new LinkedHashMap<>();
        for (ShoppingItem item : db.getShoppingItems(id)) {
            String key = item.store == null || item.store.isEmpty() ? "Inne" : item.store;
            if (!grouped.containsKey(key)) {
                grouped.put(key, new ArrayList<>());
            }
            grouped.get(key).add(item);
        }
        StringBuilder body = new StringBuilder("LISTA: ").append(list.name).append("\n");
        for (Map.Entry<String, List<ShoppingItem>> entry : grouped.entrySet()) {
            body.append("\n--- ").append(entry.getKey()).append(" ---\n");
            for (ShoppingItem item : entry.getValue()) {
                body.append(item.checked ? "[x] " : "[ ] ")
                        .append(item.product.toUpperCase(Locale.ROOT))
                        .append(" (").append(item.quantity).append(")\n");
            }
        }
        Intent send = new Intent(Intent.ACTION_SEND);
        send.setType("text/plain");
        send.putExtra(Intent.EXTRA_SUBJECT, "ZAKUPY: " + list.name);
        send.putExtra(Intent.EXTRA_TEXT, body.toString());
        startActivity(Intent.createChooser(send, "Udostępnij listę"));
    }

    private void buildBills() {
        content.addView(sectionTitle("Rachunki"));
        LinearLayout form = card();
        EditText due = input("Termin RRRR-MM-DD", today());
        attachDatePicker(due);
        EditText amount = input("Kwota", "");
        configureAmountInput(amount, false);
        Spinner category = spinner(list("Opłaty", "Spłata Długu", "Zakupy", "Inne"));
        Spinner liability = spinner(debtNames(db.getDebts("liabilities"), true));
        EditText desc = input("Opis", "");
        CheckBox recurring = new CheckBox(this);
        recurring.setText("Stały co miesiąc");
        recurring.setTextColor(TEXT);
        form.addView(label("Termin")); form.addView(due);
        form.addView(label("Kwota")); form.addView(amount);
        form.addView(label("Kategoria")); form.addView(category);
        form.addView(label("Dług, jeśli dotyczy")); form.addView(liability);
        form.addView(label("Opis")); form.addView(desc);
        form.addView(recurring);
        form.addView(actionButton("Dodaj rachunek", RED, v -> {
            String date = due.getText().toString().trim();
            double a = parseAmount(amount.getText().toString());
            String cat = category.getSelectedItem().toString();
            String description = desc.getText().toString().trim();
            Long refId = null;
            if ("Spłata Długu".equals(cat)) {
                Debt debt = selectedDebtFromLabel(db.getDebts("liabilities"), liability.getSelectedItem() == null ? "" : liability.getSelectedItem().toString());
                if (debt == null) {
                    toast("Wybierz dług");
                    return;
                }
                refId = debt.id;
                description = debt.name;
            }
            if (!isDate(date) || a <= 0 || description.isEmpty()) {
                toast("Uzupełnij rachunek");
                return;
            }
            db.addPendingBill(date, a, cat, description, recurring.isChecked(), refId);
            BudgetReminderReceiver.refreshTasks(this);
            showScreen("bills");
        }));
        content.addView(form);

        List<Bill> bills = db.getPendingBills();
        if (bills.isEmpty()) {
            content.addView(infoCard("Brak rachunków do zapłaty."));
        } else {
            for (Bill bill : bills) {
                addBillCard(bill);
            }
        }
    }

    private void addBillCard(Bill bill) {
        LinearLayout card = card();
        long days = daysBetween(calendarFrom(today()), calendarFrom(bill.dueDate));
        int color = days < 0 ? RED : (days <= 3 ? ORANGE : BLUE);
        card.addView(twoCol(bill.description, money(bill.amount), TEXT, color));
        String when = days < 0 ? "po terminie " + Math.abs(days) + " dni" : (days == 0 ? "dzisiaj" : "za " + days + " dni");
        card.addView(text(bill.dueDate + " | " + bill.category + " | " + when + (bill.recurring ? " | stały" : ""), 12, MUTED, false));
        LinearLayout actions = hbox();
        actions.addView(actionButton("Zapłać", GREEN, v -> payBillDialog(bill)),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        actions.addView(actionButton("Edytuj", BLUE, v -> editBillDialog(bill)),
                new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        actions.addView(actionButton("Usuń", RED, v -> {
            db.deletePendingBill(bill.id);
            BudgetReminderReceiver.refreshTasks(this);
            showScreen("bills");
        }), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        card.addView(actions);
        content.addView(card);
    }

    private void editBillDialog(Bill bill) {
        LinearLayout form = vbox();
        form.setPadding(dp(16), dp(8), dp(16), 0);
        EditText due = input("Termin RRRR-MM-DD", bill.dueDate);
        attachDatePicker(due);
        EditText amount = input("Kwota", formatRaw(bill.amount));
        configureAmountInput(amount, false);
        List<String> billCategories = list("Opłaty", "Spłata Długu", "Zakupy", "Inne");
        if (!billCategories.contains(bill.category)) {
            billCategories.add(bill.category);
        }
        Spinner category = spinner(billCategories);
        selectSpinnerValue(category, bill.category);
        Spinner liability = spinner(debtNames(db.getDebts("liabilities"), true));
        if (bill.refId != null) {
            Debt current = db.debtById("liabilities", bill.refId);
            if (current != null) {
                selectSpinnerValue(liability, current.name + " (" + money(current.remaining()) + ")");
            }
        }
        EditText desc = input("Opis", bill.description);
        CheckBox recurring = new CheckBox(this);
        recurring.setText("Stały co miesiąc");
        recurring.setTextColor(TEXT);
        recurring.setChecked(bill.recurring);
        form.addView(label("Termin")); form.addView(due);
        form.addView(label("Kwota")); form.addView(amount);
        form.addView(label("Kategoria")); form.addView(category);
        form.addView(label("Dług, jeśli dotyczy")); form.addView(liability);
        form.addView(label("Opis")); form.addView(desc);
        form.addView(recurring);

        new AlertDialog.Builder(this)
                .setTitle("Edytuj rachunek")
                .setView(form)
                .setPositiveButton("Zapisz", (d, w) -> {
                    String date = due.getText().toString().trim();
                    double value = parseAmount(amount.getText().toString());
                    String cat = category.getSelectedItem() == null ? "" : category.getSelectedItem().toString();
                    String description = desc.getText().toString().trim();
                    Long refId = null;
                    if ("Spłata Długu".equals(cat)) {
                        Debt debt = selectedDebtFromLabel(db.getDebts("liabilities"),
                                liability.getSelectedItem() == null ? "" : liability.getSelectedItem().toString());
                        if (debt == null) {
                            toast("Wybierz dług");
                            return;
                        }
                        refId = debt.id;
                        description = debt.name;
                    }
                    if (!isDate(date) || value <= 0 || description.isEmpty()) {
                        toast("Uzupełnij rachunek");
                        return;
                    }
                    db.updatePendingBill(bill.id, date, value, cat, description, recurring.isChecked(), refId);
                    BudgetReminderReceiver.refreshTasks(this);
                    showScreen("bills");
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }

    private void payBillDialog(Bill bill) {
        amountDialog("Zapłać rachunek", bill.description + " " + money(bill.amount), GREEN, (amount, details, accountId) -> {
            db.markBillPaid(bill.id);
            String type = "Spłata Długu".equals(bill.category) ? "liability_repayment" : "expense";
            db.addTransaction(today(), type, bill.category, bill.description, amount, 0, details, null, accountId, bill.refId);
            scheduleAfterFinancialChange(type);
            if (bill.recurring) {
                db.addPendingBill(addMonths(bill.dueDate, 1), bill.amount, bill.category, bill.description, true, bill.refId);
            }
            BudgetReminderReceiver.refreshTasks(this);
            showScreen("bills");
        }, bill.amount);
    }


    private void buildSettings() {
        content.addView(sectionTitle("Synchronizacja z PC"));
        LinearLayout sync = card();
        sync.addView(text("SYNC LAN synchronizuje wpisy z desktopem w tej samej sieci bez podmiany całej bazy. Backup ZIP nadal służy do pełnej kopii.", 13, MUTED, false));
        // Nowa, poprawna linijka:
        sync.addView(text("Adres telefonu dla PC: " + String.join(", ", mobileSyncUrls()), 12, MUTED, false));
        EditText syncUrl = input("Adres PC, np. http://192.168.1.20:8765", prefs().getString("sync_url", ""));
        syncUrl.setSingleLine(true);
        sync.addView(label("Adres synchronizacji"));
        sync.addView(syncUrl);
        sync.addView(actionButton("Synchronizuj wpisy", GREEN, v -> {
            String url = syncUrl.getText().toString().trim();
            prefs().edit().putString("sync_url", url).apply();
            confirmSync();
        }));
        sync.addView(actionButton("Eksportuj bazę ZIP", BLUE, v -> exportBackup()));
        sync.addView(actionButton("Importuj bazę ZIP/DB", ORANGE, v -> chooseBackupImport()));
        content.addView(sync);

        content.addView(sectionTitle("Konta"));
        LinearLayout addAcc = card();
        EditText name = input("Nazwa konta", "");
        EditText balance = input("Saldo początkowe", "0.00");
        configureAmountInput(balance, true);
        Spinner color = spinner(list("#27ae60", "#2980b9", "#c0392b", "#d35400", "#8e44ad", "#7f8c8d"));
        addAcc.addView(name);
        addAcc.addView(label("Saldo początkowe")); addAcc.addView(balance);
        addAcc.addView(label("Kolor")); addAcc.addView(color);
        addAcc.addView(actionButton("Dodaj konto", GREEN, v -> {
            String n = name.getText().toString().trim();
            if (n.isEmpty()) {
                toast("Podaj nazwę konta");
                return;
            }
            if (!db.addAccount(n, parseAmount(balance.getText().toString()), color.getSelectedItem().toString())) {
                toast("Nie udało się dodać konta");
                return;
            }
            showScreen("settings");
        }));
        content.addView(addAcc);

        for (Account acc : db.getAccounts()) {
            LinearLayout row = card();
            row.addView(twoCol(acc.name, money(db.accountBalance(acc.id)), parseColor(acc.color, TEXT), TEXT));
            if (acc.id != 1) {
                row.addView(actionButton("Usuń konto", RED, v -> {
                    db.deleteAccount(acc.id);
                    showScreen("settings");
                }));
            }
            content.addView(row);
        }

        content.addView(sectionTitle("Kategorie"));
        LinearLayout catForm = card();
        EditText catName = input("Nowa kategoria", "");
        catForm.addView(catName);
        catForm.addView(actionButton("Dodaj kategorię", BLUE, v -> {
            db.addCategory(catName.getText().toString().trim());
            showScreen("settings");
        }));
        content.addView(catForm);
        LinearLayout catBox = card();
        for (String cat : db.getCategories()) {
            catBox.addView(text(cat, 14, TEXT, false));
        }
        content.addView(catBox);

        content.addView(sectionTitle("Limit tygodniowy"));
        LinearLayout weekly = card();
        CheckBox enabled = new CheckBox(this);
        enabled.setText("Włącz limit tygodniowy");
        enabled.setTextColor(TEXT);
        enabled.setChecked(db.isWeeklyEnabled());
        EditText amount = input("Kwota limitu", formatRaw(db.weeklyAmount()));
        configureAmountInput(amount, false);
        weekly.addView(enabled);
        weekly.addView(label("Limit"));
        weekly.addView(amount);
        weekly.addView(actionButton("Zapisz limit", BLUE, v -> {
            db.saveWeeklyConfig(enabled.isChecked(), parseAmount(amount.getText().toString()), db.getCategories());
            toast("Zapisano limit");
            BudgetReminderReceiver.schedule(this);
        }));
        content.addView(weekly);

        buildNotificationSettings();
    }

    private void buildNotificationSettings() {
        content.addView(sectionTitle("Powiadomienia"));
        LinearLayout box = card();
        SharedPreferences p = prefs();
        CheckBox master = notificationCheck("Włącz powiadomienia systemowe", "notifications_master", true);
        CheckBox balance = notificationCheck("Stan kont", "notify_balance", true);
        CheckBox bills = notificationCheck("Rachunki i stałe wydatki", "notify_bills", true);
        CheckBox weekly = notificationCheck("Limit tygodniowy", "notify_weekly", true);
        CheckBox goals = notificationCheck("Cele oszczędnościowe", "notify_goals", true);
        CheckBox debts = notificationCheck("Długi i dłużnicy", "notify_debts", true);
        CheckBox backup = notificationCheck("Cotygodniowa kopia zapasowa", "notify_backup", true);
        CheckBox daily = notificationCheck("Codzienne przypomnienie o wydatkach", "notify_daily_expenses", true);
        CheckBox insights = notificationCheck("Zróżnicowane podpowiedzi zakupowe", "notify_insights", true);
        EditText startHour = input("Od, np. 8", String.valueOf(p.getInt("notify_start_hour", 8)));
        EditText endHour = input("Do, np. 18", String.valueOf(p.getInt("notify_end_hour", 18)));
        startHour.setInputType(InputType.TYPE_CLASS_NUMBER);
        endHour.setInputType(InputType.TYPE_CLASS_NUMBER);
        box.addView(master);
        box.addView(balance);
        box.addView(bills);
        box.addView(weekly);
        box.addView(goals);
        box.addView(debts);
        box.addView(backup);
        box.addView(daily);
        box.addView(insights);
        box.addView(label("Zakres godzin"));
        LinearLayout range = hbox();
        range.addView(startHour, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        range.addView(endHour, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        box.addView(range);
        box.addView(actionButton("Zapisz powiadomienia", BLUE, v -> {
            int start = (int) Math.max(0, Math.min(23, parseAmount(startHour.getText().toString())));
            int end = (int) Math.max(0, Math.min(23, parseAmount(endHour.getText().toString())));
            prefs().edit()
                    .putInt("notify_start_hour", start)
                    .putInt("notify_end_hour", end)
                    .apply();
            ensureNotificationPermission();
            BudgetReminderReceiver.schedule(this);
            BudgetReminderReceiver.refreshTasks(this);
            toast("Zapisano powiadomienia");
        }));
        box.addView(actionButton("Wyślij test", GREEN, v -> {
            ensureNotificationPermission();
            BudgetReminderReceiver.sendTest(this);
        }));
        content.addView(box);
    }

    private CheckBox notificationCheck(String label, String key, boolean def) {
        CheckBox cb = new CheckBox(this);
        cb.setText(label);
        cb.setTextColor(TEXT);
        cb.setTextSize(15);
        cb.setMinHeight(dp(44));
        cb.setChecked(prefs().getBoolean(key, def));
        cb.setOnCheckedChangeListener((buttonView, isChecked) ->
                prefs().edit().putBoolean(key, isChecked).apply());
        return cb;
    }

    private void amountDialog(String title, String subtitle, int color, AmountCallback callback) {
        amountDialog(title, subtitle, color, callback, 0.0);
    }

    private void amountDialog(String title, String subtitle, int color, AmountCallback callback, double prefill) {
        LinearLayout form = vbox();
        form.setPadding(dp(16), dp(8), dp(16), 0);
        form.addView(text(subtitle, 14, MUTED, false));
        Spinner account = accountSpinner();
        EditText amount = input("Kwota", prefill > 0 ? formatRaw(prefill) : "");
        configureAmountInput(amount, false);
        EditText details = input("Szczegóły", "");
        form.addView(label("Konto")); form.addView(account);
        form.addView(label("Kwota")); form.addView(amount);
        form.addView(label("Szczegóły")); form.addView(details);

        new AlertDialog.Builder(this)
                .setTitle(title)
                .setView(form)
                .setPositiveButton("Zapisz", (d, w) -> {
                    double a = parseAmount(amount.getText().toString());
                    if (a <= 0) {
                        toast("Niepoprawna kwota");
                        return;
                    }
                    callback.onAmount(a, details.getText().toString().trim(), selectedAccount(account).id);
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }

    private void chooseAttachment() {
        chooseAttachment(REQUEST_ATTACH);
    }

    private void chooseEditAttachment() {
        chooseAttachment(REQUEST_EDIT_ATTACH);
    }

    private void chooseAttachment(int requestCode) {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"image/jpeg", "image/png", "application/pdf"});
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try {
            startActivityForResult(intent, requestCode);
        } catch (ActivityNotFoundException ex) {
            toast("Brak aplikacji do wyboru pliku");
        }
    }

    private void attachFromUri(Uri uri) {
        try {
            selectedAttachment = readAttachment(uri);
            updateAttachmentLabel();
            toast("Załączono plik");
        } catch (IOException ex) {
            toast(ex.getMessage() == null ? "Nie udało się dodać załącznika" : ex.getMessage());
        }
    }

    private void attachEditFromUri(Uri uri) {
        try {
            pendingEditAttachment = readAttachment(uri);
            updateEditAttachmentLabel();
            toast("Załączono plik");
        } catch (IOException ex) {
            toast(ex.getMessage() == null ? "Nie udało się dodać załącznika" : ex.getMessage());
        }
    }

    private AttachmentDraft readAttachment(Uri uri) throws IOException {
        String displayName = "zalacznik.dat";
        String mimeType = getContentResolver().getType(uri);
        long declaredSize = -1;

        Cursor cursor = getContentResolver().query(uri, null, null, null, null);
        if (cursor != null) {
            try {
                int nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                int sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE);
                if (cursor.moveToFirst()) {
                    if (nameIndex >= 0) {
                        displayName = cursor.getString(nameIndex);
                    }
                    if (sizeIndex >= 0) {
                        declaredSize = cursor.getLong(sizeIndex);
                    }
                }
            } finally {
                cursor.close();
            }
        }

        if (declaredSize > MAX_ATTACHMENT_BYTES) {
            throw new IOException("Załącznik jest za duży");
        }

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (InputStream in = getContentResolver().openInputStream(uri)) {
            if (in == null) {
                throw new IOException("Nie można odczytać pliku");
            }
            byte[] buffer = new byte[8192];
            int read;
            long size = 0;
            while ((read = in.read(buffer)) != -1) {
                size += read;
                if (size > MAX_ATTACHMENT_BYTES) {
                    throw new IOException("Załącznik jest za duży");
                }
                out.write(buffer, 0, read);
            }
        }
        return new AttachmentDraft(safeName(displayName), mimeType == null ? "application/octet-stream" : mimeType, out.toByteArray());
    }

    private void updateAttachmentLabel() {
        if (txAttachmentText == null) {
            return;
        }
        if (selectedAttachment == null) {
            txAttachmentText.setText("Załącznik: brak");
        } else {
            txAttachmentText.setText("Załącznik: " + selectedAttachment.name + " (" + humanSize(selectedAttachment.data.length) + ")");
        }
    }

    private void updateEditAttachmentLabel() {
        if (pendingEditAttachmentText == null) {
            return;
        }
        if (pendingEditAttachment != null) {
            pendingEditAttachmentText.setText("Nowy załącznik: " + pendingEditAttachment.name
                    + " (" + humanSize(pendingEditAttachment.data.length) + ")");
        } else {
            pendingEditAttachmentText.setText(pendingEditHadAttachment ? "Załącznik: obecny" : "Załącznik: brak");
        }
    }

    private void openAttachment(Tx tx) {
        File file = db.attachmentFile(tx.attachment);
        if (file == null || !file.isFile()) {
            toast("Nie znaleziono załącznika");
            return;
        }

        try {
            String ext = extensionForAttachment(file).toLowerCase(Locale.ROOT);

            String mimeType;
            if (ext.equals(".jpg") || ext.equals(".jpeg")) {
                mimeType = "image/jpeg";
            } else if (ext.equals(".png")) {
                mimeType = "image/png";
            } else if (ext.equals(".pdf")) {
                mimeType = "application/pdf";
            } else {
                mimeType = "*/*";
            }

            Uri uri = writeDownload(
                    "budget-zalacznik-" + tx.id + ext,
                    mimeType,
                    out -> copyFile(file, out));

            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, mimeType);
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);

            startActivity(intent);

        } catch (Exception ex) {
            toast("Nie udało się otworzyć pliku");
        }
    }

    private void chooseBackupImport() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try {
            startActivityForResult(intent, REQUEST_IMPORT_BACKUP);
        } catch (ActivityNotFoundException ex) {
            toast("Brak aplikacji do wyboru pliku");
        }
    }

    private void exportBackup() {
        try {
            db.checkpoint();
            String filename = "budzet-mobile-backup-" + new SimpleDateFormat("yyyyMMdd-HHmmss", Locale.ROOT).format(new Date()) + ".zip";
            Uri uri = writeDownload(filename, "application/zip", out -> {
                try (ZipOutputStream zip = new ZipOutputStream(out)) {
                    zipFile(zip, db.dbFile, "budzet.db");
                    zipDirectory(zip, db.attachmentsDir, "attachments/");
                }
            });
            Intent intent = new Intent(Intent.ACTION_SEND);
            intent.setType("application/zip");
            intent.putExtra(Intent.EXTRA_STREAM, uri);
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(Intent.createChooser(intent, "Wyślij backup do PC"));
            toast("Backup zapisany w Pobrane/BudgetApp");
        } catch (Exception ex) {
            toast("Nie udało się wyeksportować bazy");
        }
    }

    private void importBackup(Uri uri) {
        File tmp = new File(getCacheDir(), "budget-import.tmp");
        try (InputStream in = getContentResolver().openInputStream(uri);
             OutputStream out = new FileOutputStream(tmp)) {
            if (in == null) {
                throw new IOException("Brak strumienia");
            }
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }
        } catch (IOException ex) {
            toast("Nie udało się odczytać importu");
            return;
        }

        try {
            db.close();
            if (looksLikeZip(tmp)) {
                importZip(tmp);
            } else {
                replaceDatabaseFile(tmp);
            }
            db.open();
            toast("Import zakończony");
            showScreen("home");
        } catch (Exception ex) {
            db.open();
            toast("Import nieudany: " + ex.getMessage());
        } finally {
            tmp.delete();
        }
    }

    private String normalizeSyncBaseUrl(String rawUrl) {
        String baseUrl = rawUrl == null ? "" : rawUrl.trim();
        if (baseUrl.isEmpty()) {
            return "";
        }
        if (!baseUrl.startsWith("http://") && !baseUrl.startsWith("https://")) {
            baseUrl = "http://" + baseUrl;
        }
        while (baseUrl.endsWith("/")) {
            baseUrl = baseUrl.substring(0, baseUrl.length() - 1);
        }
        if (baseUrl.endsWith("/sync")) {
            baseUrl = baseUrl.substring(0, baseUrl.length() - 5);
        }
        return baseUrl;
    }

    private String peerBaseUrlFromPayload(JSONObject payload, String fallback) {
        JSONArray urls = payload == null ? null : payload.optJSONArray("device_urls");
        if (urls != null) {
            for (int i = 0; i < urls.length(); i++) {
                String url = urls.optString(i, "").trim();
                if (!url.isEmpty()) {
                    return normalizeSyncBaseUrl(url);
                }
            }
        }
        return normalizeSyncBaseUrl(fallback);
    }

    private SyncResult downloadMissingSyncAttachments(String peerBaseUrl, JSONObject payload) {
        SyncResult result = new SyncResult();
        JSONArray rows = payload == null ? null : payload.optJSONArray("transactions");
        if (rows == null || rows.length() == 0 || peerBaseUrl == null || peerBaseUrl.trim().isEmpty()) {
            return result;
        }
        String baseUrl = normalizeSyncBaseUrl(peerBaseUrl);
        for (int i = 0; i < rows.length(); i++) {
            JSONObject tx = rows.optJSONObject(i);
            if (tx == null || !tx.optBoolean("attachment_present", false)) {
                continue;
            }
            String syncId = tx.optString("sync_id", "").trim();
            if (syncId.isEmpty()) {
                continue;
            }
            long size = tx.optLong("attachment_size", -1);
            String sha = tx.optString("attachment_sha256", "").trim();
            synchronized (db) {
                if (!db.needsSyncAttachmentDownload(syncId, size, sha)) {
                    continue;
                }
            }
            File tmp = null;
            try {
                tmp = File.createTempFile("budget-sync-attachment-", ".tmp", getCacheDir());
                downloadSyncAttachment(baseUrl, tx, tmp);
                synchronized (db) {
                    if (db.saveSyncAttachment(syncId, tx.optString("attachment_name", "zalacznik.dat"), tmp)) {
                        result.attachmentsDownloaded++;
                    } else {
                        result.attachmentErrors++;
                    }
                }
            } catch (Exception ex) {
                result.attachmentErrors++;
            } finally {
                if (tmp != null) {
                    tmp.delete();
                }
            }
        }
        return result;
    }

    private void downloadSyncAttachment(String baseUrl, JSONObject tx, File target) throws IOException {
        String syncId = tx.optString("sync_id", "").trim();
        String expectedSha = tx.optString("attachment_sha256", "").trim();
        long expectedSize = tx.optLong("attachment_size", -1);
        String url = normalizeSyncBaseUrl(baseUrl) + "/attachment/" + URLEncoder.encode(syncId, "UTF-8");
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setRequestMethod("GET");
        conn.setConnectTimeout(15000);
        conn.setReadTimeout(120000);
        int code = conn.getResponseCode();
        if (code < 200 || code >= 300) {
            throw new IOException("HTTP " + code);
        }
        long length = conn.getContentLengthLong();
        if (length > MAX_SYNC_ATTACHMENT_BYTES) {
            throw new IOException("Załącznik jest za duży");
        }
        MessageDigest digest = sha256Digest();
        long total = 0;
        try (InputStream in = conn.getInputStream();
             OutputStream out = new FileOutputStream(target)) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) {
                total += read;
                if (total > MAX_SYNC_ATTACHMENT_BYTES) {
                    throw new IOException("Załącznik jest za duży");
                }
                digest.update(buffer, 0, read);
                out.write(buffer, 0, read);
            }
        } finally {
            conn.disconnect();
        }
        if (expectedSize >= 0 && total != expectedSize) {
            throw new IOException("Niepełny załącznik");
        }
        if (!expectedSha.isEmpty() && !expectedSha.equalsIgnoreCase(hex(digest.digest()))) {
            throw new IOException("Nieprawidłowy załącznik");
        }
    }

    private void syncWithPc(String rawUrl) {
        if (rawUrl == null || rawUrl.trim().isEmpty()) {
            toast("Wpisz adres PC z włączonym SYNC LAN");
            return;
        }
        String baseUrl = normalizeSyncBaseUrl(rawUrl);
        final String endpoint = baseUrl + "/sync";
        toast("Synchronizuję...");
        new Thread(() -> {
            try {
                JSONObject payload;
                synchronized (db) {
                    payload = db.exportSyncPayload();
                }
                payload.put("device", Build.MANUFACTURER + " " + Build.MODEL);
                payload.put("device_urls", new JSONArray(mobileSyncUrls()));
                byte[] body = payload.toString().getBytes(StandardCharsets.UTF_8);
                if (body.length > MAX_SYNC_BODY_BYTES) {
                    throw new IOException("Dane synchronizacji są za duże");
                }

                HttpURLConnection conn = (HttpURLConnection) new URL(endpoint).openConnection();
                conn.setRequestMethod("POST");
                conn.setConnectTimeout(15000);
                conn.setReadTimeout(30000);
                conn.setDoOutput(true);
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                conn.setRequestProperty("Accept", "application/json");
                try (OutputStream out = conn.getOutputStream()) {
                    out.write(body);
                }
                int code = conn.getResponseCode();
                InputStream stream = code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream();
                int responseLength = conn.getContentLength();
                if (responseLength > MAX_SYNC_BODY_BYTES) {
                    throw new IOException("Odpowiedź synchronizacji jest za duża");
                }
                String response = readUtf8(stream, MAX_SYNC_BODY_BYTES);
                if (code < 200 || code >= 300) {
                    throw new IOException(response.isEmpty() ? "HTTP " + code : response);
                }
                JSONObject result = new JSONObject(response);
                SyncResult imported;
                synchronized (db) {
                    imported = db.importSyncPayload(result);
                }
                SyncResult attachmentSync = downloadMissingSyncAttachments(peerBaseUrlFromPayload(result, baseUrl), result);
                imported.attachmentsDownloaded = attachmentSync.attachmentsDownloaded;
                imported.attachmentErrors = attachmentSync.attachmentErrors;
                runOnUiThread(() -> {
                    showScreen(currentScreen);
                    toast("Zaktualizowano dane");
                });
            } catch (Exception ex) {
                runOnUiThread(() -> toast("Sync nieudany: " + syncErrorMessage(ex)));
            } catch (Throwable error) {
                runOnUiThread(() -> toast("Sync nieudany: " + syncErrorMessage(error)));
            }
        }).start();
    }

    private void startMobileSyncServer() {
        stopMobileSyncServer();
        mobileSyncServer = new MobileSyncServer(8765);
        try {
            mobileSyncServer.start();
        } catch (IOException ex) {
            mobileSyncServer = null;
        }
    }

    private void stopMobileSyncServer() {
        if (mobileSyncServer != null) {
            mobileSyncServer.stop();
            mobileSyncServer = null;
        }
    }

    private List<String> mobileSyncUrls() {
        int port = mobileSyncServer == null ? 8765 : mobileSyncServer.port();
        List<String> urls = new ArrayList<>();
        for (String ip : localIpv4Addresses()) {
            urls.add("http://" + ip + ":" + port);
        }
        if (urls.isEmpty()) {
            urls.add("http://127.0.0.1:" + port);
        }
        return urls;
    }

    private List<String> localIpv4Addresses() {
        List<String> out = new ArrayList<>();
        try {
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            while (interfaces != null && interfaces.hasMoreElements()) {
                NetworkInterface iface = interfaces.nextElement();
                if (!iface.isUp() || iface.isLoopback()) {
                    continue;
                }
                Enumeration<InetAddress> addresses = iface.getInetAddresses();
                while (addresses.hasMoreElements()) {
                    InetAddress addr = addresses.nextElement();
                    if (addr instanceof Inet4Address && !addr.isLoopbackAddress()) {
                        out.add(addr.getHostAddress());
                    }
                }
            }
        } catch (Exception ignored) {
        }
        return out;
    }

    private class MobileSyncServer {
        private ServerSocket serverSocket;
        private Thread thread;
        private volatile boolean running;
        private int port;

        MobileSyncServer(int port) {
            this.port = port;
        }

        void start() throws IOException {
            IOException last = null;
            for (int candidate = port; candidate <= port + 5; candidate++) {
                try {
                    ServerSocket socket = new ServerSocket(candidate);
                    serverSocket = socket;
                    port = candidate;
                    break;
                } catch (IOException ex) {
                    last = ex;
                }
            }
            if (serverSocket == null) {
                throw last == null ? new IOException("Nie można uruchomić serwera") : last;
            }
            running = true;
            thread = new Thread(() -> {
                while (running) {
                    try {
                        Socket socket = serverSocket.accept();
                        new Thread(() -> handleSyncSocket(socket), "budget-sync-client").start();
                    } catch (IOException ignored) {
                        if (!running) {
                            return;
                        }
                    }
                }
            }, "budget-sync-server");
            thread.setDaemon(true);
            thread.start();
        }

        int port() {
            return port;
        }

        void stop() {
            running = false;
            if (serverSocket != null) {
                try {
                    serverSocket.close();
                } catch (IOException ignored) {
                }
            }
        }
    }

    private void handleSyncSocket(Socket socket) {
        OutputStream out = null;
        try (Socket s = socket) {
            InputStream in = s.getInputStream();
            out = s.getOutputStream();
            String first = readHttpLine(in);
            if (first == null || first.trim().isEmpty()) {
                return;
            }
            String[] parts = first.split(" ");
            String method = parts.length > 0 ? parts[0] : "GET";
            String path = parts.length > 1 ? parts[1] : "/";
            String cleanPath = path.split("\\?", 2)[0];
            int length = 0;
            String header;
            while ((header = readHttpLine(in)) != null && !header.isEmpty()) {
                int sep = header.indexOf(':');
                if (sep > 0 && "content-length".equals(header.substring(0, sep).trim().toLowerCase(Locale.ROOT))) {
                    try {
                        length = Integer.parseInt(header.substring(sep + 1).trim());
                    } catch (NumberFormatException ignored) {
                    }
                }
            }
            if (length < 0 || length > MAX_SYNC_BODY_BYTES) {
                throw new IOException("Dane synchronizacji są za duże");
            }
            byte[] bodyBytes = new byte[length];
            int read = 0;
            while (read < length) {
                int count = in.read(bodyBytes, read, length - read);
                if (count < 0) {
                    break;
                }
                read += count;
            }

            JSONObject response;
            int code = 200;
            if ("GET".equals(method) && cleanPath.startsWith("/attachment/")) {
                String syncId = URLDecoder.decode(cleanPath.substring("/attachment/".length()), "UTF-8");
                File file;
                synchronized (db) {
                    file = db.attachmentFileForSyncId(syncId);
                }
                if (file == null || !file.isFile()) {
                    response = new JSONObject();
                    response.put("ok", false);
                    response.put("error", "Nie znaleziono załącznika");
                    writeHttpJson(out, 404, response);
                } else {
                    writeHttpFile(out, file);
                }
                return;
            } else if ("GET".equals(method) && "/status".equals(cleanPath)) {
                response = new JSONObject();
                response.put("ok", true);
                response.put("service", "BudgetApp Mobile Sync LAN");
                response.put("urls", new JSONArray(mobileSyncUrls()));
            } else if ("GET".equals(method) && "/transactions".equals(cleanPath)) {
                synchronized (db) {
                    response = db.exportSyncPayload();
                }
                response.put("ok", true);
            } else if ("POST".equals(method) && "/sync".equals(cleanPath)) {
                JSONObject incoming = new JSONObject(new String(bodyBytes, 0, read, StandardCharsets.UTF_8));
                SyncResult imported;
                synchronized (db) {
                    imported = db.importSyncPayload(incoming);
                }
                String fallbackPeerUrl = "http://" + s.getInetAddress().getHostAddress() + ":8765";
                SyncResult attachmentSync = downloadMissingSyncAttachments(peerBaseUrlFromPayload(incoming, fallbackPeerUrl), incoming);
                imported.attachmentsDownloaded = attachmentSync.attachmentsDownloaded;
                imported.attachmentErrors = attachmentSync.attachmentErrors;
                synchronized (db) {
                    response = db.exportSyncPayload();
                }
                JSONObject importedJson = new JSONObject();
                importedJson.put("inserted", imported.inserted);
                importedJson.put("updated", imported.updated);
                importedJson.put("deleted", imported.deleted);
                importedJson.put("attachments_downloaded", imported.attachmentsDownloaded);
                importedJson.put("attachment_errors", imported.attachmentErrors);
                response.put("ok", true);
                response.put("imported", importedJson);
                runOnUiThread(() -> {
                    showScreen(currentScreen);
                    toast("Zaktualizowano dane");
                });
            } else {
                code = 404;
                response = new JSONObject();
                response.put("ok", false);
                response.put("error", "Nieznany endpoint");
            }
            writeHttpJson(out, code, response);
        } catch (Exception ex) {
            writeSyncError(out, ex);
        } catch (Throwable error) {
            writeSyncError(out, error);
        }
    }

    private void writeSyncError(OutputStream out, Throwable error) {
        if (out == null) {
            return;
        }
        try {
            JSONObject response = new JSONObject();
            response.put("ok", false);
            response.put("error", syncErrorMessage(error));
            writeHttpJson(out, 500, response);
        } catch (Throwable ignored) {
        }
    }

    private String syncErrorMessage(Throwable error) {
        if (error == null) {
            return "Nieznany błąd";
        }
        String message = error.getMessage();
        if (message == null || message.trim().isEmpty()) {
            return error.getClass().getSimpleName();
        }
        return message;
    }

    private String readHttpLine(InputStream in) throws IOException {
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        int prev = -1;
        int current;
        while ((current = in.read()) != -1) {
            if (prev == '\r' && current == '\n') {
                byte[] bytes = buffer.toByteArray();
                int length = bytes.length > 0 && bytes[bytes.length - 1] == '\r' ? bytes.length - 1 : bytes.length;
                return new String(bytes, 0, length, StandardCharsets.US_ASCII);
            }
            buffer.write(current);
            prev = current;
        }
        if (buffer.size() == 0) {
            return null;
        }
        return buffer.toString("US-ASCII");
    }

    private void writeHttpJson(OutputStream out, int code, JSONObject payload) throws IOException {
        byte[] body = payload.toString().getBytes(StandardCharsets.UTF_8);
        if (body.length > MAX_SYNC_BODY_BYTES) {
            throw new IOException("Odpowiedź synchronizacji jest za duża");
        }
        String status = code == 200 ? "OK" : "ERROR";
        String headers = "HTTP/1.1 " + code + " " + status + "\r\n"
                + "Content-Type: application/json; charset=utf-8\r\n"
                + "Content-Length: " + body.length + "\r\n"
                + "Connection: close\r\n\r\n";
        out.write(headers.getBytes(StandardCharsets.UTF_8));
        out.write(body);
        out.flush();
    }

    private void writeHttpFile(OutputStream out, File file) throws IOException {
        if (file.length() > MAX_SYNC_ATTACHMENT_BYTES) {
            throw new IOException("Załącznik jest za duży");
        }
        String headers = "HTTP/1.1 200 OK\r\n"
                + "Content-Type: application/octet-stream\r\n"
                + "Content-Length: " + file.length() + "\r\n"
                + "Connection: close\r\n\r\n";
        out.write(headers.getBytes(StandardCharsets.UTF_8));
        try (InputStream in = new FileInputStream(file)) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }
        }
        out.flush();
    }

    private String readUtf8(InputStream stream, int maxBytes) throws IOException {
        if (stream == null) {
            return "";
        }
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int total = 0;
        int read;
        try (InputStream in = stream) {
            while ((read = in.read(buffer)) != -1) {
                total += read;
                if (total > maxBytes) {
                    throw new IOException("Odpowiedź synchronizacji jest za duża");
                }
                out.write(buffer, 0, read);
            }
        }
        return new String(out.toByteArray(), StandardCharsets.UTF_8);
    }

    private void importZip(File zipFile) throws IOException {
        File base = getFilesDir();
        File newDb = null;
        File tempDir = new File(getCacheDir(), "budget-import-unzip");
        deleteRecursively(tempDir);
        tempDir.mkdirs();

        try (ZipInputStream zip = new ZipInputStream(new FileInputStream(zipFile))) {
            ZipEntry entry;
            while ((entry = zip.getNextEntry()) != null) {
                if (entry.isDirectory()) {
                    continue;
                }
                String name = entry.getName();
                if ("budzet.db".equals(name)) {
                    newDb = new File(tempDir, "budzet.db");
                    try (OutputStream out = new FileOutputStream(newDb)) {
                        copyStream(zip, out);
                    }
                } else if (name.startsWith("attachments/") && !name.endsWith("/")) {
                    File out = safeZipTarget(tempDir, name);
                    File parent = out.getParentFile();
                    if (parent != null) {
                        parent.mkdirs();
                    }
                    try (OutputStream stream = new FileOutputStream(out)) {
                        copyStream(zip, stream);
                    }
                }
            }
        }

        if (newDb == null || !newDb.isFile()) {
            throw new IOException("Brak budzet.db w ZIP");
        }

        replaceDatabaseFile(newDb);
        deleteRecursively(db.attachmentsDir);
        File importedAttachments = new File(tempDir, "attachments");
        if (importedAttachments.isDirectory()) {
            copyDirectory(importedAttachments, db.attachmentsDir);
        } else {
            db.attachmentsDir.mkdirs();
        }
        deleteRecursively(tempDir);
        if (!base.equals(getFilesDir())) {
            throw new IOException("Nieprawidłowy katalog importu");
        }
    }

    private void replaceDatabaseFile(File source) throws IOException {
        deleteSqliteSidecars(db.dbFile);
        copyFile(source, db.dbFile);
        deleteSqliteSidecars(db.dbFile);
    }

    private void deleteSqliteSidecars(File databaseFile) {
        if (databaseFile == null) {
            return;
        }
        File parent = databaseFile.getParentFile();
        if (parent == null) {
            return;
        }
        String name = databaseFile.getName();
        for (String suffix : new String[]{"-wal", "-shm", "-journal"}) {
            new File(parent, name + suffix).delete();
        }
    }

    private Uri writeDownload(String filename, String mime, StreamWriter writer) throws IOException {
        ContentResolver resolver = getContentResolver();
        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, filename);
        values.put(MediaStore.Downloads.MIME_TYPE, mime);
        values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/BudgetApp");
        values.put(MediaStore.Downloads.IS_PENDING, 1);
        Uri uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
        if (uri == null) {
            throw new IOException("Brak URI eksportu");
        }
        try (OutputStream out = resolver.openOutputStream(uri)) {
            if (out == null) {
                throw new IOException("Brak strumienia eksportu");
            }
            writer.write(out);
        }
        values.clear();
        values.put(MediaStore.Downloads.IS_PENDING, 0);
        resolver.update(uri, values, null, null);
        return uri;
    }

    private void buildTransactionsAfterSearch(String text) {
        showScreen("transactions");
        if (transactionSearchInput != null) {
            transactionSearchInput.setText(text);
            buildTransactionsRefresh();
        }
    }

    private TextView sectionTitle(String value) {
        TextView t = text(value, 18, TEXT, true);
        t.setPadding(0, dp(14), 0, dp(6));
        return t;
    }

    private LinearLayout metricCard(String title, String value, int color) {
        LinearLayout box = card();
        box.setPadding(dp(12), dp(10), dp(12), dp(10));
        box.addView(text(title, 12, MUTED, true));
        box.addView(text(value, 21, color, true));
        return box;
    }

    private LinearLayout infoCard(String message) {
        LinearLayout box = card();
        box.addView(text(message, 14, MUTED, false));
        return box;
    }

    private TextView label(String value) {
        TextView label = text(value, 12, TEXT, true);
        label.setPadding(0, dp(8), 0, dp(2));
        return label;
    }

    private TextView twoCol(String left, String right, int leftColor, int rightColor) {
        TextView row = text(left + "\n" + right, 14, leftColor, true);
        row.setPadding(0, dp(4), 0, dp(4));
        String full = left + "\n" + right;
        SpannableString span = new SpannableString(full);
        span.setSpan(new ForegroundColorSpan(leftColor), 0, left.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        span.setSpan(new ForegroundColorSpan(rightColor), left.length() + 1, full.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        row.setText(span);
        row.setGravity(Gravity.START);
        row.setTextAlignment(View.TEXT_ALIGNMENT_GRAVITY);
        return row;
    }

    private ProgressBar progressLine(double value, double max, int color) {
        ProgressBar bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(1000);
        int progress = max <= 0 ? 0 : (int) Math.max(0, Math.min(1000, (value / max) * 1000));
        bar.setProgress(progress);
        bar.setPadding(0, 0, 0, dp(8));
        bar.getProgressDrawable().setTint(color);
        return bar;
    }

    private LinearLayout card() {
        LinearLayout box = vbox();
        box.setPadding(dp(14), dp(14), dp(14), dp(14));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, dp(7), 0, dp(10));
        box.setLayoutParams(params);
        box.setBackground(cardBg());
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            box.setElevation(dp(1));
        }
        return box;
    }

    private GradientDrawable cardBg() {
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(WHITE);
        bg.setCornerRadius(dp(8));
        bg.setStroke(dp(1), BORDER);
        return bg;
    }

    private LinearLayout vbox() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        return box;
    }

    private LinearLayout hbox() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.HORIZONTAL);
        box.setGravity(Gravity.CENTER_VERTICAL);
        GradientDrawable divider = new GradientDrawable();
        divider.setColor(Color.TRANSPARENT);
        divider.setSize(dp(8), 1);
        box.setDividerDrawable(divider);
        box.setShowDividers(LinearLayout.SHOW_DIVIDER_MIDDLE);
        return box;
    }

    private TextView text(String value, int sp, int color, boolean bold) {
        TextView text = new TextView(this);
        text.setText(value);
        text.setTextSize(sp);
        text.setTextColor(color);
        text.setIncludeFontPadding(true);
        if (bold) {
            text.setTypeface(text.getTypeface(), Typeface.BOLD);
        }
        return text;
    }

    private EditText input(String hint, String value) {
        AutoCompleteTextView input = new AutoCompleteTextView(this);
        input.setHint(hint);
        input.setText(value);
        styleTextInput(input);
        installAutoComplete(input);
        return input;
    }

    private EditText expenseDetailsInput(String hint, String value) {
        MultiAutoCompleteTextView input = new MultiAutoCompleteTextView(this);
        input.setHint(hint);
        input.setText(value);
        styleTextInput(input);
        input.setSingleLine(false);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        input.setImeOptions(EditorInfo.IME_ACTION_NONE);
        input.setTokenizer(new NewlineTokenizer());
        installExpenseDetailsAutoComplete(input);
        return input;
    }

    private void installAutoComplete(AutoCompleteTextView input) {
        if (db == null || input == null) {
            return;
        }
        String kind = suggestionKindForHint(input.getHint());
        if (kind == null) {
            input.setAdapter(null);
            return;
        }
        List<String> suggestions = db.textSuggestions(kind);
        if (suggestions.isEmpty()) {
            input.setAdapter(null);
            return;
        }
        input.setAdapter(new ArrayAdapter<>(
                this,
                android.R.layout.simple_dropdown_item_1line,
                suggestions
        ));
        input.setThreshold(1);
        input.setOnEditorActionListener((v, actionId, event) -> {
            if (input.isPopupShowing()) {
                input.performCompletion();
                return true;
            }
            return false;
        });
    }

    private void installExpenseDetailsAutoComplete(MultiAutoCompleteTextView input) {
        if (db == null || input == null) {
            return;
        }
        List<String> suggestions = db.textSuggestions("expense_details");
        if (suggestions.isEmpty()) {
            input.setAdapter(null);
            return;
        }
        input.setAdapter(new ArrayAdapter<>(
                this,
                android.R.layout.simple_dropdown_item_1line,
                suggestions
        ));
        input.setThreshold(1);
        input.setOnEditorActionListener((v, actionId, event) -> {
            if (input.isPopupShowing()) {
                input.performCompletion();
                return true;
            }
            return false;
        });
    }

    private void refreshAutocomplete(EditText input) {
        if (input instanceof AutoCompleteTextView) {
            installAutoComplete((AutoCompleteTextView) input);
        }
    }

    private String suggestionKindForHint(CharSequence hintValue) {
        String hint = String.valueOf(hintValue == null ? "" : hintValue).toLowerCase(Locale.ROOT);
        if (hint.contains("kwota") || hint.contains("saldo") || hint.contains("limit")
                || hint.contains("rrrr") || hint.contains("data") || hint.contains("termin")
                || hint.contains("adres") || hint.contains("http") || hint.contains("od, np.")
                || hint.contains("do, np.") || hint.matches(".*\\b[0-9]+\\b.*")) {
            return null;
        }
        if (hint.contains("szczeg")) {
            return "details";
        }
        if (hint.contains("produk")) {
            return "product";
        }
        if (hint.contains("ilość") || hint.contains("ilosc")) {
            return "quantity";
        }
        if (hint.contains("sklep")) {
            return "shop";
        }
        if (hint.contains("źród") || hint.contains("zrod")) {
            return "source";
        }
        if (hint.contains("kategoria")) {
            return "category";
        }
        if (hint.contains("cel")) {
            return "goal";
        }
        if (hint.contains("dłuż") || hint.contains("dluz") || hint.contains("wiszę") || hint.contains("wisze")) {
            return "debt";
        }
        if (hint.contains("konto")) {
            return "account";
        }
        if (hint.contains("lista")) {
            return "shopping_list";
        }
        if (hint.contains("opis")) {
            return "description";
        }
        if (hint.contains("nazwa")) {
            return "name";
        }
        return "description";
    }

    private static class NewlineTokenizer implements MultiAutoCompleteTextView.Tokenizer {
        @Override
        public int findTokenStart(CharSequence text, int cursor) {
            int i = cursor;
            while (i > 0 && text.charAt(i - 1) != '\n') {
                i--;
            }
            while (i < cursor && Character.isWhitespace(text.charAt(i)) && text.charAt(i) != '\n') {
                i++;
            }
            return i;
        }

        @Override
        public int findTokenEnd(CharSequence text, int cursor) {
            int i = cursor;
            int len = text.length();
            while (i < len && text.charAt(i) != '\n') {
                i++;
            }
            return i;
        }

        @Override
        public CharSequence terminateToken(CharSequence text) {
            return String.valueOf(text).trim() + "\n";
        }
    }

    private void styleTextInput(EditText input) {
        input.setTextColor(TEXT);
        input.setHintTextColor(MUTED);
        input.setSingleLine(false);
        input.setTextSize(16);
        input.setMinHeight(dp(52));
        input.setPadding(dp(12), dp(10), dp(12), dp(10));
        input.setBackground(outline(BORDER));
        input.setOnFocusChangeListener((view, hasFocus) -> {
            if (hasFocus) {
                ensureFieldVisible(view);
            }
        });
        input.setOnClickListener(this::ensureFieldVisible);
    }

    private void configureAmountInput(EditText input, boolean signed) {
        if (input instanceof AutoCompleteTextView) {
            ((AutoCompleteTextView) input).setAdapter(null);
        }
        input.setSingleLine(true);
        input.setKeyListener(DigitsKeyListener.getInstance(signed ? "0123456789.,-" : "0123456789.,"));
        int inputType = InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL;
        if (signed) {
            inputType |= InputType.TYPE_NUMBER_FLAG_SIGNED;
        }
        input.setRawInputType(inputType);
        input.setImeOptions(EditorInfo.IME_ACTION_DONE);
    }

    private void ensureFieldVisible(View view) {
        if (scroll == null || view == null) {
            return;
        }
        ensureFieldVisibleDelayed(view, 80);
        ensureFieldVisibleDelayed(view, 260);
        ensureFieldVisibleDelayed(view, 560);
    }

    private void ensureFieldVisibleDelayed(View view, long delayMs) {
        scroll.postDelayed(() -> {
            int[] scrollLoc = new int[2];
            int[] viewLoc = new int[2];
            scroll.getLocationOnScreen(scrollLoc);
            view.getLocationOnScreen(viewLoc);
            int visibleBottom = scrollLoc[1] + scroll.getHeight() - dp(28);
            int viewBottom = viewLoc[1] + view.getHeight();
            if (viewBottom > visibleBottom) {
                scroll.smoothScrollBy(0, viewBottom - visibleBottom + dp(12));
            }
        }, delayMs);
    }

    private Button actionButton(String value, int color, View.OnClickListener listener) {
        Button button = button(value, color);
        button.setOnClickListener(listener);
        return button;
    }

    private Button button(String value, int color) {
        Button button = new Button(this);
        button.setText(value);
        button.setAllCaps(false);
        button.setTextColor(color);
        button.setTextSize(15);
        button.setMinHeight(dp(48));
        button.setPadding(dp(12), dp(4), dp(12), dp(4));
        button.setBackground(outline(color));
        button.setOnTouchListener((v, event) -> {
            if (event.getActionMasked() == MotionEvent.ACTION_DOWN) {
                v.animate().scaleX(0.985f).scaleY(0.985f).setDuration(80).start();
            } else if (event.getActionMasked() == MotionEvent.ACTION_UP
                    || event.getActionMasked() == MotionEvent.ACTION_CANCEL) {
                v.animate().scaleX(1.0f).scaleY(1.0f).setDuration(140)
                        .setInterpolator(new DecelerateInterpolator(1.8f))
                        .start();
            }
            return false;
        });
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            button.setElevation(dp(1));
        }
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(dp(6), dp(10), dp(6), dp(4));
        button.setLayoutParams(params);
        return button;
    }

    private Button smallButton(String value, int color) {
        Button button = button(value, color);
        button.setMinHeight(dp(42));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(dp(4), dp(5), dp(4), dp(5));
        button.setLayoutParams(params);
        return button;
    }

    private GradientDrawable outline(int color) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(Color.TRANSPARENT);
        drawable.setCornerRadius(dp(6));
        drawable.setStroke(dp(2), color);
        return drawable;
    }

    private GradientDrawable fill(int color, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(radius);
        return drawable;
    }

    private Spinner spinner(List<String> values) {
        Spinner spinner = new Spinner(this);
        setSpinnerValues(spinner, values);
        spinner.setPadding(0, 0, 0, dp(6));
        return spinner;
    }

    private void setSpinnerValues(Spinner spinner, List<String> values) {
        if (values == null || values.isEmpty()) {
            values = list("");
        }
        ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, android.R.layout.simple_spinner_item, values) {
            @Override
            public View getView(int position, View convertView, ViewGroup parent) {
                TextView view = (TextView) super.getView(position, convertView, parent);
                styleSpinnerText(view, false);
                return view;
            }

            @Override
            public View getDropDownView(int position, View convertView, ViewGroup parent) {
                TextView view = (TextView) super.getDropDownView(position, convertView, parent);
                styleSpinnerText(view, true);
                return view;
            }
        };
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);
        spinner.setMinimumHeight(dp(54));
        spinner.setPadding(dp(8), 0, dp(8), 0);
        spinner.setBackground(outline(BORDER));
        spinner.setDropDownVerticalOffset(dp(4));
    }

    private void styleSpinnerText(TextView view, boolean dropdown) {
        view.setTextColor(TEXT);
        view.setTextSize(dropdown ? 17 : 16);
        view.setSingleLine(false);
        view.setGravity(Gravity.CENTER_VERTICAL);
        view.setPadding(dp(10), dp(dropdown ? 12 : 8), dp(10), dp(dropdown ? 12 : 8));
    }

    private Spinner accountSpinner() {
        List<String> names = new ArrayList<>();
        for (Account acc : db.getAccounts()) {
            names.add(acc.name);
        }
        return spinner(names);
    }

    private Account selectedAccount(Spinner spinner) {
        Object item = spinner.getSelectedItem();
        if (item != null) {
            String raw = item.toString();
            for (Account acc : db.getAccounts()) {
                if (acc.name.equals(raw)) {
                    return acc;
                }
            }
            int sep = raw.indexOf('|');
            if (sep > 0) {
                try {
                    Account acc = db.accountById(Long.parseLong(raw.substring(0, sep).trim()));
                    if (acc != null) {
                        return acc;
                    }
                } catch (NumberFormatException ignored) {
                }
            }
        }
        return firstAccount();
    }

    private void selectSpinnerValue(Spinner spinner, String value) {
        if (spinner == null || value == null) {
            return;
        }
        for (int i = 0; i < spinner.getCount(); i++) {
            if (value.equals(spinner.getItemAtPosition(i).toString())) {
                spinner.setSelection(i);
                return;
            }
        }
    }

    private Account firstAccount() {
        List<Account> accounts = db.getAccounts();
        if (accounts.isEmpty()) {
            db.ensureDefaults();
            accounts = db.getAccounts();
        }
        return accounts.get(0);
    }

    private void selectAccount(Spinner spinner, long id) {
        Account account = db.accountById(id);
        for (int i = 0; i < spinner.getCount(); i++) {
            String raw = spinner.getItemAtPosition(i).toString();
            if ((account != null && raw.equals(account.name)) || raw.startsWith(id + " |")) {
                spinner.setSelection(i);
                return;
            }
        }
    }

    private void attachDatePicker(EditText input) {
        input.setSingleLine(true);
        input.setInputType(InputType.TYPE_NULL);
        input.setFocusable(false);
        input.setOnClickListener(v -> {
            Calendar cal = calendarFrom(input.getText().toString().trim());
            new DatePickerDialog(this, (view, year, month, dayOfMonth) ->
                    input.setText(String.format(Locale.ROOT, "%04d-%02d-%02d", year, month + 1, dayOfMonth)),
                    cal.get(Calendar.YEAR), cal.get(Calendar.MONTH), cal.get(Calendar.DAY_OF_MONTH)).show();
        });
    }

    private void changeMonth(int delta) {
        currentMonth += delta;
        if (currentMonth < 1) {
            currentMonth = 12;
            currentYear--;
        } else if (currentMonth > 12) {
            currentMonth = 1;
            currentYear++;
        }
    }

    private String monthPrefix() {
        return String.format(Locale.ROOT, "%04d-%02d", currentYear, currentMonth);
    }

    private String monthTitle() {
        String[] months = {"Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"};
        return months[currentMonth - 1] + " " + currentYear;
    }

    private String today() {
        return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(new Date());
    }

    private String endOfMonth() {
        Calendar cal = Calendar.getInstance();
        cal.set(Calendar.YEAR, currentYear);
        cal.set(Calendar.MONTH, currentMonth - 1);
        cal.set(Calendar.DAY_OF_MONTH, cal.getActualMaximum(Calendar.DAY_OF_MONTH));
        return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(cal.getTime());
    }

    private String addMonths(String date, int months) {
        Calendar cal = calendarFrom(date);
        cal.add(Calendar.MONTH, months);
        return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(cal.getTime());
    }

    private Calendar calendarFrom(String date) {
        Calendar cal = Calendar.getInstance();
        try {
            Date parsed = new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).parse(date);
            if (parsed != null) {
                cal.setTime(parsed);
            }
        } catch (ParseException ignored) {
        }
        return cal;
    }

    private boolean isDate(String date) {
        if (date == null || !date.matches("\\d{4}-\\d{2}-\\d{2}")) {
            return false;
        }
        try {
            SimpleDateFormat fmt = new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT);
            fmt.setLenient(false);
            fmt.parse(date);
            return true;
        } catch (ParseException ex) {
            return false;
        }
    }

    private long daysBetween(Calendar start, Calendar end) {
        Calendar a = (Calendar) start.clone();
        Calendar b = (Calendar) end.clone();
        a.set(Calendar.HOUR_OF_DAY, 0); a.set(Calendar.MINUTE, 0); a.set(Calendar.SECOND, 0); a.set(Calendar.MILLISECOND, 0);
        b.set(Calendar.HOUR_OF_DAY, 0); b.set(Calendar.MINUTE, 0); b.set(Calendar.SECOND, 0); b.set(Calendar.MILLISECOND, 0);
        return (b.getTimeInMillis() - a.getTimeInMillis()) / (24L * 60L * 60L * 1000L);
    }

    private double parseAmount(String raw) {
        try {
            return Double.parseDouble(String.valueOf(raw).trim().replace(",", "."));
        } catch (Exception ex) {
            return 0.0;
        }
    }

    private String money(double value) {
        return String.format(Locale.ROOT, "%.2f zł", value);
    }

    private String formatRaw(double value) {
        return String.format(Locale.ROOT, "%.2f", value);
    }

    private List<String> list(String... values) {
        List<String> list = new ArrayList<>();
        Collections.addAll(list, values);
        return list;
    }

    private void addToMap(Map<String, Double> map, String key, double value) {
        String safe = key == null || key.isEmpty() ? "Inne" : key;
        map.put(safe, map.getOrDefault(safe, 0.0) + value);
    }

    private void addToListMap(Map<String, List<Tx>> map, String key, Tx value) {
        String safe = key == null || key.isEmpty() ? "Inne" : key;
        if (!map.containsKey(safe)) {
            map.put(safe, new ArrayList<>());
        }
        map.get(safe).add(value);
    }

    private int compareTransactionsBySyncOrder(Tx a, Tx b) {
        int byOrder = transactionOrderKey(a).compareTo(transactionOrderKey(b));
        return byOrder != 0 ? byOrder : Long.compare(a.id, b.id);
    }

    private String transactionOrderKey(Tx tx) {
        if (tx != null && tx.syncOrder != null && !tx.syncOrder.trim().isEmpty()) {
            return tx.syncOrder.trim();
        }
        String date = tx == null || tx.date == null || tx.date.trim().isEmpty() ? "1970-01-01" : tx.date.trim();
        long id = tx == null ? 0 : tx.id;
        return date + "T00:00:00.000|android-legacy|" + String.format(Locale.ROOT, "%012d", id);
    }

    private String safeLabel(String value) {
        return value == null || value.trim().isEmpty() ? "Inne" : value;
    }

    private void scheduleTransactionSearchRefresh() {
        if (!"transactions".equals(currentScreen) || transactionListContainer == null) {
            return;
        }
        if (searchRunnable != null) {
            uiHandler.removeCallbacks(searchRunnable);
        }
        searchRunnable = this::addTransactionList;
        uiHandler.postDelayed(searchRunnable, 250);
    }

    private String weekStart(String date) {
        Calendar cal = calendarFrom(date);
        int day = cal.get(Calendar.DAY_OF_WEEK);
        int delta = day == Calendar.SUNDAY ? -6 : Calendar.MONDAY - day;
        cal.add(Calendar.DAY_OF_MONTH, delta);
        return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(cal.getTime());
    }

    private String addDays(String date, int days) {
        Calendar cal = calendarFrom(date);
        cal.add(Calendar.DAY_OF_MONTH, days);
        return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(cal.getTime());
    }

    private List<String> goalNames() {
        List<String> names = new ArrayList<>();
        for (Goal goal : db.getGoals()) {
            names.add(goal.name);
        }
        return names;
    }

    private Goal selectedGoalByName(String name) {
        for (Goal goal : db.getGoals()) {
            if (goal.name.equals(name)) {
                return goal;
            }
        }
        return null;
    }

    private List<String> savingsBuckets() {
        List<String> names = new ArrayList<>();
        names.add("Oszczędności");
        names.addAll(goalNames());
        return names;
    }

    private List<String> debtNames(List<Debt> debts, boolean onlyActive) {
        List<String> names = new ArrayList<>();
        for (Debt debt : debts) {
            double remaining = debt.remaining();
            if (!onlyActive || remaining > 0.01) {
                names.add(debt.name + " (" + money(remaining) + ")");
            }
        }
        return names;
    }

    private Debt selectedDebtFromLabel(List<Debt> debts, String label) {
        for (Debt debt : debts) {
            if (label != null && label.startsWith(debt.name + " (")) {
                return debt;
            }
        }
        return null;
    }

    private int transactionAmountColor(Tx tx) {
        if ("income".equals(tx.type) || "debtor_repayment".equals(tx.type)) {
            return GREEN;
        }
        if ("expense".equals(tx.type) || "liability_repayment".equals(tx.type)) {
            return RED;
        }
        if ("goal_deposit".equals(tx.type)) {
            return tx.amount >= 0 ? RED : GREEN;
        }
        return BLUE;
    }

    private void scheduleAfterFinancialChange(String type) {
        if ("expense".equals(type)
                || "liability_repayment".equals(type)
                || "income".equals(type)
                || "debtor_repayment".equals(type)) {
            BudgetReminderReceiver.scheduleAfterTransaction(this, type);
            BudgetReminderReceiver.refreshTasks(this);
        }
    }

    private String typeLabel(String type) {
        Map<String, String> labels = new HashMap<>();
        labels.put("income", "Wpływ");
        labels.put("expense", "Wydatek");
        labels.put("savings", "Oszczędności");
        labels.put("savings_migration", "Transfer");
        labels.put("account_transfer", "Migracja kasy");
        labels.put("goal_deposit", "Cel");
        labels.put("liability_repayment", "Spłata długu");
        labels.put("debtor_repayment", "Zwrot");
        return labels.getOrDefault(type, type);
    }

    private int parseColor(String raw, int fallback) {
        try {
            int color = Color.parseColor(raw);

            // jeżeli kolor jest prawie biały, użyj domyślnego
            if (Color.red(color) > 240 &&
                Color.green(color) > 240 &&
                Color.blue(color) > 240) {
                return fallback;
            }

            return color;
        } catch (Exception ex) {
            return fallback;
        }
    }

    private String safeName(String name) {
        return String.valueOf(name == null ? "plik" : name).replace("/", "_").replace("\\", "_").trim();
    }

    private String humanSize(long bytes) {
        if (bytes < 1024) {
            return bytes + " B";
        }
        if (bytes < 1024 * 1024) {
            return String.format(Locale.ROOT, "%.1f KB", bytes / 1024.0);
        }
        return String.format(Locale.ROOT, "%.1f MB", bytes / 1024.0 / 1024.0);
    }

    private MessageDigest sha256Digest() throws IOException {
        try {
            return MessageDigest.getInstance("SHA-256");
        } catch (Exception ex) {
            throw new IOException("Brak SHA-256", ex);
        }
    }

    private String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            out.append(String.format(Locale.ROOT, "%02x", b & 0xff));
        }
        return out.toString();
    }

    private String defaultShoppingListName() {
        return new SimpleDateFormat("dd.MM.yyyy", Locale.ROOT).format(new Date()) + " zakupy";
    }

    private int getStatusBarHeight() {
        int id = getResources().getIdentifier("status_bar_height", "dimen", "android");
        int base = id > 0 ? getResources().getDimensionPixelSize(id) : 0;
        return base + dp(8);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }

    private SharedPreferences prefs() {
        return getSharedPreferences(PREFS, MODE_PRIVATE);
    }

    private boolean looksLikeZip(File file) throws IOException {
        try (InputStream in = new FileInputStream(file)) {
            return in.read() == 'P' && in.read() == 'K';
        }
    }

    private void zipFile(ZipOutputStream zip, File file, String name) throws IOException {
        if (file == null || !file.isFile()) {
            return;
        }
        zip.putNextEntry(new ZipEntry(name));
        try (InputStream in = new FileInputStream(file)) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) {
                zip.write(buffer, 0, read);
            }
        }
        zip.closeEntry();
    }

    private void zipDirectory(ZipOutputStream zip, File dir, String prefix) throws IOException {
        if (dir == null || !dir.isDirectory()) {
            return;
        }
        File[] files = dir.listFiles();
        if (files == null) {
            return;
        }
        for (File file : files) {
            if (file.isDirectory()) {
                zipDirectory(zip, file, prefix + file.getName() + "/");
            } else {
                zipFile(zip, file, prefix + file.getName());
            }
        }
    }

    private File safeZipTarget(File base, String name) throws IOException {
        File target = new File(base, name);
        String basePath = base.getCanonicalPath() + File.separator;
        String targetPath = target.getCanonicalPath();
        if (!targetPath.startsWith(basePath)) {
            throw new IOException("Nieprawidłowy wpis ZIP");
        }
        return target;
    }

    private void copyFile(File src, File dst) throws IOException {
        File parent = dst.getParentFile();
        if (parent != null) {
            parent.mkdirs();
        }
        try (InputStream in = new FileInputStream(src);
             OutputStream out = new FileOutputStream(dst)) {
            copyStream(in, out);
        }
    }

    private void copyFile(File src, OutputStream out) throws IOException {
        try (InputStream in = new FileInputStream(src)) {
            copyStream(in, out);
        }
    }

    private void copyStream(InputStream in, OutputStream out) throws IOException {
        byte[] buffer = new byte[8192];
        int read;
        while ((read = in.read(buffer)) != -1) {
            out.write(buffer, 0, read);
        }
        out.flush();
    }

    private void copyDirectory(File src, File dst) throws IOException {
        if (!src.isDirectory()) {
            return;
        }
        if (!dst.exists()) {
            dst.mkdirs();
        }
        File[] files = src.listFiles();
        if (files == null) {
            return;
        }
        for (File file : files) {
            File target = new File(dst, file.getName());
            if (file.isDirectory()) {
                copyDirectory(file, target);
            } else {
                copyFile(file, target);
            }
        }
    }

    private void deleteRecursively(File file) {
        if (file == null || !file.exists()) {
            return;
        }
        if (file.isDirectory()) {
            File[] children = file.listFiles();
            if (children != null) {
                for (File child : children) {
                    deleteRecursively(child);
                }
            }
        }
        file.delete();
    }

    private String extensionForAttachment(File file) {
        try (InputStream in = new FileInputStream(file)) {
            byte[] header = new byte[8];
            int read = in.read(header);
            if (read >= 4 && header[0] == (byte) 0xff && header[1] == (byte) 0xd8) {
                return ".jpg";
            }
            if (read >= 4 && header[0] == (byte) 0x89 && header[1] == 0x50 && header[2] == 0x4e && header[3] == 0x47) {
                return ".png";
            }
            if (read >= 4 && header[0] == 0x25 && header[1] == 0x50 && header[2] == 0x44 && header[3] == 0x46) {
                return ".pdf";
            }
        } catch (IOException ignored) {
        }
        return ".dat";
    }

    private interface AmountCallback {
        void onAmount(double amount, String details, long accountId);
    }

    private interface StreamWriter {
        void write(OutputStream out) throws IOException;
    }

    private static class AttachmentDraft {
        final String name;
        final String mime;
        final byte[] data;

        AttachmentDraft(String name, String mime, byte[] data) {
            this.name = name;
            this.mime = mime;
            this.data = data;
        }
    }

    private static class Account {
        long id;
        String name;
        double initialBalance;
        String color;
    }

    private static class Tx {
        long id;
        String date;
        String type;
        String category;
        String subcategory;
        double amount;
        String details;
        String attachment;
        boolean hasAttachment;
        long accountId;
        Long refId;
        int exclude;
        String syncId;
        String updatedAt;
        String syncOrder;
    }

    private static class Goal {
        long id;
        String name;
        double target;
        long defaultAccountId;
    }

    private static class Debt {
        long id;
        String name;
        double total;
        double paid;
        String deadline;

        double remaining() {
            return total - paid;
        }
    }

    private static class Bill {
        long id;
        String dueDate;
        double amount;
        String category;
        String description;
        boolean recurring;
        Long refId;
    }

    private static class ShoppingListData {
        long id;
        String name;
        String createdAt;
        String status;
    }

    private static class ShoppingItem {
        long id;
        String product;
        String quantity;
        String store;
        boolean checked;
    }

    private static class SyncResult {
        int inserted;
        int updated;
        int deleted;
        int attachmentsDownloaded;
        int attachmentErrors;
    }

    private static class ImportRow {
        final int change;
        final long localId;

        ImportRow(int change, long localId) {
            this.change = change;
            this.localId = localId;
        }
    }

    private static class BudgetDb {
        final Activity activity;
        final File dbFile;
        final File attachmentsDir;
        SQLiteDatabase conn;

        BudgetDb(Activity activity) {
            this.activity = activity;
            dbFile = new File(activity.getFilesDir(), "budzet.db");
            attachmentsDir = new File(activity.getFilesDir(), "attachments");
        }

        void open() {
            attachmentsDir.mkdirs();
            conn = SQLiteDatabase.openOrCreateDatabase(dbFile, null);
            createTables();
            ensureDefaults();
            normalizeImportedData();
        }

        void close() {
            if (conn != null && conn.isOpen()) {
                conn.close();
            }
        }

        void checkpoint() {
            try {
                conn.rawQuery("PRAGMA wal_checkpoint(FULL)", null).close();
            } catch (Exception ignored) {
            }
        }

        void createTables() {
            conn.execSQL("CREATE TABLE IF NOT EXISTS transactions (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, type TEXT, category TEXT, subcategory TEXT, " +
                    "amount REAL, currency TEXT, exchange_rate REAL, exclude_from_weekly INTEGER DEFAULT 0, " +
                    "details TEXT DEFAULT '', attachment TEXT, ref_id INTEGER, account_id INTEGER, " +
                    "sync_id TEXT UNIQUE, updated_at TEXT, sync_order TEXT)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS people (name TEXT PRIMARY KEY)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS month_locks (month_str TEXT PRIMARY KEY)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS categories (name TEXT PRIMARY KEY)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, target_amount REAL, default_account_id INTEGER)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS liabilities (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, total_amount REAL, deadline TEXT, attachment TEXT, sync_id TEXT, updated_at TEXT)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS debtors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, total_amount REAL, deadline TEXT, attachment TEXT, sync_id TEXT, updated_at TEXT)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS app_config (key TEXT PRIMARY KEY, value TEXT)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS sync_deletions (" +
                    "table_name TEXT NOT NULL, sync_id TEXT NOT NULL, deleted_at TEXT NOT NULL, " +
                    "PRIMARY KEY (table_name, sync_id))");
            conn.execSQL("CREATE TABLE IF NOT EXISTS mobile_imports (mobile_id TEXT PRIMARY KEY, transaction_id INTEGER, source_file TEXT, source_device TEXT, imported_at TEXT)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS shopping_lists (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, created_at TEXT, status TEXT DEFAULT 'open', sync_id TEXT, updated_at TEXT)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS shopping_items (id INTEGER PRIMARY KEY AUTOINCREMENT, list_id INTEGER, product_name TEXT, quantity TEXT, store TEXT DEFAULT '', is_checked INTEGER DEFAULT 0, sync_id TEXT, updated_at TEXT)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS shops (name TEXT PRIMARY KEY)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS products (name TEXT PRIMARY KEY)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS weekly_history (monday_date TEXT PRIMARY KEY, amount REAL, categories TEXT)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS pending_bills (id INTEGER PRIMARY KEY AUTOINCREMENT, due_date TEXT, amount REAL, category TEXT, description TEXT, is_paid INTEGER DEFAULT 0, is_recurring INTEGER DEFAULT 0, ref_id INTEGER, sync_id TEXT, updated_at TEXT)");
            conn.execSQL("CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, initial_balance REAL DEFAULT 0.0, color TEXT DEFAULT '#7f8c8d')");
            conn.execSQL("CREATE TABLE IF NOT EXISTS modules (module_name TEXT PRIMARY KEY, is_enabled INTEGER DEFAULT 1)");

            migrate("transactions", "exclude_from_weekly", "INTEGER DEFAULT 0");
            migrate("transactions", "details", "TEXT DEFAULT ''");
            migrate("transactions", "attachment", "TEXT");
            migrate("transactions", "ref_id", "INTEGER");
            migrate("transactions", "account_id", "INTEGER");
            migrate("transactions", "sync_id", "TEXT");
            migrate("transactions", "updated_at", "TEXT");
            migrate("transactions", "sync_order", "TEXT");
            migrate("goals", "default_account_id", "INTEGER");
            migrate("accounts", "color", "TEXT DEFAULT '#7f8c8d'");
            migrate("liabilities", "attachment", "TEXT");
            migrate("liabilities", "sync_id", "TEXT");
            migrate("liabilities", "updated_at", "TEXT");
            migrate("debtors", "attachment", "TEXT");
            migrate("debtors", "sync_id", "TEXT");
            migrate("debtors", "updated_at", "TEXT");
            migrate("shopping_items", "store", "TEXT DEFAULT ''");
            migrate("shopping_items", "is_checked", "INTEGER DEFAULT 0");
            migrate("shopping_lists", "sync_id", "TEXT");
            migrate("shopping_lists", "updated_at", "TEXT");
            migrate("shopping_items", "sync_id", "TEXT");
            migrate("shopping_items", "updated_at", "TEXT");
            migrate("pending_bills", "is_recurring", "INTEGER DEFAULT 0");
            migrate("pending_bills", "ref_id", "INTEGER");
            migrate("pending_bills", "sync_id", "TEXT");
            migrate("pending_bills", "updated_at", "TEXT");

            // =================================================================================
            // --- NOWE: AUTOMATYCZNE GENEROWANIE METADANYCH SYNCHRONIZACJI (ANDROID) ---
            // =================================================================================

            // 1. Trigger dla NOWYCH wpisów - sam generuje losowy UUID (sync_id) oraz aktualny czas z milisekundami
            conn.execSQL("CREATE TRIGGER IF NOT EXISTS tx_bi_sync_metadata " +
                    "AFTER INSERT ON transactions " +
                    "FOR EACH ROW " +
                    "BEGIN " +
                    "    UPDATE transactions " +
                    "    SET " +
                    "        sync_id = CASE " +
                    "            WHEN (NEW.sync_id IS NULL OR NEW.sync_id = '') " +
                    "            THEN (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))) " +
                    "            ELSE NEW.sync_id " +
                    "        END, " +
                    "        updated_at = CASE " +
                    "            WHEN (NEW.updated_at IS NULL OR NEW.updated_at = '') " +
                    "            THEN strftime('%Y-%m-%d %H:%M:%f', 'now') " +
                    "            ELSE NEW.updated_at " +
                    "        END " +
                    "    WHERE id = NEW.id; " +
                    "END;");

            conn.execSQL("DROP TRIGGER IF EXISTS tx_bu_sync_metadata");

            // 2. Trigger dla EDYCJI - zachowuje importowany czas, a lokalne ręczne zmiany i tak ustawiają updated_at w kodzie
            conn.execSQL("CREATE TRIGGER IF NOT EXISTS tx_bu_sync_metadata " +
                    "AFTER UPDATE ON transactions " +
                    "FOR EACH ROW " +
                    "WHEN NEW.updated_at = OLD.updated_at AND (" +
                    "NEW.date IS NOT OLD.date OR NEW.type IS NOT OLD.type OR NEW.category IS NOT OLD.category OR " +
                    "NEW.subcategory IS NOT OLD.subcategory OR NEW.amount IS NOT OLD.amount OR " +
                    "NEW.details IS NOT OLD.details OR NEW.account_id IS NOT OLD.account_id OR " +
                    "NEW.exclude_from_weekly IS NOT OLD.exclude_from_weekly OR NEW.ref_id IS NOT OLD.ref_id" +
                    ") " +
                    "BEGIN " +
                    "    UPDATE transactions " +
                    "    SET updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now') " +
                    "    WHERE id = NEW.id; " +
                    "END;");

            // 3. Jednorazowa naprawa starych rekordów na telefonie, które mają pusty sync_id (zapobiega nadpisywaniu)
            conn.execSQL("UPDATE transactions " +
                    "SET sync_id = (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))) " +
                    "WHERE sync_id IS NULL OR sync_id = '';");

            // 4. Jednorazowa naprawa starych rekordów na telefonie, które nie mają zapisanego czasu modyfikacji
            conn.execSQL("UPDATE transactions " +
                    "SET updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now') " +
                    "WHERE updated_at IS NULL OR updated_at = '';");

            conn.execSQL("UPDATE transactions " +
                    "SET sync_order = IFNULL(date, '1970-01-01') || 'T00:00:00.000|android-legacy|' || printf('%012d', id) " +
                    "WHERE sync_order IS NULL OR sync_order = '';");
            ensureAuxSyncMetadata();
        }


        void migrate(String table, String col, String def) {
            try {
                conn.execSQL("ALTER TABLE " + table + " ADD COLUMN " + col + " " + def);
            } catch (Exception ignored) {
            }
        }

        void ensureDefaults() {
            exec("INSERT OR IGNORE INTO people VALUES (?)", "Mąż");
            exec("INSERT OR IGNORE INTO people VALUES (?)", "Żona");
            for (String c : new String[]{"Zakupy", "Remonty", "Spłata Długu", "Samochód", "Ciuchy", "Opłaty", "Rozrywka", "Inne", "Zdrowie", "Pożyczki"}) {
                exec("INSERT OR IGNORE INTO categories VALUES (?)", c);
            }
            for (String s : new String[]{"Biedronka", "Dino", "Lidl", "Polo", "Kaufland", "Apteka", "Rossmann", "Pepco"}) {
                exec("INSERT OR IGNORE INTO shops VALUES (?)", s);
            }
            exec("INSERT OR IGNORE INTO accounts (id, name, initial_balance, color) VALUES (1, 'Gotówka', 0.0, '#27ae60')");
            exec("INSERT OR IGNORE INTO modules VALUES ('shopping_list', 1)");
            exec("INSERT OR IGNORE INTO modules VALUES ('weekly_limit', 1)");
            if (getConfig("weekly_limit_config") == null) {
                saveWeeklyConfig(false, 500.0, getCategories());
            }
        }

        void normalizeImportedData() {
            exec("UPDATE transactions SET account_id = 1 " +
                    "WHERE account_id IS NULL " +
                    "OR TRIM(CAST(account_id AS TEXT)) = '' " +
                    "OR CAST(account_id AS INTEGER) <= 0 " +
                    "OR CAST(account_id AS INTEGER) NOT IN (SELECT id FROM accounts)");
            exec("UPDATE transactions SET ref_id = (SELECT id FROM liabilities WHERE liabilities.name = transactions.subcategory LIMIT 1) " +
                    "WHERE type = 'liability_repayment' AND ref_id IS NULL");
            exec("UPDATE transactions SET ref_id = (SELECT id FROM debtors WHERE debtors.name = transactions.subcategory LIMIT 1) " +
                    "WHERE type = 'debtor_repayment' AND ref_id IS NULL");
            ensureTransactionSyncMetadata();
            ensureAuxSyncMetadata();
        }

        void ensureTransactionSyncMetadata() {
            String now = timestamp();
            try (Cursor c = conn.rawQuery("SELECT id FROM transactions WHERE sync_id IS NULL OR TRIM(sync_id)=''", null)) {
                while (c.moveToNext()) {
                    ContentValues values = new ContentValues();
                    values.put("sync_id", UUID.randomUUID().toString());
                    values.put("updated_at", now);
                    conn.update("transactions", values, "id=?", new String[]{String.valueOf(c.getLong(0))});
                }
            }
            ContentValues values = new ContentValues();
            values.put("updated_at", now);
            conn.update("transactions", values, "updated_at IS NULL OR TRIM(updated_at)=''", null);
            try (Cursor c = conn.rawQuery("SELECT id, IFNULL(date,''), IFNULL(updated_at,'') FROM transactions WHERE sync_order IS NULL OR TRIM(sync_order)=''", null)) {
                while (c.moveToNext()) {
                    ContentValues orderValues = new ContentValues();
                    String base = c.getString(2);
                    base = (c.getString(1) == null || c.getString(1).isEmpty() ? "1970-01-01" : c.getString(1)) + "T00:00:00.000";
                    orderValues.put("sync_order", base + "|android-legacy|" + String.format(Locale.ROOT, "%012d", c.getLong(0)));
                    conn.update("transactions", orderValues, "id=?", new String[]{String.valueOf(c.getLong(0))});
                }
            }
        }

        void ensureAuxSyncMetadata() {
            for (String table : new String[]{"pending_bills", "shopping_lists", "shopping_items", "liabilities", "debtors"}) {
                String now = timestamp();
                try (Cursor c = conn.rawQuery("SELECT id FROM " + table + " WHERE sync_id IS NULL OR TRIM(sync_id)=''", null)) {
                    while (c.moveToNext()) {
                        ContentValues values = new ContentValues();
                        values.put("sync_id", UUID.randomUUID().toString());
                        values.put("updated_at", now);
                        conn.update(table, values, "id=?", new String[]{String.valueOf(c.getLong(0))});
                    }
                } catch (Exception ignored) {
                }
                ContentValues values = new ContentValues();
                values.put("updated_at", now);
                try {
                    conn.update(table, values, "updated_at IS NULL OR TRIM(updated_at)=''", null);
                } catch (Exception ignored) {
                }
            }
        }

        void exec(String sql, Object... args) {
            conn.execSQL(sql, args);
        }

        String getConfig(String key) {
            try (Cursor c = conn.rawQuery("SELECT value FROM app_config WHERE key=?", new String[]{key})) {
                return c.moveToFirst() ? c.getString(0) : null;
            }
        }

        void setConfig(String key, String value) {
            exec("INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)", key, value);
        }

        void saveWeeklyConfig(boolean enabled, double amount, List<String> categories) {
            try {
                JSONObject obj = new JSONObject();
                obj.put("enabled", enabled);
                obj.put("amount", amount);
                JSONArray arr = new JSONArray();
                for (String c : categories) {
                    arr.put(c);
                }
                obj.put("categories", arr);
                setConfig("weekly_limit_config", obj.toString());
            } catch (JSONException ignored) {
            }
        }

        boolean isWeeklyEnabled() {
            try {
                String raw = getConfig("weekly_limit_config");
                return raw != null && new JSONObject(raw).optBoolean("enabled", false);
            } catch (JSONException ex) {
                return false;
            }
        }

        double weeklyAmount() {
            try {
                String raw = getConfig("weekly_limit_config");
                return raw == null ? 500.0 : new JSONObject(raw).optDouble("amount", 500.0);
            } catch (JSONException ex) {
                return 500.0;
            }
        }

        List<String> weeklyCategories() {
            List<String> out = new ArrayList<>();
            try {
                String raw = getConfig("weekly_limit_config");
                if (raw == null) {
                    return null;
                }
                JSONArray arr = new JSONObject(raw).optJSONArray("categories");
                if (arr == null) {
                    return null;
                }
                for (int i = 0; i < arr.length(); i++) {
                    out.add(arr.optString(i));
                }
                return out;
            } catch (JSONException ex) {
                return null;
            }
        }

        Map<String, Double> weeklySpendingByCategory(String start, String end, List<String> categories) {
            Map<String, Double> out = new LinkedHashMap<>();
            StringBuilder sql = new StringBuilder("SELECT category, SUM(amount) FROM transactions " +
                    "WHERE type='expense' AND IFNULL(exclude_from_weekly,0)=0 AND date >= ? AND date <= ?");
            List<String> args = new ArrayList<>();
            args.add(start);
            args.add(end);
            if (categories != null) {
                if (categories.isEmpty()) {
                    return out;
                }
                sql.append(" AND category IN (");
                for (int i = 0; i < categories.size(); i++) {
                    if (i > 0) sql.append(",");
                    sql.append("?");
                    args.add(categories.get(i));
                }
                sql.append(")");
            }
            sql.append(" GROUP BY category ORDER BY SUM(amount) DESC");
            try (Cursor c = conn.rawQuery(sql.toString(), args.toArray(new String[0]))) {
                while (c.moveToNext()) {
                    out.put(c.getString(0), c.getDouble(1));
                }
            }
            return out;
        }

        List<String> getPeople() {
            return queryStrings("SELECT name FROM people ORDER BY name");
        }

        void addPerson(String name) {
            if (name != null && !name.trim().isEmpty()) {
                exec("INSERT OR IGNORE INTO people VALUES (?)", name.trim());
            }
        }

        List<String> getCategories() {
            return queryStrings("SELECT name FROM categories ORDER BY name");
        }

        void addCategory(String name) {
            if (name != null && !name.trim().isEmpty()) {
                exec("INSERT OR IGNORE INTO categories VALUES (?)", name.trim());
            }
        }

        List<String> queryStrings(String sql) {
            List<String> out = new ArrayList<>();
            try (Cursor c = conn.rawQuery(sql, null)) {
                while (c.moveToNext()) {
                    out.add(c.getString(0));
                }
            }
            return out;
        }

        List<String> textSuggestions(String kind) {
            Set<String> out = new LinkedHashSet<>();
            String safeKind = kind == null ? "description" : kind.trim().toLowerCase(Locale.ROOT);
            List<String> queries = new ArrayList<>();
            if ("source".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT name FROM people",
                        "SELECT DISTINCT category FROM transactions WHERE type='income'",
                        "SELECT DISTINCT subcategory FROM transactions WHERE type='income'");
            } else if ("category".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT name FROM categories",
                        "SELECT DISTINCT category FROM transactions WHERE type='expense'",
                        "SELECT DISTINCT category FROM pending_bills");
            } else if ("shop".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT name FROM shops",
                        "SELECT DISTINCT subcategory FROM transactions WHERE type='expense'",
                        "SELECT DISTINCT store FROM shopping_items");
            } else if ("details".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT DISTINCT details FROM transactions",
                        "SELECT DISTINCT product_name FROM shopping_items",
                        "SELECT DISTINCT quantity FROM shopping_items",
                        "SELECT DISTINCT description FROM pending_bills");
            } else if ("expense_details".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT DISTINCT details FROM transactions WHERE type='expense'");
            } else if ("product".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT name FROM products",
                        "SELECT DISTINCT product_name FROM shopping_items");
            } else if ("quantity".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT DISTINCT quantity FROM shopping_items");
            } else if ("goal".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT name FROM goals",
                        "SELECT DISTINCT subcategory FROM transactions WHERE type='goal_deposit'");
            } else if ("debt".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT name FROM liabilities",
                        "SELECT name FROM debtors",
                        "SELECT DISTINCT subcategory FROM transactions WHERE type IN ('liability_repayment','debtor_repayment')");
            } else if ("account".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT name FROM accounts");
            } else if ("shopping_list".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT name FROM shopping_lists");
            } else if ("name".equals(safeKind)) {
                Collections.addAll(queries,
                        "SELECT name FROM people",
                        "SELECT name FROM categories",
                        "SELECT name FROM liabilities",
                        "SELECT name FROM debtors",
                        "SELECT name FROM goals",
                        "SELECT name FROM shopping_lists");
            } else {
                Collections.addAll(queries,
                        "SELECT DISTINCT subcategory FROM transactions",
                        "SELECT DISTINCT description FROM pending_bills",
                        "SELECT name FROM shops");
            }
            for (String sql : queries) {
                try (Cursor c = conn.rawQuery(sql, null)) {
                    while (c.moveToNext()) {
                        if ("expense_details".equals(safeKind)) {
                            addLineSuggestions(out, str(c, 0));
                        } else {
                            addSuggestion(out, str(c, 0));
                        }
                    }
                } catch (Exception ignored) {
                }
            }
            List<String> values = new ArrayList<>(out);
            Collections.sort(values, String.CASE_INSENSITIVE_ORDER);
            if (values.size() > 800) {
                return new ArrayList<>(values.subList(0, 800));
            }
            return values;
        }

        void addSuggestion(Set<String> out, String value) {
            if (value == null) {
                return;
            }
            String clean = value.trim();
            if (clean.isEmpty()) {
                return;
            }
            out.add(clean);
            for (String line : clean.replace(";", "\n").split("\\r?\\n")) {
                String part = line.trim();
                if (!part.isEmpty()) {
                    out.add(part);
                }
            }
        }

        void addLineSuggestions(Set<String> out, String value) {
            if (value == null) {
                return;
            }
            for (String line : value.replace(";", "\n").split("\\r?\\n")) {
                String part = line.trim();
                if (!part.isEmpty()) {
                    out.add(part);
                }
            }
        }

        long addTransaction(String date, String type, String category, String subcategory, double amount,
                            int exclude, String details, byte[] attachment, long accountId, Long refId) {
            String filename = null;
            if (attachment != null && attachment.length > 0) {
                filename = UUID.randomUUID().toString().replace("-", "") + ".dat";
                try (OutputStream out = new FileOutputStream(new File(attachmentsDir, filename))) {
                    out.write(attachment);
                } catch (IOException ignored) {
                    filename = null;
                }
            }
            android.content.ContentValues values = new android.content.ContentValues();
            values.put("date", date);
            values.put("type", type);
            values.put("category", category);
            values.put("subcategory", subcategory);
            values.put("amount", amount);
            values.put("currency", "PLN");
            values.put("exchange_rate", 1.0);
            values.put("exclude_from_weekly", exclude);
            values.put("details", details == null ? "" : details);
            values.put("attachment", filename);
            if (refId == null) {
                values.putNull("ref_id");
            } else {
                values.put("ref_id", refId);
            }
            values.put("account_id", accountId);
            values.put("sync_id", UUID.randomUUID().toString());
            values.put("updated_at", timestamp());
            values.put("sync_order", syncOrder());
            return conn.insert("transactions", null, values);
        }

        boolean transferAccounts(long fromId, long toId, double amount, String details) {
            if (fromId == toId || amount <= 0) {
                return false;
            }
            Account from = accountById(fromId);
            Account to = accountById(toId);
            if (from == null || to == null) {
                return false;
            }
            String cleanDetails = details == null ? "" : details.trim();
            conn.beginTransaction();
            try {
                addTransaction(todayStatic(), "account_transfer", "Migracja kasy", "Wypłata techniczna",
                        -amount, 1, cleanDetails.isEmpty() ? "Przeniesiono do: " + to.name : cleanDetails,
                        null, fromId, null);
                addTransaction(todayStatic(), "account_transfer", "Migracja kasy", "Wpłata techniczna",
                        amount, 1, cleanDetails.isEmpty() ? "Pobrano z: " + from.name : cleanDetails,
                        null, toId, null);
                conn.setTransactionSuccessful();
                return true;
            } finally {
                conn.endTransaction();
            }
        }

        void updateTransaction(long id, String date, String category, String subcategory, double amount, String details,
                               long accountId, byte[] attachment) {
            android.content.ContentValues values = new android.content.ContentValues();
            values.put("date", date);
            values.put("category", category);
            values.put("subcategory", subcategory);
            values.put("amount", amount);
            values.put("details", details == null ? "" : details);
            values.put("account_id", accountId);
            if (attachment != null && attachment.length > 0) {
                String filename = UUID.randomUUID().toString().replace("-", "") + ".dat";
                try (OutputStream out = new FileOutputStream(new File(attachmentsDir, filename))) {
                    out.write(attachment);
                    String oldAttachment = attachmentForTransactionId(id);
                    if (oldAttachment != null && !oldAttachment.trim().isEmpty()) {
                        deleteAttachmentFile(oldAttachment);
                    }
                    values.put("attachment", filename);
                } catch (IOException ignored) {
                }
            }
            values.put("updated_at", timestamp());
            conn.update("transactions", values, "id=?", new String[]{String.valueOf(id)});
        }

        void deleteTransaction(long id) {
            recordSyncDeletion("transactions", id);
            try (Cursor c = conn.rawQuery("SELECT attachment FROM transactions WHERE id=?", new String[]{String.valueOf(id)})) {
                if (c.moveToFirst() && c.getString(0) != null) {
                    File file = new File(attachmentsDir, c.getString(0));
                    file.delete();
                }
            }
            conn.delete("transactions", "id=?", new String[]{String.valueOf(id)});
        }

        boolean isSyncDeletableTable(String table) {
            return "transactions".equals(table)
                    || "pending_bills".equals(table)
                    || "shopping_lists".equals(table)
                    || "shopping_items".equals(table)
                    || "liabilities".equals(table)
                    || "debtors".equals(table);
        }

        boolean upsertSyncDeletion(String table, String syncId, String deletedAt) {
            if (!isSyncDeletableTable(table) || syncId == null || syncId.trim().isEmpty()) {
                return false;
            }
            String safeDeletedAt = deletedAt == null || deletedAt.trim().isEmpty() ? timestamp() : deletedAt.trim();
            try (Cursor c = conn.rawQuery("SELECT deleted_at FROM sync_deletions WHERE table_name=? AND sync_id=?",
                    new String[]{table, syncId.trim()})) {
                if (c.moveToFirst() && str(c, 0).compareTo(safeDeletedAt) >= 0) {
                    return false;
                }
            }
            ContentValues values = new ContentValues();
            values.put("table_name", table);
            values.put("sync_id", syncId.trim());
            values.put("deleted_at", safeDeletedAt);
            conn.insertWithOnConflict("sync_deletions", null, values, SQLiteDatabase.CONFLICT_REPLACE);
            return true;
        }

        void recordSyncDeletion(String table, long id) {
            if (!isSyncDeletableTable(table)) {
                return;
            }
            try (Cursor c = conn.rawQuery("SELECT IFNULL(sync_id,'') FROM " + table + " WHERE id=?",
                    new String[]{String.valueOf(id)})) {
                if (c.moveToFirst()) {
                    upsertSyncDeletion(table, str(c, 0), timestamp());
                }
            }
        }

        void clearSyncDeletion(String table, String syncId) {
            conn.delete("sync_deletions", "table_name=? AND sync_id=?", new String[]{table, syncId == null ? "" : syncId.trim()});
        }

        boolean isSyncDeleted(String table, String syncId, String remoteUpdated) {
            if (syncId == null || syncId.trim().isEmpty()) {
                return false;
            }
            try (Cursor c = conn.rawQuery("SELECT deleted_at FROM sync_deletions WHERE table_name=? AND sync_id=?",
                    new String[]{table, syncId.trim()})) {
                return c.moveToFirst() && str(c, 0).compareTo(remoteUpdated == null ? "" : remoteUpdated) >= 0;
            }
        }

        void deleteLocalSyncedRow(String table, long id) {
            if ("transactions".equals(table)) {
                try (Cursor c = conn.rawQuery("SELECT IFNULL(attachment,'') FROM transactions WHERE id=?",
                        new String[]{String.valueOf(id)})) {
                    if (c.moveToFirst() && !str(c, 0).isEmpty()) {
                        deleteAttachmentFile(str(c, 0));
                    }
                }
            } else if ("shopping_lists".equals(table)) {
                conn.delete("shopping_items", "list_id=?", new String[]{String.valueOf(id)});
            }
            conn.delete(table, "id=?", new String[]{String.valueOf(id)});
        }

        int importRemoteDeletion(JSONObject item) {
            if (item == null) {
                return 0;
            }
            String table = item.optString("table_name", item.optString("table", "")).trim();
            String syncId = item.optString("sync_id", "").trim();
            String deletedAt = item.optString("deleted_at", item.optString("updated_at", timestamp())).trim();
            if (!isSyncDeletableTable(table) || syncId.isEmpty()) {
                return 0;
            }
            boolean tombstoneChanged = upsertSyncDeletion(table, syncId, deletedAt);
            try (Cursor c = conn.rawQuery("SELECT id, IFNULL(updated_at,'') FROM " + table + " WHERE sync_id=?",
                    new String[]{syncId})) {
                if (c.moveToFirst() && str(c, 1).compareTo(deletedAt) <= 0) {
                    deleteLocalSyncedRow(table, c.getLong(0));
                    return 3;
                }
            }
            return tombstoneChanged ? 2 : 0;
        }

        JSONArray exportDeletions() throws JSONException {
            JSONArray out = new JSONArray();
            try (Cursor c = conn.rawQuery("SELECT table_name, sync_id, deleted_at FROM sync_deletions ORDER BY deleted_at, table_name, sync_id", null)) {
                while (c.moveToNext()) {
                    JSONObject item = new JSONObject();
                    item.put("table_name", str(c, 0));
                    item.put("sync_id", str(c, 1));
                    item.put("deleted_at", str(c, 2));
                    out.put(item);
                }
            }
            return out;
        }

        JSONArray exportDebts(String table) throws JSONException {
            JSONArray out = new JSONArray();
            try (Cursor c = conn.rawQuery("SELECT name, total_amount, deadline, IFNULL(sync_id,''), IFNULL(updated_at,'') " +
                    "FROM " + table + " ORDER BY IFNULL(updated_at,''), id", null)) {
                while (c.moveToNext()) {
                    JSONObject item = new JSONObject();
                    item.put("sync_id", str(c, 3));
                    item.put("updated_at", str(c, 4));
                    item.put("name", str(c, 0));
                    item.put("total_amount", c.getDouble(1));
                    item.put("deadline", str(c, 2));
                    out.put(item);
                }
            }
            return out;
        }

        JSONObject exportSyncPayload() throws JSONException {
            ensureTransactionSyncMetadata();
            ensureAuxSyncMetadata();
            JSONObject payload = new JSONObject();

            JSONArray accounts = new JSONArray();
            for (Account acc : getAccounts()) {
                JSONObject item = new JSONObject();
                item.put("name", acc.name);
                item.put("initial_balance", acc.initialBalance);
                item.put("color", acc.color);
                accounts.put(item);
            }
            payload.put("accounts", accounts);

            JSONArray categories = new JSONArray();
            for (String category : getCategories()) {
                categories.put(category);
            }
            payload.put("categories", categories);

            JSONArray people = new JSONArray();
            for (String person : getPeople()) {
                people.put(person);
            }
            payload.put("people", people);

            payload.put("liabilities", exportDebts("liabilities"));
            payload.put("debtors", exportDebts("debtors"));

            JSONArray rows = new JSONArray();
            try (Cursor c = conn.rawQuery("SELECT id, date, type, category, subcategory, amount, " +
                    "IFNULL(exclude_from_weekly,0), IFNULL(details,''), account_id, ref_id, sync_id, updated_at, IFNULL(sync_order,''), IFNULL(attachment,'') " +
                    "FROM transactions ORDER BY IFNULL(sync_order, IFNULL(updated_at, '')), id", null)) {
                while (c.moveToNext()) {
                    Account acc = accountById(c.isNull(8) ? 1 : c.getLong(8));
                    JSONObject tx = new JSONObject();
                    tx.put("sync_id", str(c, 10));
                    tx.put("updated_at", str(c, 11));
                    tx.put("sync_order", str(c, 12));
                    tx.put("date", str(c, 1));
                    tx.put("type", str(c, 2));
                    tx.put("category", str(c, 3));
                    tx.put("subcategory", str(c, 4));
                    tx.put("amount", c.getDouble(5));
                    tx.put("exclude_from_weekly", c.getInt(6));
                    tx.put("details", str(c, 7));
                    tx.put("account_name", acc == null ? "Gotówka" : acc.name);
                    tx.put("account_color", acc == null ? "#27ae60" : acc.color);
                    tx.put("ref_sync_id", debtSyncIdById(c.isNull(9) ? null : c.getLong(9), str(c, 2)));
                    putSyncAttachmentMetadata(tx, str(c, 13));
                    rows.put(tx);
                }
            }
            payload.put("transactions", rows);

            JSONArray bills = new JSONArray();
            try (Cursor c = conn.rawQuery("SELECT id, due_date, amount, category, description, IFNULL(is_paid,0), " +
                    "IFNULL(is_recurring,0), ref_id, IFNULL(sync_id,''), IFNULL(updated_at,'') FROM pending_bills " +
                    "ORDER BY IFNULL(updated_at,''), id", null)) {
                while (c.moveToNext()) {
                    JSONObject bill = new JSONObject();
                    bill.put("sync_id", str(c, 8));
                    bill.put("updated_at", str(c, 9));
                    bill.put("due_date", str(c, 1));
                    bill.put("amount", c.getDouble(2));
                    bill.put("category", str(c, 3));
                    bill.put("description", str(c, 4));
                    bill.put("is_paid", c.getInt(5));
                    bill.put("is_recurring", c.getInt(6));
                    bill.put("ref_name", debtNameById(c.isNull(7) ? null : c.getLong(7), "liabilities"));
                    bill.put("ref_sync_id", debtSyncIdById(c.isNull(7) ? null : c.getLong(7), "liabilities"));
                    bills.put(bill);
                }
            }
            payload.put("pending_bills", bills);

            JSONArray lists = new JSONArray();
            Map<Long, String> listSyncById = new HashMap<>();
            try (Cursor c = conn.rawQuery("SELECT id, name, created_at, status, IFNULL(sync_id,''), IFNULL(updated_at,'') " +
                    "FROM shopping_lists ORDER BY IFNULL(created_at,''), id", null)) {
                while (c.moveToNext()) {
                    listSyncById.put(c.getLong(0), str(c, 4));
                    JSONObject item = new JSONObject();
                    item.put("sync_id", str(c, 4));
                    item.put("updated_at", str(c, 5));
                    item.put("name", str(c, 1));
                    item.put("created_at", str(c, 2));
                    item.put("status", str(c, 3));
                    lists.put(item);
                }
            }
            payload.put("shopping_lists", lists);

            JSONArray items = new JSONArray();
            try (Cursor c = conn.rawQuery("SELECT id, list_id, product_name, quantity, IFNULL(store,''), IFNULL(is_checked,0), " +
                    "IFNULL(sync_id,''), IFNULL(updated_at,'') FROM shopping_items " +
                    "ORDER BY list_id, IFNULL(store,''), product_name, id", null)) {
                while (c.moveToNext()) {
                    String parentSync = listSyncById.get(c.getLong(1));
                    if (parentSync == null || parentSync.isEmpty()) {
                        continue;
                    }
                    JSONObject item = new JSONObject();
                    item.put("sync_id", str(c, 6));
                    item.put("updated_at", str(c, 7));
                    item.put("list_sync_id", parentSync);
                    item.put("product_name", str(c, 2));
                    item.put("quantity", str(c, 3));
                    item.put("store", str(c, 4));
                    item.put("is_checked", c.getInt(5));
                    items.put(item);
                }
            }
            payload.put("shopping_items", items);
            payload.put("deletions", exportDeletions());
            return payload;
        }

        SyncResult importSyncPayload(JSONObject payload) throws JSONException {
            SyncResult result = new SyncResult();

            JSONArray accounts = payload.optJSONArray("accounts");
            if (accounts != null) {
                for (int i = 0; i < accounts.length(); i++) {
                    JSONObject account = accounts.optJSONObject(i);
                    if (account != null) {
                        ensureAccount(account.optString("name", "Gotówka"),
                                account.optDouble("initial_balance", 0.0),
                                account.optString("color", "#7f8c8d"));
                    }
                }
            }

            JSONArray categories = payload.optJSONArray("categories");
            if (categories != null) {
                for (int i = 0; i < categories.length(); i++) {
                    addCategory(categories.optString(i));
                }
            }

            JSONArray people = payload.optJSONArray("people");
            if (people != null) {
                for (int i = 0; i < people.length(); i++) {
                    addPerson(people.optString(i));
                }
            }

            JSONArray deletions = payload.optJSONArray("deletions");
            if (deletions != null) {
                for (int i = 0; i < deletions.length(); i++) {
                    int change = importRemoteDeletion(deletions.optJSONObject(i));
                    if (change == 3) {
                        result.deleted++;
                    } else if (change == 2) {
                        result.updated++;
                    }
                }
            }

            JSONArray liabilities = payload.optJSONArray("liabilities");
            if (liabilities != null) {
                for (int i = 0; i < liabilities.length(); i++) {
                    JSONObject item = liabilities.optJSONObject(i);
                    if (item == null) {
                        continue;
                    }
                    int change = importRemoteDebt("liabilities", item);
                    if (change == 1) {
                        result.inserted++;
                    } else if (change == 2) {
                        result.updated++;
                    }
                }
            }

            JSONArray debtors = payload.optJSONArray("debtors");
            if (debtors != null) {
                for (int i = 0; i < debtors.length(); i++) {
                    JSONObject item = debtors.optJSONObject(i);
                    if (item == null) {
                        continue;
                    }
                    int change = importRemoteDebt("debtors", item);
                    if (change == 1) {
                        result.inserted++;
                    } else if (change == 2) {
                        result.updated++;
                    }
                }
            }

            JSONArray rows = payload.optJSONArray("transactions");
            conn.beginTransaction();
            try {
                if (rows != null) {
                    for (int i = 0; i < rows.length(); i++) {
                        JSONObject tx = rows.optJSONObject(i);
                        if (tx == null) {
                            continue;
                        }
                        int change = importRemoteTransaction(tx);
                        if (change == 1) {
                            result.inserted++;
                        } else if (change == 2) {
                            result.updated++;
                        }
                    }
                }

                JSONArray bills = payload.optJSONArray("pending_bills");
                if (bills != null) {
                    for (int i = 0; i < bills.length(); i++) {
                        JSONObject bill = bills.optJSONObject(i);
                        if (bill == null) {
                            continue;
                        }
                        int change = importRemoteBill(bill);
                        if (change == 1) {
                            result.inserted++;
                        } else if (change == 2) {
                            result.updated++;
                        }
                    }
                }

                Map<String, Long> listIds = new HashMap<>();
                JSONArray lists = payload.optJSONArray("shopping_lists");
                if (lists != null) {
                    for (int i = 0; i < lists.length(); i++) {
                        JSONObject list = lists.optJSONObject(i);
                        if (list == null) {
                            continue;
                        }
                        ImportRow change = importRemoteShoppingList(list);
                        if (change.localId > 0) {
                            listIds.put(list.optString("sync_id", ""), change.localId);
                        }
                        if (change.change == 1) {
                            result.inserted++;
                        } else if (change.change == 2) {
                            result.updated++;
                        }
                    }
                }

                JSONArray items = payload.optJSONArray("shopping_items");
                if (items != null) {
                    for (int i = 0; i < items.length(); i++) {
                        JSONObject item = items.optJSONObject(i);
                        if (item == null) {
                            continue;
                        }
                        int change = importRemoteShoppingItem(item, listIds);
                        if (change == 1) {
                            result.inserted++;
                        } else if (change == 2) {
                            result.updated++;
                        }
                    }
                }
                conn.setTransactionSuccessful();
            } finally {
                conn.endTransaction();
            }
            normalizeImportedData();
            return result;
        }

        void putAttachmentValue(ContentValues values, JSONObject tx, String existingFilename) {
            String filename = writeSyncAttachment(tx, existingFilename);
            if (filename == null || filename.trim().isEmpty()) {
                if (tx.has("attachment_present") && !tx.optBoolean("attachment_present", true)) {
                    values.putNull("attachment");
                } else if (existingFilename != null && !existingFilename.trim().isEmpty()) {
                    values.put("attachment", existingFilename);
                } else {
                    values.putNull("attachment");
                }
            } else {
                values.put("attachment", filename);
            }
        }

        String writeSyncAttachment(JSONObject tx, String existingFilename) {
            String encoded = tx.optString("attachment_data", "").trim();
            if (encoded.isEmpty()) {
                if (tx.has("attachment_present") && !tx.optBoolean("attachment_present", true)
                        && existingFilename != null && !existingFilename.trim().isEmpty()) {
                    deleteAttachmentFile(existingFilename);
                    return "";
                }
                return existingFilename;
            }
            try {
                byte[] data = Base64.decode(encoded, Base64.DEFAULT);
                if (data.length <= 0 || data.length > MAX_ATTACHMENT_BYTES) {
                    return existingFilename;
                }
                String rawName = safeAttachmentName(tx.optString("attachment_name", "zalacznik.dat"));
                String filename = UUID.randomUUID().toString().replace("-", "") + "-" + rawName;
                File target = new File(attachmentsDir, filename);
                attachmentsDir.mkdirs();
                try (OutputStream out = new FileOutputStream(target)) {
                    out.write(data);
                }
                if (existingFilename != null && !existingFilename.trim().isEmpty() && !existingFilename.equals(filename)) {
                    deleteAttachmentFile(existingFilename);
                }
                return filename;
            } catch (Exception ex) {
                return existingFilename;
            }
        }

        String safeAttachmentName(String raw) {
            String value = raw == null ? "zalacznik.dat" : raw;
            value = value.replace("/", "_").replace("\\", "_").trim();
            return value.isEmpty() ? "zalacznik.dat" : value;
        }

        void putSyncAttachmentMetadata(JSONObject tx, String filename) throws JSONException {
            File file = attachmentFile(filename);
            if (file == null || !file.isFile()) {
                tx.put("attachment_present", false);
                return;
            }
            tx.put("attachment_present", true);
            tx.put("attachment_name", safeAttachmentName(filename));
            tx.put("attachment_size", file.length());
            String sha = fileSha256(file);
            if (!sha.isEmpty()) {
                tx.put("attachment_sha256", sha);
            }
        }

        boolean needsSyncAttachmentDownload(String syncId, long expectedSize, String expectedSha256) {
            String filename = attachmentForSyncId(syncId);
            File file = attachmentFile(filename);
            if (file == null || !file.isFile()) {
                return true;
            }
            if (expectedSize >= 0 && file.length() != expectedSize) {
                return true;
            }
            String expectedSha = expectedSha256 == null ? "" : expectedSha256.trim();
            return !expectedSha.isEmpty() && !expectedSha.equalsIgnoreCase(fileSha256(file));
        }

        boolean saveSyncAttachment(String syncId, String rawName, File source) {
            if (syncId == null || syncId.trim().isEmpty()
                    || source == null || !source.isFile() || source.length() <= 0 || source.length() > MAX_SYNC_ATTACHMENT_BYTES) {
                return false;
            }
            String existing = attachmentForSyncId(syncId);
            String filename = UUID.randomUUID().toString().replace("-", "") + "-" + safeAttachmentName(rawName);
            File target = new File(attachmentsDir, filename);
            attachmentsDir.mkdirs();
            try (InputStream in = new FileInputStream(source);
                 OutputStream out = new FileOutputStream(target)) {
                byte[] buffer = new byte[8192];
                int read;
                while ((read = in.read(buffer)) != -1) {
                    out.write(buffer, 0, read);
                }
            } catch (IOException ex) {
                target.delete();
                return false;
            }
            ContentValues values = new ContentValues();
            values.put("attachment", filename);
            int changed = conn.update("transactions", values, "sync_id=?", new String[]{syncId});
            if (changed <= 0) {
                target.delete();
                return false;
            }
            if (existing != null && !existing.trim().isEmpty() && !existing.equals(filename)) {
                deleteAttachmentFile(existing);
            }
            return true;
        }

        String attachmentForTransactionId(long id) {
            try (Cursor c = conn.rawQuery("SELECT IFNULL(attachment,'') FROM transactions WHERE id=?", new String[]{String.valueOf(id)})) {
                return c.moveToFirst() ? str(c, 0) : "";
            }
        }

        String attachmentForSyncId(String syncId) {
            if (syncId == null || syncId.trim().isEmpty()) {
                return "";
            }
            try (Cursor c = conn.rawQuery("SELECT IFNULL(attachment,'') FROM transactions WHERE sync_id=?", new String[]{syncId})) {
                return c.moveToFirst() ? str(c, 0) : "";
            }
        }

        File attachmentFileForSyncId(String syncId) {
            return attachmentFile(attachmentForSyncId(syncId));
        }

        String fileSha256(File file) {
            try {
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                try (InputStream in = new FileInputStream(file)) {
                    byte[] buffer = new byte[8192];
                    int read;
                    while ((read = in.read(buffer)) != -1) {
                        digest.update(buffer, 0, read);
                    }
                }
                byte[] bytes = digest.digest();
                StringBuilder out = new StringBuilder(bytes.length * 2);
                for (byte b : bytes) {
                    out.append(String.format(Locale.ROOT, "%02x", b & 0xff));
                }
                return out.toString();
            } catch (Exception ex) {
                return "";
            }
        }

        int importRemoteTransaction(JSONObject tx) {
            String syncId = tx.optString("sync_id", "");
            if (syncId.trim().isEmpty()) {
                return 0;
            }
            String remoteUpdated = tx.optString("updated_at", timestamp());
            if (isSyncDeleted("transactions", syncId, remoteUpdated)) {
                return 0;
            }
            String remoteOrder = tx.optString("sync_order", remoteUpdated);
            boolean remoteHasOrder = tx.has("sync_order") && !tx.optString("sync_order", "").trim().isEmpty();
            String[] existing = transactionUpdatedAt(syncId);
            if (existing != null && existing[0] != null && existing[0].compareTo(remoteUpdated) >= 0) {
                if ((existing.length < 2 || existing[1].isEmpty()) && !tx.optString("attachment_data", "").trim().isEmpty()) {
                    String filename = writeSyncAttachment(tx, existing.length < 2 ? "" : existing[1]);
                    if (filename != null && existing.length > 2) {
                        ContentValues attach = new ContentValues();
                        attach.put("attachment", filename);
                        conn.update("transactions", attach, "id=?", new String[]{existing[2]});
                        return 2;
                    }
                }
                return 0;
            }

            Account account = ensureAccount(tx.optString("account_name", "Gotówka"),
                    0.0, tx.optString("account_color", "#7f8c8d"));
            ContentValues values = new ContentValues();
            values.put("date", tx.optString("date", todayStatic()));
            values.put("type", tx.optString("type", "expense"));
            values.put("category", tx.optString("category", "Inne"));
            values.put("subcategory", tx.optString("subcategory", ""));
            values.put("amount", tx.optDouble("amount", 0.0));
            values.put("currency", "PLN");
            values.put("exchange_rate", 1.0);
            values.put("exclude_from_weekly", tx.optInt("exclude_from_weekly", 0));
            values.put("details", tx.optString("details", ""));
            if (existing == null) {
                values.putNull("attachment");
            } else {
                putAttachmentValue(values, tx, existing.length < 2 ? "" : existing[1]);
            }
            Long refId = resolveRef(values.getAsString("type"), values.getAsString("subcategory"), tx.optString("ref_sync_id", ""));
            if (refId == null) values.putNull("ref_id"); else values.put("ref_id", refId);
            values.put("account_id", account.id);
            values.put("sync_id", syncId);
            values.put("updated_at", remoteUpdated);
            values.put("sync_order", remoteOrder == null || remoteOrder.trim().isEmpty() ? remoteUpdated : remoteOrder);

            addCategory(values.getAsString("category"));
            if ("income".equals(values.getAsString("type"))) {
                addPerson(values.getAsString("category"));
            }

            if (existing == null) {
                Long duplicateId = findLegacyDuplicateTransaction(tx, values, syncId, remoteOrder, remoteHasOrder);
                if (duplicateId != null) {
                    putAttachmentValue(values, tx, attachmentForTransactionId(duplicateId));
                    conn.update("transactions", values, "id=?", new String[]{String.valueOf(duplicateId)});
                    clearSyncDeletion("transactions", syncId);
                    return 2;
                }
                putAttachmentValue(values, tx, "");
                conn.insert("transactions", null, values);
                clearSyncDeletion("transactions", syncId);
                return 1;
            }
            conn.update("transactions", values, "sync_id=?", new String[]{syncId});
            clearSyncDeletion("transactions", syncId);
            return 2;
        }

        int importRemoteDebt(String table, JSONObject item) {
            String syncId = item.optString("sync_id", "").trim();
            if (syncId.isEmpty()) {
                return 0;
            }
            String remoteUpdated = item.optString("updated_at", timestamp());
            if (isSyncDeleted(table, syncId, remoteUpdated)) {
                return 0;
            }
            long existingId = -1;
            String existingUpdated = "";
            try (Cursor c = conn.rawQuery("SELECT id, IFNULL(updated_at,'') FROM " + table + " WHERE sync_id=?", new String[]{syncId})) {
                if (c.moveToFirst()) {
                    existingId = c.getLong(0);
                    existingUpdated = str(c, 1);
                }
            }
            if (existingId > 0 && existingUpdated.compareTo(remoteUpdated) >= 0) {
                return 0;
            }

            String name = item.optString("name", "").trim();
            if (name.isEmpty()) {
                return 0;
            }
            ContentValues values = new ContentValues();
            values.put("name", name);
            values.put("total_amount", item.optDouble("total_amount", 0.0));
            values.put("deadline", item.optString("deadline", ""));
            values.put("sync_id", syncId);
            values.put("updated_at", remoteUpdated);

            if (existingId > 0) {
                conn.update(table, values, "id=?", new String[]{String.valueOf(existingId)});
                clearSyncDeletion(table, syncId);
                return 2;
            }

            Long duplicateId = findLegacyDuplicateDebt(table, values, syncId);
            if (duplicateId != null) {
                conn.update(table, values, "id=?", new String[]{String.valueOf(duplicateId)});
                clearSyncDeletion(table, syncId);
                return 2;
            }
            conn.insert(table, null, values);
            clearSyncDeletion(table, syncId);
            return 1;
        }

        int importRemoteBill(JSONObject bill) {
            String syncId = bill.optString("sync_id", "").trim();
            if (syncId.isEmpty()) {
                return 0;
            }
            String remoteUpdated = bill.optString("updated_at", timestamp());
            if (isSyncDeleted("pending_bills", syncId, remoteUpdated)) {
                return 0;
            }
            long existingId = -1;
            String existingUpdated = "";
            try (Cursor c = conn.rawQuery("SELECT id, IFNULL(updated_at,'') FROM pending_bills WHERE sync_id=?", new String[]{syncId})) {
                if (c.moveToFirst()) {
                    existingId = c.getLong(0);
                    existingUpdated = str(c, 1);
                }
            }
            if (existingId > 0 && existingUpdated.compareTo(remoteUpdated) >= 0) {
                return 0;
            }

            ContentValues values = new ContentValues();
            String category = bill.optString("category", "Inne");
            String description = bill.optString("description", "");
            values.put("due_date", bill.optString("due_date", todayStatic()));
            values.put("amount", bill.optDouble("amount", 0.0));
            values.put("category", category);
            values.put("description", description);
            values.put("is_paid", bill.optInt("is_paid", 0));
            values.put("is_recurring", bill.optInt("is_recurring", 0));
            Long refId = resolveBillRef(category, description, bill.optString("ref_name", ""), bill.optString("ref_sync_id", ""));
            if (refId == null) values.putNull("ref_id"); else values.put("ref_id", refId);
            values.put("sync_id", syncId);
            values.put("updated_at", remoteUpdated);

            if (existingId > 0) {
                conn.update("pending_bills", values, "id=?", new String[]{String.valueOf(existingId)});
                clearSyncDeletion("pending_bills", syncId);
                return 2;
            }

            Long duplicateId = findLegacyDuplicateBill(values, syncId);
            if (duplicateId != null) {
                conn.update("pending_bills", values, "id=?", new String[]{String.valueOf(duplicateId)});
                clearSyncDeletion("pending_bills", syncId);
                return 2;
            }
            conn.insert("pending_bills", null, values);
            clearSyncDeletion("pending_bills", syncId);
            return 1;
        }

        ImportRow importRemoteShoppingList(JSONObject remote) {
            String syncId = remote.optString("sync_id", "").trim();
            if (syncId.isEmpty()) {
                return new ImportRow(0, -1);
            }
            String remoteUpdated = remote.optString("updated_at", timestamp());
            if (isSyncDeleted("shopping_lists", syncId, remoteUpdated)) {
                return new ImportRow(0, -1);
            }
            long existingId = -1;
            String existingUpdated = "";
            try (Cursor c = conn.rawQuery("SELECT id, IFNULL(updated_at,'') FROM shopping_lists WHERE sync_id=?", new String[]{syncId})) {
                if (c.moveToFirst()) {
                    existingId = c.getLong(0);
                    existingUpdated = str(c, 1);
                }
            }
            if (existingId > 0 && existingUpdated.compareTo(remoteUpdated) >= 0) {
                return new ImportRow(0, existingId);
            }

            ContentValues values = new ContentValues();
            values.put("name", remote.optString("name", "Lista zakupów"));
            values.put("created_at", remote.optString("created_at", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.ROOT).format(new Date())));
            values.put("status", remote.optString("status", "open"));
            values.put("sync_id", syncId);
            values.put("updated_at", remoteUpdated);

            if (existingId > 0) {
                conn.update("shopping_lists", values, "id=?", new String[]{String.valueOf(existingId)});
                clearSyncDeletion("shopping_lists", syncId);
                return new ImportRow(2, existingId);
            }

            Long duplicateId = findLegacyDuplicateShoppingList(values, syncId);
            if (duplicateId != null) {
                conn.update("shopping_lists", values, "id=?", new String[]{String.valueOf(duplicateId)});
                clearSyncDeletion("shopping_lists", syncId);
                return new ImportRow(2, duplicateId);
            }
            long id = conn.insert("shopping_lists", null, values);
            clearSyncDeletion("shopping_lists", syncId);
            return new ImportRow(1, id);
        }

        int importRemoteShoppingItem(JSONObject remote, Map<String, Long> listIds) {
            String syncId = remote.optString("sync_id", "").trim();
            String listSyncId = remote.optString("list_sync_id", "").trim();
            if (syncId.isEmpty() || listSyncId.isEmpty()) {
                return 0;
            }
            String remoteUpdated = remote.optString("updated_at", timestamp());
            if (isSyncDeleted("shopping_items", syncId, remoteUpdated)) {
                return 0;
            }
            Long listId = localShoppingListId(listSyncId, listIds);
            if (listId == null || listId <= 0) {
                return 0;
            }
            long existingId = -1;
            String existingUpdated = "";
            try (Cursor c = conn.rawQuery("SELECT id, IFNULL(updated_at,'') FROM shopping_items WHERE sync_id=?", new String[]{syncId})) {
                if (c.moveToFirst()) {
                    existingId = c.getLong(0);
                    existingUpdated = str(c, 1);
                }
            }
            if (existingId > 0 && existingUpdated.compareTo(remoteUpdated) >= 0) {
                return 0;
            }

            ContentValues values = new ContentValues();
            values.put("list_id", listId);
            values.put("product_name", remote.optString("product_name", ""));
            values.put("quantity", remote.optString("quantity", ""));
            values.put("store", remote.optString("store", ""));
            values.put("is_checked", remote.optInt("is_checked", 0));
            values.put("sync_id", syncId);
            values.put("updated_at", remoteUpdated);

            if (existingId > 0) {
                conn.update("shopping_items", values, "id=?", new String[]{String.valueOf(existingId)});
                addProduct(values.getAsString("product_name"));
                addShop(values.getAsString("store"));
                clearSyncDeletion("shopping_items", syncId);
                return 2;
            }

            Long duplicateId = findLegacyDuplicateShoppingItem(values, syncId);
            if (duplicateId != null) {
                conn.update("shopping_items", values, "id=?", new String[]{String.valueOf(duplicateId)});
                addProduct(values.getAsString("product_name"));
                addShop(values.getAsString("store"));
                clearSyncDeletion("shopping_items", syncId);
                return 2;
            }
            conn.insert("shopping_items", null, values);
            addProduct(values.getAsString("product_name"));
            addShop(values.getAsString("store"));
            clearSyncDeletion("shopping_items", syncId);
            return 1;
        }

        Long resolveBillRef(String category, String description, String refName) {
            return resolveBillRef(category, description, refName, "");
        }

        Long resolveBillRef(String category, String description, String refName, String refSyncId) {
            if (!"Spłata Długu".equals(category)) {
                return null;
            }
            if (refSyncId != null && !refSyncId.trim().isEmpty()) {
                try (Cursor c = conn.rawQuery("SELECT id FROM liabilities WHERE sync_id=? LIMIT 1", new String[]{refSyncId.trim()})) {
                    if (c.moveToFirst()) {
                        return c.getLong(0);
                    }
                }
            }
            for (String name : new String[]{refName, description}) {
                if (name == null || name.trim().isEmpty()) {
                    continue;
                }
                try (Cursor c = conn.rawQuery("SELECT id FROM liabilities WHERE name=? LIMIT 1", new String[]{name.trim()})) {
                    if (c.moveToFirst()) {
                        return c.getLong(0);
                    }
                }
            }
            return null;
        }

        Long findLegacyDuplicateBill(ContentValues values, String syncId) {
            try (Cursor c = conn.rawQuery("SELECT id FROM pending_bills " +
                    "WHERE IFNULL(due_date,'')=? AND ABS(IFNULL(amount,0.0)-?) < 0.000001 " +
                    "AND IFNULL(category,'')=? AND IFNULL(description,'')=? AND IFNULL(is_recurring,0)=? " +
                    "AND (sync_id IS NULL OR TRIM(sync_id)='' OR sync_id != ?) ORDER BY id LIMIT 1",
                    new String[]{
                            values.getAsString("due_date"),
                            String.valueOf(values.getAsDouble("amount")),
                            values.getAsString("category"),
                            values.getAsString("description"),
                            String.valueOf(values.getAsInteger("is_recurring")),
                            syncId
                    })) {
                return c.moveToFirst() ? c.getLong(0) : null;
            }
        }

        Long findLegacyDuplicateDebt(String table, ContentValues values, String syncId) {
            try (Cursor c = conn.rawQuery("SELECT id FROM " + table + " " +
                    "WHERE IFNULL(name,'')=? AND ABS(IFNULL(total_amount,0.0)-?) < 0.000001 " +
                    "AND IFNULL(deadline,'')=? " +
                    "AND (sync_id IS NULL OR TRIM(sync_id)='' OR sync_id != ?) ORDER BY id LIMIT 1",
                    new String[]{
                            values.getAsString("name"),
                            String.valueOf(values.getAsDouble("total_amount")),
                            values.getAsString("deadline"),
                            syncId
                    })) {
                return c.moveToFirst() ? c.getLong(0) : null;
            }
        }

        Long findLegacyDuplicateShoppingList(ContentValues values, String syncId) {
            try (Cursor c = conn.rawQuery("SELECT id FROM shopping_lists " +
                    "WHERE IFNULL(name,'')=? AND IFNULL(created_at,'')=? " +
                    "AND (sync_id IS NULL OR TRIM(sync_id)='' OR sync_id != ?) ORDER BY id LIMIT 1",
                    new String[]{values.getAsString("name"), values.getAsString("created_at"), syncId})) {
                return c.moveToFirst() ? c.getLong(0) : null;
            }
        }

        Long findLegacyDuplicateShoppingItem(ContentValues values, String syncId) {
            try (Cursor c = conn.rawQuery("SELECT id FROM shopping_items " +
                    "WHERE list_id=? AND IFNULL(product_name,'')=? AND IFNULL(quantity,'')=? AND IFNULL(store,'')=? " +
                    "AND (sync_id IS NULL OR TRIM(sync_id)='' OR sync_id != ?) ORDER BY id LIMIT 1",
                    new String[]{
                            String.valueOf(values.getAsLong("list_id")),
                            values.getAsString("product_name"),
                            values.getAsString("quantity"),
                            values.getAsString("store"),
                            syncId
                    })) {
                return c.moveToFirst() ? c.getLong(0) : null;
            }
        }

        Long localShoppingListId(String syncId, Map<String, Long> cache) {
            if (cache.containsKey(syncId)) {
                return cache.get(syncId);
            }
            try (Cursor c = conn.rawQuery("SELECT id FROM shopping_lists WHERE sync_id=?", new String[]{syncId})) {
                if (c.moveToFirst()) {
                    long id = c.getLong(0);
                    cache.put(syncId, id);
                    return id;
                }
            }
            return null;
        }

        String debtNameById(Long id, String table) {
            if (id == null) {
                return "";
            }
            try (Cursor c = conn.rawQuery("SELECT name FROM " + table + " WHERE id=?", new String[]{String.valueOf(id)})) {
                return c.moveToFirst() ? str(c, 0) : "";
            }
        }

        String debtSyncIdById(Long id, String tableOrType) {
            if (id == null) {
                return "";
            }
            String table = "";
            if ("liabilities".equals(tableOrType) || "liability_repayment".equals(tableOrType)) {
                table = "liabilities";
            } else if ("debtors".equals(tableOrType) || "debtor_repayment".equals(tableOrType)) {
                table = "debtors";
            }
            if (table.isEmpty()) {
                return "";
            }
            try (Cursor c = conn.rawQuery("SELECT IFNULL(sync_id,'') FROM " + table + " WHERE id=?", new String[]{String.valueOf(id)})) {
                return c.moveToFirst() ? str(c, 0) : "";
            }
        }

        boolean isLegacySyncOrder(String value) {
            String raw = value == null ? "" : value.trim();
            if (raw.isEmpty()) {
                return true;
            }
            int sep = raw.lastIndexOf('|');
            String tail = sep >= 0 ? raw.substring(sep + 1) : raw;
            if (tail.isEmpty()) {
                return true;
            }
            for (int i = 0; i < tail.length(); i++) {
                if (!Character.isDigit(tail.charAt(i))) {
                    return false;
                }
            }
            return true;
        }

        Long findLegacyDuplicateTransaction(JSONObject tx, ContentValues values, String syncId, String remoteOrder, boolean remoteHasOrder) {
            if (remoteHasOrder && !isLegacySyncOrder(remoteOrder)) {
                return null;
            }
            String sql = "SELECT id FROM transactions " +
                    "WHERE IFNULL(date,'')=? " +
                    "AND IFNULL(type,'')=? " +
                    "AND IFNULL(category,'')=? " +
                    "AND IFNULL(subcategory,'')=? " +
                    "AND ABS(IFNULL(amount,0.0) - ?) < 0.000001 " +
                    "AND IFNULL(exclude_from_weekly,0)=? " +
                    "AND IFNULL(details,'')=? " +
                    "AND IFNULL(account_id,1)=? " +
                    "AND (sync_id IS NULL OR sync_id != ?) " +
                    "AND (sync_order IS NULL OR TRIM(sync_order)='' OR sync_order GLOB '*|[0-9]*') " +
                    "ORDER BY id LIMIT 1";
            try (Cursor c = conn.rawQuery(sql, new String[]{
                    tx.optString("date", todayStatic()),
                    values.getAsString("type"),
                    values.getAsString("category"),
                    values.getAsString("subcategory"),
                    String.valueOf(tx.optDouble("amount", 0.0)),
                    String.valueOf(tx.optInt("exclude_from_weekly", 0)),
                    values.getAsString("details"),
                    String.valueOf(values.getAsLong("account_id")),
                    syncId
            })) {
                return c.moveToFirst() ? c.getLong(0) : null;
            }
        }

        String[] transactionUpdatedAt(String syncId) {
            try (Cursor c = conn.rawQuery("SELECT IFNULL(updated_at,''), IFNULL(attachment,''), id FROM transactions WHERE sync_id=?", new String[]{syncId})) {
                if (c.moveToFirst()) {
                    return new String[]{str(c, 0), str(c, 1), String.valueOf(c.getLong(2))};
                }
            }
            return null;
        }

        List<Tx> getTransactions(String monthPrefix, String query) {
            List<Tx> out = new ArrayList<>();
            StringBuilder sql = new StringBuilder("SELECT id, date, type, category, subcategory, amount, details, attachment, account_id, ref_id, exclude_from_weekly, sync_id, updated_at, sync_order FROM transactions");
            List<String> args = new ArrayList<>();
            sql.append(" WHERE ABS(IFNULL(amount,0.0)) >= 0.001");
            if (monthPrefix != null && !monthPrefix.isEmpty()) {
                sql.append(" AND date LIKE ?");
                args.add(monthPrefix + "%");
            }
            sql.append(" ORDER BY IFNULL(sync_order, IFNULL(updated_at,'')) DESC, id DESC");
            String q = query == null ? "" : query.toLowerCase(Locale.ROOT);
            try (Cursor c = conn.rawQuery(sql.toString(), args.toArray(new String[0]))) {
                while (c.moveToNext()) {
                    Tx tx = new Tx();
                    tx.id = c.getLong(0);
                    tx.date = str(c, 1);
                    tx.type = str(c, 2);
                    tx.category = str(c, 3);
                    tx.subcategory = str(c, 4);
                    tx.amount = c.getDouble(5);
                    tx.details = str(c, 6);
                    tx.attachment = str(c, 7);
                    tx.hasAttachment = tx.attachment != null && !tx.attachment.isEmpty();
                    tx.accountId = c.isNull(8) ? 1 : c.getLong(8);
                    tx.refId = c.isNull(9) ? null : c.getLong(9);
                    tx.exclude = c.isNull(10) ? 0 : c.getInt(10);
                    tx.syncId = str(c, 11);
                    tx.updatedAt = str(c, 12);
                    tx.syncOrder = str(c, 13);
                    if (q.isEmpty() || matches(tx, q)) {
                        out.add(tx);
                    }
                }
            }
            return out;
        }

        boolean matches(Tx tx, String q) {

            Account acc = accountById(tx.accountId);

            return tx.date.toLowerCase(Locale.ROOT).contains(q)
                    || tx.type.toLowerCase(Locale.ROOT).contains(q)
                    || tx.category.toLowerCase(Locale.ROOT).contains(q)
                    || tx.subcategory.toLowerCase(Locale.ROOT).contains(q)
                    || tx.details.toLowerCase(Locale.ROOT).contains(q)
                    || String.format(Locale.ROOT, "%.2f", tx.amount).contains(q)
                    || String.valueOf((int) tx.amount).contains(q)
                    || (acc != null && acc.name.toLowerCase(Locale.ROOT).contains(q));
        }

        String str(Cursor c, int index) {
            return c.isNull(index) ? "" : c.getString(index);
        }

        boolean isMonthLocked(String month) {
            try (Cursor c = conn.rawQuery("SELECT 1 FROM month_locks WHERE month_str=?", new String[]{month})) {
                return c.moveToFirst();
            }
        }

        void lockMonth(String month) {
            exec("INSERT OR IGNORE INTO month_locks VALUES (?)", month);
        }

        void unlockMonth(String month) {
            conn.delete("month_locks", "month_str=?", new String[]{month});
        }

        List<Account> getAccounts() {
            List<Account> out = new ArrayList<>();
            try (Cursor c = conn.rawQuery("SELECT id, name, initial_balance, color FROM accounts ORDER BY id", null)) {
                while (c.moveToNext()) {
                    Account a = new Account();
                    a.id = c.getLong(0);
                    a.name = c.getString(1);
                    a.initialBalance = c.getDouble(2);
                    a.color = c.isNull(3) ? "#7f8c8d" : c.getString(3);
                    out.add(a);
                }
            }
            return out;
        }

        Account accountById(long id) {
            for (Account acc : getAccounts()) {
                if (acc.id == id) {
                    return acc;
                }
            }
            return null;
        }

        Account accountByName(String name) {
            String safe = name == null || name.trim().isEmpty() ? "Gotówka" : name.trim();
            for (Account acc : getAccounts()) {
                if (acc.name.equals(safe)) {
                    return acc;
                }
            }
            return null;
        }

        Account ensureAccount(String name, double initial, String color) {
            String safeName = name == null || name.trim().isEmpty() ? "Gotówka" : name.trim();
            Account existing = accountByName(safeName);
            if (existing != null) {
                return existing;
            }
            if (!addAccount(safeName, initial, color == null || color.trim().isEmpty() ? "#7f8c8d" : color)) {
                Account fallback = firstExistingAccount();
                return fallback == null ? new Account() : fallback;
            }
            return accountByName(safeName);
        }

        Account firstExistingAccount() {
            List<Account> accounts = getAccounts();
            return accounts.isEmpty() ? null : accounts.get(0);
        }

        boolean addAccount(String name, double initial, String color) {
            try {
                exec("INSERT INTO accounts (name, initial_balance, color) VALUES (?, ?, ?)", name, initial, color);
                return true;
            } catch (Exception ex) {
                return false;
            }
        }

        void deleteAccount(long id) {
            if (id == 1) {
                return;
            }
            conn.delete("accounts", "id=?", new String[]{String.valueOf(id)});
            exec("UPDATE transactions SET account_id=1 WHERE account_id=?", id);
        }

        Long resolveRef(String type, String subcategory) {
            return resolveRef(type, subcategory, "");
        }

        Long resolveRef(String type, String subcategory, String refSyncId) {
            String table = null;
            if ("liability_repayment".equals(type)) {
                table = "liabilities";
            } else if ("debtor_repayment".equals(type)) {
                table = "debtors";
            }

            if (table != null && refSyncId != null && !refSyncId.trim().isEmpty()) {
                try (Cursor c = conn.rawQuery("SELECT id FROM " + table + " WHERE sync_id=? LIMIT 1", new String[]{refSyncId.trim()})) {
                    if (c.moveToFirst()) {
                        return c.getLong(0);
                    }
                }
            }

            if (subcategory == null || subcategory.trim().isEmpty()) {
                return null;
            }
            if ("liability_repayment".equals(type)) {
                table = "liabilities";
            } else if ("debtor_repayment".equals(type)) {
                table = "debtors";
            } else if ("goal_deposit".equals(type)) {
                try (Cursor c = conn.rawQuery("SELECT id FROM goals WHERE name=? LIMIT 1", new String[]{subcategory})) {
                    return c.moveToFirst() ? c.getLong(0) : null;
                }
            }
            if (table == null) {
                return null;
            }
            try (Cursor c = conn.rawQuery("SELECT id FROM " + table + " WHERE name=? LIMIT 1", new String[]{subcategory})) {
                return c.moveToFirst() ? c.getLong(0) : null;
            }
        }

        double accountBalance(long accountId) {
            return accountBalanceInternal(accountId, null, false);
        }

        double accountBalanceBefore(long accountId, String exclusiveDate) {
            return accountBalanceInternal(accountId, exclusiveDate, true);
        }

        double accountBalanceInternal(long accountId, String dateLimit, boolean exclusive) {

            Account acc = accountById(accountId);
            double balance = acc == null ? 0.0 : acc.initialBalance;

            List<Tx> rows = getTransactions(null, null);

            for (Tx tx : rows) {

                if (tx.accountId != accountId) {
                    continue;
                }

                if (dateLimit != null) {
                    int cmp = tx.date.compareTo(dateLimit);
                    if ((exclusive && cmp >= 0) || (!exclusive && cmp > 0)) {
                        continue;
                    }
                }

                balance += accountBalanceDelta(tx.type, tx.amount);
            }

            return balance;
        }

        double accountBalanceDelta(String type, double amount) {
            if ("income".equals(type) || "debtor_repayment".equals(type)) {
                return amount;
            }
            if ("account_transfer".equals(type)) {
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

        double totalBalanceAllAccounts() {
            double total = 0.0;

            for (Account acc : getAccounts()) {
                total += accountBalance(acc.id);
            }

            return total;
        }

        boolean addGoal(String name, double target, long accountId) {
            try {
                exec("INSERT INTO goals (name, target_amount, default_account_id) VALUES (?, ?, ?)", name, target, accountId);
                return true;
            } catch (Exception ex) {
                return false;
            }
        }

        List<Goal> getGoals() {
            List<Goal> out = new ArrayList<>();
            try (Cursor c = conn.rawQuery("SELECT id, name, target_amount, IFNULL(default_account_id, 1) FROM goals ORDER BY name", null)) {
                while (c.moveToNext()) {
                    Goal g = new Goal();
                    g.id = c.getLong(0);
                    g.name = c.getString(1);
                    g.target = c.getDouble(2);
                    g.defaultAccountId = c.getLong(3);
                    out.add(g);
                }
            }
            return out;
        }

        void deleteGoal(long id) {
            conn.delete("goals", "id=?", new String[]{String.valueOf(id)});
        }

        double goalTotal(Goal goal) {
            double total = scalarDouble("SELECT IFNULL(SUM(amount),0) FROM transactions WHERE type='goal_deposit' AND (ref_id=? OR (ref_id IS NULL AND subcategory=?))",
                    String.valueOf(goal.id), goal.name);
            total += scalarDouble("SELECT IFNULL(SUM(amount),0) FROM transactions WHERE type IN ('savings','savings_migration') AND subcategory IN (?,?,?)",
                    goal.name, "Wpłata: " + goal.name, "Wypłata: " + goal.name);
            return total;
        }

        double totalCashSavings() {
            Set<String> goalVariants = new HashSet<>();
            for (Goal g : getGoals()) {
                goalVariants.add(g.name);
                goalVariants.add("Wpłata: " + g.name);
                goalVariants.add("Wypłata: " + g.name);
            }
            double total = 0.0;
            try (Cursor c = conn.rawQuery("SELECT amount, subcategory FROM transactions WHERE type IN ('savings','savings_migration')", null)) {
                while (c.moveToNext()) {
                    if (!goalVariants.contains(c.getString(1))) {
                        total += c.getDouble(0);
                    }
                }
            }
            return total;
        }

        long addDebt(String table, String name, double amount, String deadline) {
            android.content.ContentValues values = new android.content.ContentValues();
            values.put("name", name);
            values.put("total_amount", amount);
            values.put("deadline", deadline);
            values.put("sync_id", UUID.randomUUID().toString());
            values.put("updated_at", timestamp());
            return conn.insert(table, null, values);
        }

        List<Debt> getDebts(String table) {
            List<Debt> out = new ArrayList<>();
            String type = "liabilities".equals(table) ? "liability_repayment" : "debtor_repayment";
            try (Cursor c = conn.rawQuery("SELECT id, name, total_amount, deadline FROM " + table + " ORDER BY deadline, name", null)) {
                while (c.moveToNext()) {
                    Debt d = new Debt();
                    d.id = c.getLong(0);
                    d.name = c.getString(1);
                    d.total = c.getDouble(2);
                    d.deadline = c.getString(3);
                    d.paid = scalarDouble("SELECT IFNULL(SUM(amount),0) FROM transactions WHERE type=? AND ref_id=?",
                            type, String.valueOf(d.id));
                    out.add(d);
                }
            }
            return out;
        }

        Debt debtById(String table, long id) {
            for (Debt debt : getDebts(table)) {
                if (debt.id == id) {
                    return debt;
                }
            }
            return null;
        }

        void deleteDebt(String table, long id) {
            recordSyncDeletion(table, id);
            conn.delete(table, "id=?", new String[]{String.valueOf(id)});
        }

        List<Bill> getPendingBills() {
            List<Bill> out = new ArrayList<>();
            try (Cursor c = conn.rawQuery("SELECT id, due_date, amount, category, description, IFNULL(is_recurring,0), ref_id FROM pending_bills WHERE is_paid=0 ORDER BY due_date", null)) {
                while (c.moveToNext()) {
                    Bill b = new Bill();
                    b.id = c.getLong(0);
                    b.dueDate = c.getString(1);
                    b.amount = c.getDouble(2);
                    b.category = c.getString(3);
                    b.description = c.getString(4);
                    b.recurring = c.getInt(5) == 1;
                    b.refId = c.isNull(6) ? null : c.getLong(6);
                    out.add(b);
                }
            }
            return out;
        }

        void addPendingBill(String dueDate, double amount, String category, String description, boolean recurring, Long refId) {
            android.content.ContentValues values = new android.content.ContentValues();
            values.put("due_date", dueDate);
            values.put("amount", amount);
            values.put("category", category);
            values.put("description", description);
            values.put("is_paid", 0);
            values.put("is_recurring", recurring ? 1 : 0);
            if (refId == null) values.putNull("ref_id"); else values.put("ref_id", refId);
            values.put("sync_id", UUID.randomUUID().toString());
            values.put("updated_at", timestamp());
            conn.insert("pending_bills", null, values);
        }

        void updatePendingBill(long id, String dueDate, double amount, String category, String description, boolean recurring, Long refId) {
            android.content.ContentValues values = new android.content.ContentValues();
            values.put("due_date", dueDate);
            values.put("amount", amount);
            values.put("category", category);
            values.put("description", description);
            values.put("is_recurring", recurring ? 1 : 0);
            if (refId == null) values.putNull("ref_id"); else values.put("ref_id", refId);
            values.put("updated_at", timestamp());
            conn.update("pending_bills", values, "id=?", new String[]{String.valueOf(id)});
        }

        void markBillPaid(long id) {
            android.content.ContentValues values = new android.content.ContentValues();
            values.put("is_paid", 1);
            values.put("updated_at", timestamp());
            conn.update("pending_bills", values, "id=?", new String[]{String.valueOf(id)});
        }

        void deletePendingBill(long id) {
            recordSyncDeletion("pending_bills", id);
            conn.delete("pending_bills", "id=?", new String[]{String.valueOf(id)});
        }

        long createShoppingList(String name) {
            android.content.ContentValues values = new android.content.ContentValues();
            values.put("name", name);
            values.put("created_at", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.ROOT).format(new Date()));
            values.put("status", "open");
            values.put("sync_id", UUID.randomUUID().toString());
            values.put("updated_at", timestamp());
            return conn.insert("shopping_lists", null, values);
        }

        List<ShoppingListData> getShoppingLists() {
            List<ShoppingListData> out = new ArrayList<>();
            try (Cursor c = conn.rawQuery("SELECT id, name, created_at, status FROM shopping_lists ORDER BY created_at DESC", null)) {
                while (c.moveToNext()) {
                    ShoppingListData list = new ShoppingListData();
                    list.id = c.getLong(0);
                    list.name = c.getString(1);
                    list.createdAt = c.getString(2);
                    list.status = c.getString(3);
                    out.add(list);
                }
            }
            return out;
        }

        ShoppingListData shoppingListById(long id) {
            for (ShoppingListData list : getShoppingLists()) {
                if (list.id == id) {
                    return list;
                }
            }
            return null;
        }

        void addShoppingItem(long listId, String product, String quantity, String store) {
            android.content.ContentValues values = new android.content.ContentValues();
            values.put("list_id", listId);
            values.put("product_name", product);
            values.put("quantity", quantity == null || quantity.trim().isEmpty() ? "1 szt." : quantity);
            values.put("store", store == null ? "" : store);
            values.put("is_checked", 0);
            values.put("sync_id", UUID.randomUUID().toString());
            values.put("updated_at", timestamp());
            conn.insert("shopping_items", null, values);
        }

        List<ShoppingItem> getShoppingItems(long listId) {
            List<ShoppingItem> out = new ArrayList<>();
            try (Cursor c = conn.rawQuery("SELECT id, product_name, quantity, store, IFNULL(is_checked,0) FROM shopping_items WHERE list_id=? ORDER BY store ASC, product_name ASC",
                    new String[]{String.valueOf(listId)})) {
                while (c.moveToNext()) {
                    ShoppingItem item = new ShoppingItem();
                    item.id = c.getLong(0);
                    item.product = c.getString(1);
                    item.quantity = c.getString(2);
                    item.store = c.getString(3);
                    item.checked = c.getInt(4) == 1;
                    out.add(item);
                }
            }
            return out;
        }

        void setShoppingItemChecked(long id, boolean checked) {
            android.content.ContentValues values = new android.content.ContentValues();
            values.put("is_checked", checked ? 1 : 0);
            values.put("updated_at", timestamp());
            conn.update("shopping_items", values, "id=?", new String[]{String.valueOf(id)});
        }

        void deleteShoppingItem(long id) {
            recordSyncDeletion("shopping_items", id);
            conn.delete("shopping_items", "id=?", new String[]{String.valueOf(id)});
        }

        void closeShoppingList(long id) {
            android.content.ContentValues values = new android.content.ContentValues();
            values.put("status", "closed");
            values.put("updated_at", timestamp());
            conn.update("shopping_lists", values, "id=?", new String[]{String.valueOf(id)});
        }

        void deleteShoppingList(long id) {
            try (Cursor c = conn.rawQuery("SELECT id FROM shopping_items WHERE list_id=?", new String[]{String.valueOf(id)})) {
                while (c.moveToNext()) {
                    recordSyncDeletion("shopping_items", c.getLong(0));
                }
            }
            recordSyncDeletion("shopping_lists", id);
            conn.delete("shopping_items", "list_id=?", new String[]{String.valueOf(id)});
            conn.delete("shopping_lists", "id=?", new String[]{String.valueOf(id)});
        }

        void addShop(String name) {
            if (name != null && !name.trim().isEmpty()) {
                exec("INSERT OR IGNORE INTO shops VALUES (?)", name.trim());
            }
        }

        List<String> getShops() {
            return queryStrings("SELECT name FROM shops ORDER BY name");
        }

        void addProduct(String name) {
            if (name != null && !name.trim().isEmpty()) {
                exec("INSERT OR IGNORE INTO products VALUES (?)", name.trim());
            }
        }

        List<String> getProducts() {
            return queryStrings("SELECT name FROM products ORDER BY name");
        }

        boolean shoppingListHasItems(long id) {
            return scalarDouble(
                    "SELECT COUNT(*) FROM shopping_items WHERE list_id=?",
                    String.valueOf(id)
            ) > 0;
        }

        double sumTransactions(String from, String to, List<String> types) {
            if (types == null || types.isEmpty()) {
                return 0.0;
            }
            StringBuilder placeholders = new StringBuilder();
            List<String> args = new ArrayList<>();
            args.add(from);
            args.add(to);
            for (int i = 0; i < types.size(); i++) {
                if (i > 0) placeholders.append(",");
                placeholders.append("?");
                args.add(types.get(i));
            }
            return scalarDouble("SELECT IFNULL(SUM(amount),0) FROM transactions WHERE date >= ? AND date <= ? AND type IN (" + placeholders + ")",
                    args.toArray(new String[0]));
        }

        Map<String, Double> categorySpending(String month) {
            Map<String, Double> out = new LinkedHashMap<>();
            try (Cursor c = conn.rawQuery("SELECT category, SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ? GROUP BY category ORDER BY SUM(amount) DESC",
                    new String[]{month + "%"})) {
                while (c.moveToNext()) {
                    out.put(c.getString(0), c.getDouble(1));
                }
            }
            return out;
        }

        File attachmentFile(String filename) {
            if (filename == null || filename.trim().isEmpty()) {
                return null;
            }
            return new File(attachmentsDir, safeAttachmentName(filename));
        }

        void deleteAttachmentFile(String filename) {
            File file = attachmentFile(filename);
            if (file != null) {
                file.delete();
            }
        }

        double scalarDouble(String sql, String... args) {
            try (Cursor c = conn.rawQuery(sql, args)) {
                return c.moveToFirst() ? c.getDouble(0) : 0.0;
            }
        }

        static String timestamp() {
            return new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS", Locale.ROOT).format(new Date());
        }

        static String syncOrder() {
            return timestamp() + "|android|" + UUID.randomUUID().toString();
        }

        static String todayStatic() {
            return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(new Date());
        }
    }
}
