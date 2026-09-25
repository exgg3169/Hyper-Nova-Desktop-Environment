package org.hypernova.launcher;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.InputMethodManager;
import android.widget.AdapterView;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.GridView;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.PopupMenu;
import android.widget.TextView;
import android.widget.Toast;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** The HyperNova home screen: wallpaper, clock, taskbar or dock and the start menu. */
public class MainActivity extends Activity {
    private static final Locale TR = new Locale("tr", "TR");
    private static final int MATCH = ViewGroup.LayoutParams.MATCH_PARENT;
    private static final int WRAP = ViewGroup.LayoutParams.WRAP_CONTENT;

    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    private final List<AppEntry> apps = new ArrayList<>();

    private Prefs prefs;
    private NovaStyle style;
    private boolean clock24h;
    private TextView bigClock;
    private TextView bigDate;
    private TextView barClock;
    private LinearLayout pinnedBar;
    private FrameLayout menuOverlay;
    private EditText menuSearch;
    private AppAdapter menuAdapter;
    private AppAdapter tileAdapter;
    private BroadcastReceiver receiver;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = new Prefs(this);
        buildUi();
        loadApps();
        registerReceivers();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (prefs.style() != style || prefs.clock24h() != clock24h) {
            buildUi();
            refreshPinned();
        }
        updateClock();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        // Pressing Home while already home closes the start menu.
        closeMenu();
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        // A home screen never finishes on Back; it only closes the menu.
        closeMenu();
    }

    @Override
    protected void onDestroy() {
        if (receiver != null) {
            unregisterReceiver(receiver);
        }
        io.shutdownNow();
        super.onDestroy();
    }

    // --- data -----------------------------------------------------------------------

    private void loadApps() {
        io.execute(() -> {
            List<AppEntry> loaded = AppRepository.load(this);
            main.post(() -> {
                apps.clear();
                apps.addAll(loaded);
                if (prefs.pinned() == null) {
                    prefs.setPinned(AppRepository.defaultPinned(this, apps));
                }
                refreshPinned();
                if (menuAdapter != null) {
                    menuAdapter.setApps(apps);
                }
            });
        });
    }

    private void registerReceivers() {
        receiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (Intent.ACTION_TIME_TICK.equals(intent.getAction())
                        || Intent.ACTION_TIME_CHANGED.equals(intent.getAction())
                        || Intent.ACTION_TIMEZONE_CHANGED.equals(intent.getAction())) {
                    updateClock();
                } else {
                    loadApps();
                }
            }
        };
        IntentFilter time = new IntentFilter();
        time.addAction(Intent.ACTION_TIME_TICK);
        time.addAction(Intent.ACTION_TIME_CHANGED);
        time.addAction(Intent.ACTION_TIMEZONE_CHANGED);
        IntentFilter packages = new IntentFilter();
        packages.addAction(Intent.ACTION_PACKAGE_ADDED);
        packages.addAction(Intent.ACTION_PACKAGE_REMOVED);
        packages.addAction(Intent.ACTION_PACKAGE_CHANGED);
        packages.addDataScheme("package");
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(receiver, time, Context.RECEIVER_EXPORTED);
            registerReceiver(receiver, packages, Context.RECEIVER_EXPORTED);
        } else {
            registerReceiver(receiver, time);
            registerReceiver(receiver, packages);
        }
    }

    private List<AppEntry> pinnedApps() {
        List<AppEntry> result = new ArrayList<>();
        List<String> keys = prefs.pinned();
        if (keys == null) {
            return result;
        }
        for (String key : keys) {
            for (AppEntry app : apps) {
                if (app.key().equals(key)) {
                    result.add(app);
                    break;
                }
            }
        }
        return result;
    }

    private boolean isPinned(AppEntry app) {
        List<String> keys = prefs.pinned();
        return keys != null && keys.contains(app.key());
    }

    private void setPinned(AppEntry app, boolean pinned) {
        List<String> keys = prefs.pinned();
        if (keys == null) {
            keys = new ArrayList<>();
        }
        keys.remove(app.key());
        if (pinned) {
            keys.add(app.key());
        }
        prefs.setPinned(keys);
        refreshPinned();
    }

    // --- layout ---------------------------------------------------------------------

    private int dp(float value) {
        return Ui.dp(this, value);
    }

    private void buildUi() {
        style = prefs.style();
        clock24h = prefs.clock24h();
        getWindow().setNavigationBarColor(style.navigationBarColor());

        FrameLayout root = new FrameLayout(this);
        WallpaperView wallpaper = new WallpaperView(this, style);
        wallpaper.setOnLongClickListener(v -> {
            openSettings();
            return true;
        });
        wallpaper.setOnClickListener(v -> closeMenu());
        root.addView(wallpaper, new FrameLayout.LayoutParams(MATCH, MATCH));

        LinearLayout column = new LinearLayout(this);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setFitsSystemWindows(true);
        column.addView(buildClockWidget(), new LinearLayout.LayoutParams(MATCH, WRAP));
        View spacer = new View(this);
        column.addView(spacer, new LinearLayout.LayoutParams(MATCH, 0, 1));
        if (style.hasTaskbar()) {
            column.addView(buildTaskbar(), new LinearLayout.LayoutParams(MATCH, dp(48)));
        } else {
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(WRAP, WRAP);
            lp.gravity = Gravity.CENTER_HORIZONTAL;
            lp.bottomMargin = dp(10);
            column.addView(buildDock(), lp);
        }
        // Let taps on the empty area reach the wallpaper (long-press opens settings).
        spacer.setClickable(false);
        column.setClickable(false);
        root.addView(column, new FrameLayout.LayoutParams(MATCH, MATCH));

        menuOverlay = buildMenu();
        menuOverlay.setVisibility(View.GONE);
        root.addView(menuOverlay, new FrameLayout.LayoutParams(MATCH, MATCH));
        setContentView(root);
        updateClock();
    }

    private View buildClockWidget() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(style == NovaStyle.MAC ? Gravity.END : Gravity.CENTER_HORIZONTAL);
        box.setPadding(dp(24), dp(40), dp(24), 0);
        bigClock = new TextView(this);
        bigClock.setTextColor(Color.WHITE);
        bigClock.setTextSize(64);
        bigClock.setTypeface(Typeface.create("sans-serif-light", Typeface.NORMAL));
        bigClock.setShadowLayer(10, 0, 2, 0x99000000);
        bigDate = new TextView(this);
        bigDate.setTextColor(Color.WHITE);
        bigDate.setTextSize(18);
        bigDate.setShadowLayer(8, 0, 1, 0x99000000);
        box.addView(bigClock);
        box.addView(bigDate);
        return box;
    }

    private View buildTaskbar() {
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        switch (style) {
            case XP:
                bar.setBackground(Ui.vertical(0xFF3168D5, 0xFF4993E6, 0xFF2157D7, 0xFF2663E0, 0xFF1941A5));
                break;
            case WIN7:
                bar.setBackground(Ui.vertical(0xE63B5877, 0xF01F3A57, 0xF5142A42));
                break;
            default:
                bar.setBackgroundColor(0xF0101010);
                break;
        }
        bar.addView(buildStartButton(), new LinearLayout.LayoutParams(WRAP, MATCH));

        if (style == NovaStyle.WIN10) {
            TextView search = new TextView(this);
            search.setText("Aramak için yazın");
            search.setTextColor(0xFF4A4A4A);
            search.setTextSize(13);
            search.setSingleLine(true);
            search.setGravity(Gravity.CENTER_VERTICAL);
            search.setPadding(dp(10), 0, dp(10), 0);
            search.setBackgroundColor(0xFFF3F3F3);
            search.setOnClickListener(v -> openMenu(true));
            bar.addView(search, new LinearLayout.LayoutParams(dp(130), MATCH));
        }

        HorizontalScrollView scroll = new HorizontalScrollView(this);
        scroll.setHorizontalScrollBarEnabled(false);
        pinnedBar = new LinearLayout(this);
        pinnedBar.setOrientation(LinearLayout.HORIZONTAL);
        pinnedBar.setGravity(Gravity.CENTER_VERTICAL);
        pinnedBar.setPadding(dp(4), 0, dp(4), 0);
        scroll.addView(pinnedBar, new FrameLayout.LayoutParams(WRAP, MATCH));
        bar.addView(scroll, new LinearLayout.LayoutParams(0, MATCH, 1));

        barClock = new TextView(this);
        barClock.setTextColor(Color.WHITE);
        barClock.setTextSize(style == NovaStyle.XP ? 13 : 12);
        barClock.setGravity(Gravity.CENTER);
        barClock.setPadding(dp(10), 0, dp(10), 0);
        if (style == NovaStyle.XP) {
            barClock.setBackground(Ui.vertical(0xFF0C59B9, 0xFF139EE9, 0xFF18B5F2, 0xFF139BEB, 0xFF0D8DEA));
        }
        barClock.setOnClickListener(v -> openSettings());
        bar.addView(barClock, new LinearLayout.LayoutParams(WRAP, MATCH));
        return bar;
    }

    private View buildStartButton() {
        LinearLayout start = new LinearLayout(this);
        start.setGravity(Gravity.CENTER);
        start.setOnClickListener(v -> toggleMenu());
        start.setContentDescription("Başlat");
        ImageView icon = new ImageView(this);
        switch (style) {
            case XP: {
                float r = dp(16);
                start.setBackground(Ui.rounded(Ui.vertical(0xFF388E38, 0xFF5DBD57, 0xFF3F9E3A, 0xFF378F34, 0xFF2B6C27),
                        0, 0, r, r, r, r, 0, 0));
                start.setPadding(dp(8), 0, dp(18), 0);
                icon.setImageDrawable(LogoDrawables.star(0xF2FFFFFF));
                start.addView(icon, new LinearLayout.LayoutParams(dp(22), dp(22)));
                TextView label = new TextView(this);
                label.setText("başlat");
                label.setTextColor(Color.WHITE);
                label.setTextSize(17);
                label.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD_ITALIC));
                label.setShadowLayer(2, 1, 1, 0x88000000);
                label.setPadding(dp(4), 0, 0, 0);
                start.addView(label);
                break;
            }
            case WIN7:
                start.setPadding(dp(8), 0, dp(8), 0);
                icon.setImageDrawable(LogoDrawables.orb());
                start.addView(icon, new LinearLayout.LayoutParams(dp(40), dp(40)));
                break;
            default:
                start.setPadding(dp(16), 0, dp(16), 0);
                icon.setImageDrawable(LogoDrawables.panes(Color.WHITE));
                start.addView(icon, new LinearLayout.LayoutParams(dp(18), dp(18)));
                break;
        }
        return start;
    }

    private View buildDock() {
        LinearLayout dock = new LinearLayout(this);
        dock.setOrientation(LinearLayout.HORIZONTAL);
        dock.setGravity(Gravity.CENTER_VERTICAL);
        GradientDrawable bg = Ui.solid(0x73F0F0F4, dp(22));
        bg.setStroke(dp(1), 0x80FFFFFF);
        dock.setBackground(bg);
        dock.setPadding(dp(8), dp(6), dp(8), dp(6));

        ImageView launchpad = new ImageView(this);
        launchpad.setImageDrawable(LogoDrawables.star(null));
        launchpad.setContentDescription("Uygulamalar");
        launchpad.setOnClickListener(v -> toggleMenu());
        dock.addView(launchpad, iconParams(48));

        pinnedBar = new LinearLayout(this);
        pinnedBar.setOrientation(LinearLayout.HORIZONTAL);
        pinnedBar.setGravity(Gravity.CENTER_VERTICAL);
        dock.addView(pinnedBar, new LinearLayout.LayoutParams(WRAP, WRAP));
        return dock;
    }

    private LinearLayout.LayoutParams iconParams(int sizeDp) {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(sizeDp), dp(sizeDp));
        lp.leftMargin = dp(4);
        lp.rightMargin = dp(4);
        return lp;
    }

    private void refreshPinned() {
        if (pinnedBar == null) {
            return;
        }
        pinnedBar.removeAllViews();
        int size = style == NovaStyle.MAC ? 48 : (style == NovaStyle.XP ? 30 : 34);
        List<AppEntry> pinned = pinnedApps();
        int max = style == NovaStyle.MAC ? 5 : pinned.size();
        for (int i = 0; i < Math.min(max, pinned.size()); i++) {
            AppEntry app = pinned.get(i);
            ImageView icon = new ImageView(this);
            icon.setImageDrawable(app.icon);
            icon.setContentDescription(app.label);
            icon.setPadding(dp(3), dp(3), dp(3), dp(3));
            icon.setOnClickListener(v -> launch(app));
            icon.setOnLongClickListener(v -> {
                showAppOptions(v, app);
                return true;
            });
            pinnedBar.addView(icon, iconParams(size));
        }
    }

    // --- start menu -----------------------------------------------------------------

    private FrameLayout buildMenu() {
        FrameLayout overlay = new FrameLayout(this);
        overlay.setFitsSystemWindows(true);
        overlay.setOnClickListener(v -> closeMenu());

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setClickable(true);

        int text = style == NovaStyle.XP || style == NovaStyle.WIN7 ? 0xFF1E1E1E : Color.WHITE;
        menuAdapter = new AppAdapter(this, style == NovaStyle.MAC ? AppAdapter.Mode.GRID : AppAdapter.Mode.LIST, text);
        menuAdapter.setApps(apps);
        menuSearch = new EditText(this);
        menuSearch.setSingleLine(true);
        menuSearch.setTextSize(15);
        menuSearch.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {
            }

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                menuAdapter.filter(s.toString());
            }

            @Override
            public void afterTextChanged(Editable s) {
            }
        });

        AdapterView.OnItemClickListener open = (parent, view, position, id) ->
                launch((AppEntry) parent.getItemAtPosition(position));
        AdapterView.OnItemLongClickListener options = (parent, view, position, id) -> {
            showAppOptions(view, (AppEntry) parent.getItemAtPosition(position));
            return true;
        };

        FrameLayout.LayoutParams panelParams;
        switch (style) {
            case MAC: {
                overlay.setBackgroundColor(0xE61C1C28);
                styleSearch(0x2EFFFFFF, Color.WHITE, "Ara", dp(10));
                LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(dp(260), WRAP);
                sp.gravity = Gravity.CENTER_HORIZONTAL;
                sp.topMargin = dp(24);
                panel.addView(menuSearch, sp);
                GridView grid = new GridView(this);
                grid.setNumColumns(GridView.AUTO_FIT);
                grid.setColumnWidth(dp(88));
                grid.setStretchMode(GridView.STRETCH_COLUMN_WIDTH);
                grid.setVerticalSpacing(dp(12));
                grid.setAdapter(menuAdapter);
                grid.setOnItemClickListener(open);
                grid.setOnItemLongClickListener(options);
                LinearLayout.LayoutParams gp = new LinearLayout.LayoutParams(MATCH, 0, 1);
                gp.topMargin = dp(16);
                panel.addView(grid, gp);
                panelParams = new FrameLayout.LayoutParams(MATCH, MATCH);
                break;
            }
            case XP: {
                overlay.setBackgroundColor(0x33000000);
                panel.setBackgroundColor(0xFFD3E5FA);
                panel.addView(menuHeader(Ui.vertical(0xFF1868CE, 0xFF0E60CB, 0xFF3A8AE8, 0xFF1A64D0), Color.WHITE));
                View stripe = new View(this);
                stripe.setBackgroundColor(0xFFF1A44B);
                panel.addView(stripe, new LinearLayout.LayoutParams(MATCH, dp(2)));
                styleSearch(Color.WHITE, 0xFF1E1E1E, "Programları ara", dp(2));
                LinearLayout.LayoutParams sp = margins(new LinearLayout.LayoutParams(MATCH, WRAP), 8);
                panel.addView(menuSearch, sp);
                panel.addView(appList(0xFFFFFFFF, open, options), new LinearLayout.LayoutParams(MATCH, 0, 1));
                LinearLayout footer = footer(Ui.vertical(0xFF4282D6, 0xFF3B77D3, 0xFF1C4FAE), Color.WHITE);
                panel.addView(footer, new LinearLayout.LayoutParams(MATCH, dp(48)));
                panelParams = startPanelParams();
                break;
            }
            case WIN7: {
                overlay.setBackgroundColor(0x33000000);
                GradientDrawable glass = Ui.vertical(0xF54A6F95, 0xF7203D5D, 0xFA16304C);
                glass.setCornerRadius(dp(8));
                panel.setBackground(glass);
                panel.setPadding(dp(8), dp(8), dp(8), dp(8));
                panel.addView(menuHeader(null, Color.WHITE));
                ListView list = appList(0, open, options);
                GradientDrawable white = Ui.solid(Color.WHITE, dp(5));
                white.setStroke(dp(1), 0xFF6C8AA8);
                list.setBackground(white);
                panel.addView(list, new LinearLayout.LayoutParams(MATCH, 0, 1));
                styleSearch(Color.WHITE, 0xFF1E1E1E, "Programları ve dosyaları ara", dp(4));
                panel.addView(menuSearch, margins(new LinearLayout.LayoutParams(MATCH, WRAP), 4));
                panel.addView(footer(null, Color.WHITE), new LinearLayout.LayoutParams(MATCH, dp(44)));
                panelParams = startPanelParams();
                break;
            }
            default: {
                overlay.setBackgroundColor(0x33000000);
                panel.setBackgroundColor(0xF51F1F1F);
                styleSearch(0xFF2B2B2B, Color.WHITE, "Aramak için buraya yazın", 0);
                panel.addView(menuSearch, margins(new LinearLayout.LayoutParams(MATCH, WRAP), 8));
                TextView pinnedTitle = sectionTitle("Sabitlenenler");
                panel.addView(pinnedTitle);
                tileAdapter = new AppAdapter(this, AppAdapter.Mode.TILE, Color.WHITE);
                GridView tiles = new GridView(this);
                tiles.setNumColumns(4);
                tiles.setHorizontalSpacing(dp(4));
                tiles.setVerticalSpacing(dp(4));
                tiles.setAdapter(tileAdapter);
                tiles.setOnItemClickListener(open);
                tiles.setOnItemLongClickListener(options);
                panel.addView(tiles, margins(new LinearLayout.LayoutParams(MATCH, dp(172)), 8));
                panel.addView(sectionTitle("Tüm uygulamalar"));
                panel.addView(appList(0, open, options), new LinearLayout.LayoutParams(MATCH, 0, 1));
                panel.addView(footer(null, Color.WHITE), new LinearLayout.LayoutParams(MATCH, dp(44)));
                panelParams = startPanelParams();
                break;
            }
        }
        overlay.addView(panel, panelParams);
        return overlay;
    }

    private FrameLayout.LayoutParams startPanelParams() {
        int width = Math.min(getResources().getDisplayMetrics().widthPixels, dp(400));
        int height = (int) (getResources().getDisplayMetrics().heightPixels * 0.72f);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(width, height);
        lp.gravity = Gravity.BOTTOM | Gravity.START;
        lp.bottomMargin = dp(48);
        return lp;
    }

    private LinearLayout.LayoutParams margins(LinearLayout.LayoutParams lp, int marginDp) {
        lp.setMargins(dp(marginDp), dp(marginDp), dp(marginDp), dp(marginDp));
        return lp;
    }

    private void styleSearch(int background, int textColor, String hint, int radius) {
        menuSearch.setHint(hint);
        menuSearch.setHintTextColor((textColor & 0x00FFFFFF) | 0x99000000);
        menuSearch.setTextColor(textColor);
        menuSearch.setBackground(Ui.solid(background, radius));
        menuSearch.setPadding(dp(12), dp(8), dp(12), dp(8));
    }

    private ListView appList(int background, AdapterView.OnItemClickListener open,
                             AdapterView.OnItemLongClickListener options) {
        ListView list = new ListView(this);
        list.setBackgroundColor(background);
        list.setDivider(null);
        list.setAdapter(menuAdapter);
        list.setOnItemClickListener(open);
        list.setOnItemLongClickListener(options);
        return list;
    }

    private TextView sectionTitle(String title) {
        TextView view = new TextView(this);
        view.setText(title);
        view.setTextColor(Color.WHITE);
        view.setTypeface(Typeface.DEFAULT_BOLD);
        view.setPadding(dp(12), dp(6), dp(12), dp(2));
        return view;
    }

    private View menuHeader(GradientDrawable background, int textColor) {
        LinearLayout header = new LinearLayout(this);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(12), dp(10), dp(12), dp(10));
        if (background != null) {
            header.setBackground(background);
        }
        ImageView logo = new ImageView(this);
        logo.setImageDrawable(LogoDrawables.star(null));
        header.addView(logo, new LinearLayout.LayoutParams(dp(40), dp(40)));
        TextView title = new TextView(this);
        title.setText("HyperNova");
        title.setTextColor(textColor);
        title.setTextSize(18);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setShadowLayer(3, 1, 1, 0x66000000);
        title.setPadding(dp(10), 0, 0, 0);
        header.addView(title);
        return header;
    }

    private LinearLayout footer(GradientDrawable background, int textColor) {
        LinearLayout footer = new LinearLayout(this);
        footer.setGravity(Gravity.CENTER_VERTICAL | Gravity.END);
        footer.setPadding(dp(8), 0, dp(8), 0);
        if (background != null) {
            footer.setBackground(background);
        }
        footer.addView(footerButton("HyperNova Ayarları", textColor, v -> openSettings()));
        footer.addView(footerButton("Android Ayarları", textColor,
                v -> startSafely(new Intent(Settings.ACTION_SETTINGS))));
        return footer;
    }

    private TextView footerButton(String label, int color, View.OnClickListener listener) {
        TextView button = new TextView(this);
        button.setText(label);
        button.setTextColor(color);
        button.setTextSize(13);
        button.setPadding(dp(10), dp(8), dp(10), dp(8));
        button.setOnClickListener(v -> {
            closeMenu();
            listener.onClick(v);
        });
        return button;
    }

    private void toggleMenu() {
        if (menuOverlay.getVisibility() == View.VISIBLE) {
            closeMenu();
        } else {
            openMenu(false);
        }
    }

    private void openMenu(boolean focusSearch) {
        menuSearch.setText("");
        menuAdapter.setApps(apps);
        if (tileAdapter != null) {
            tileAdapter.setApps(pinnedApps());
        }
        menuOverlay.setAlpha(0f);
        menuOverlay.setVisibility(View.VISIBLE);
        menuOverlay.animate().alpha(1f).setDuration(140).start();
        if (focusSearch || style == NovaStyle.MAC) {
            menuSearch.requestFocus();
            if (focusSearch) {
                InputMethodManager imm = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
                menuSearch.post(() -> imm.showSoftInput(menuSearch, InputMethodManager.SHOW_IMPLICIT));
            }
        }
    }

    private void closeMenu() {
        if (menuOverlay == null || menuOverlay.getVisibility() != View.VISIBLE) {
            return;
        }
        InputMethodManager imm = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
        imm.hideSoftInputFromWindow(menuSearch.getWindowToken(), 0);
        menuOverlay.setVisibility(View.GONE);
    }

    // --- actions --------------------------------------------------------------------

    private void launch(AppEntry app) {
        Intent intent = new Intent(Intent.ACTION_MAIN)
                .addCategory(Intent.CATEGORY_LAUNCHER)
                .setComponent(app.component)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
        if (startSafely(intent)) {
            closeMenu();
        }
    }

    private boolean startSafely(Intent intent) {
        try {
            startActivity(intent);
            return true;
        } catch (ActivityNotFoundException | SecurityException e) {
            Toast.makeText(this, "Açılamadı: " + e.getMessage(), Toast.LENGTH_SHORT).show();
            return false;
        }
    }

    private void showAppOptions(View anchor, AppEntry app) {
        PopupMenu menu = new PopupMenu(this, anchor);
        boolean pinned = isPinned(app);
        String where = style == NovaStyle.MAC ? "Dock'a" : "Görev çubuğuna";
        menu.getMenu().add(0, 1, 0, pinned ? "Sabitlemeyi kaldır" : where + " sabitle");
        menu.getMenu().add(0, 2, 1, "Uygulama bilgisi");
        menu.getMenu().add(0, 3, 2, "Kaldır");
        menu.setOnMenuItemClickListener(item -> {
            Uri uri = Uri.fromParts("package", app.packageName(), null);
            switch (item.getItemId()) {
                case 1:
                    setPinned(app, !pinned);
                    if (tileAdapter != null) {
                        tileAdapter.setApps(pinnedApps());
                    }
                    return true;
                case 2:
                    startSafely(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, uri));
                    return true;
                case 3:
                    startSafely(new Intent(Intent.ACTION_DELETE, uri));
                    return true;
                default:
                    return false;
            }
        });
        menu.show();
    }

    private void openSettings() {
        startSafely(new Intent(this, SettingsActivity.class));
    }

    private void updateClock() {
        if (bigClock == null) {
            return;
        }
        Date now = new Date();
        String time = new SimpleDateFormat(clock24h ? "HH:mm" : "hh:mm a", TR).format(now);
        bigClock.setText(time);
        bigDate.setText(new SimpleDateFormat("d MMMM EEEE", TR).format(now));
        if (barClock != null) {
            barClock.setText(style == NovaStyle.XP ? time
                    : time + "\n" + new SimpleDateFormat("dd.MM.yyyy", TR).format(now));
        }
    }
}
