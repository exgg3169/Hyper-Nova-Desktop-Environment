package org.hypernova.launcher;

import android.content.ComponentName;
import android.graphics.drawable.Drawable;

/** One launchable activity. */
public final class AppEntry {
    public final String label;
    public final ComponentName component;
    public final Drawable icon;

    public AppEntry(String label, ComponentName component, Drawable icon) {
        this.label = label;
        this.component = component;
        this.icon = icon;
    }

    public String key() {
        return component.flattenToString();
    }

    public String packageName() {
        return component.getPackageName();
    }
}
