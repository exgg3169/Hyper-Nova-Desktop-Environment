package org.hypernova.launcher;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

/** HyperNova Ayarları: style picker, clock format and default-launcher shortcut. */
public class SettingsActivity extends Activity {
    private static final int MATCH = ViewGroup.LayoutParams.MATCH_PARENT;
    private static final int WRAP = ViewGroup.LayoutParams.WRAP_CONTENT;

    private Prefs prefs;
    private LinearLayout styleList;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = new Prefs(this);

        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(18), dp(12), dp(18), dp(24));

        content.addView(title("Masaüstü stili"));
        content.addView(subtitle("HyperNova'nın görünümünü seçin. Ana ekran hemen güncellenir."));
        styleList = new LinearLayout(this);
        styleList.setOrientation(LinearLayout.VERTICAL);
        content.addView(styleList);
        renderStyles();

        content.addView(title("Saat"));
        Switch clock = new Switch(this);
        clock.setText("24 saat biçimini kullan");
        clock.setTextSize(15);
        clock.setChecked(prefs.clock24h());
        clock.setOnCheckedChangeListener((button, checked) -> prefs.setClock24h(checked));
        content.addView(clock, new LinearLayout.LayoutParams(MATCH, dp(48)));

        content.addView(title("Başlatıcı"));
        Button makeDefault = new Button(this);
        makeDefault.setText("HyperNova'yı varsayılan ana ekran yap");
        makeDefault.setOnClickListener(v -> {
            try {
                startActivity(new Intent(Settings.ACTION_HOME_SETTINGS));
            } catch (ActivityNotFoundException e) {
                Toast.makeText(this, "Ana ekran ayarı bu cihazda bulunamadı", Toast.LENGTH_SHORT).show();
            }
        });
        content.addView(makeDefault, new LinearLayout.LayoutParams(MATCH, WRAP));

        content.addView(title("Hakkında"));
        content.addView(subtitle("HyperNova Launcher 0.1.0\nHyperNova OS'un mobil başlatıcısı.\n"
                + "MIT lisanslı, tamamen açık kaynak:\ngithub.com/exgg3169/Hyper-Nova-Desktop-Environment"));

        ScrollView scroll = new ScrollView(this);
        scroll.addView(content);
        setContentView(scroll);
    }

    private void renderStyles() {
        styleList.removeAllViews();
        NovaStyle current = prefs.style();
        for (NovaStyle style : NovaStyle.values()) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(Gravity.CENTER_VERTICAL);
            row.setPadding(dp(8), dp(8), dp(8), dp(8));
            GradientDrawable bg = Ui.solid(style == current ? 0x1F0063B1 : Color.TRANSPARENT, dp(10));
            bg.setStroke(dp(2), style == current ? 0xFF0063B1 : 0x00000000);
            row.setBackground(bg);

            WallpaperView preview = new WallpaperView(this, style);
            preview.setClipToOutline(true);
            preview.setBackground(Ui.solid(Color.BLACK, dp(8)));
            row.addView(preview, new LinearLayout.LayoutParams(dp(120), dp(80)));

            LinearLayout texts = new LinearLayout(this);
            texts.setOrientation(LinearLayout.VERTICAL);
            texts.setPadding(dp(14), 0, 0, 0);
            TextView name = new TextView(this);
            name.setText(style.title);
            name.setTextSize(17);
            name.setTypeface(Typeface.DEFAULT_BOLD);
            name.setTextColor(0xFF1C1C1C);
            texts.addView(name);
            TextView description = new TextView(this);
            description.setText(style.description);
            description.setTextColor(0xFF666666);
            texts.addView(description);
            row.addView(texts, new LinearLayout.LayoutParams(0, WRAP, 1));

            row.setOnClickListener(v -> {
                prefs.setStyle(style);
                renderStyles();
            });
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(MATCH, WRAP);
            lp.bottomMargin = dp(8);
            styleList.addView(row, lp);
        }
    }

    private TextView title(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(20);
        view.setTypeface(Typeface.DEFAULT_BOLD);
        view.setTextColor(0xFF1C1C1C);
        view.setPadding(0, dp(18), 0, dp(6));
        return view;
    }

    private TextView subtitle(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextColor(0xFF666666);
        view.setPadding(0, 0, 0, dp(10));
        return view;
    }

    private int dp(float value) {
        return Ui.dp(this, value);
    }
}
