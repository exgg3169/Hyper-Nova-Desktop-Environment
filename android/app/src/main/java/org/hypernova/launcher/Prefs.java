package org.hypernova.launcher;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Small wrapper around the launcher's SharedPreferences. */
public final class Prefs {
    private static final String KEY_STYLE = "style";
    private static final String KEY_PINNED = "pinned";
    private static final String KEY_CLOCK_24H = "clock_24h";

    private final SharedPreferences prefs;

    public Prefs(Context context) {
        prefs = context.getSharedPreferences("hypernova", Context.MODE_PRIVATE);
    }

    public NovaStyle style() {
        return NovaStyle.from(prefs.getString(KEY_STYLE, NovaStyle.WIN10.id));
    }

    public void setStyle(NovaStyle style) {
        prefs.edit().putString(KEY_STYLE, style.id).apply();
    }

    public boolean clock24h() {
        return prefs.getBoolean(KEY_CLOCK_24H, true);
    }

    public void setClock24h(boolean value) {
        prefs.edit().putBoolean(KEY_CLOCK_24H, value).apply();
    }

    /** Pinned component names, or null when the user never changed them. */
    public List<String> pinned() {
        String raw = prefs.getString(KEY_PINNED, null);
        if (raw == null) {
            return null;
        }
        List<String> result = new ArrayList<>();
        for (String item : Arrays.asList(raw.split("\n"))) {
            if (!item.isEmpty()) {
                result.add(item);
            }
        }
        return result;
    }

    public void setPinned(List<String> pinned) {
        prefs.edit().putString(KEY_PINNED, String.join("\n", pinned)).apply();
    }
}
