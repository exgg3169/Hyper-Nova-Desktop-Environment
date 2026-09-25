package org.hypernova.launcher;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.net.Uri;
import android.provider.MediaStore;
import android.provider.Settings;

import java.text.Collator;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Loads the apps that have a launcher entry. Call {@link #load} off the UI thread. */
public final class AppRepository {
    private AppRepository() {
    }

    public static List<AppEntry> load(Context context) {
        PackageManager pm = context.getPackageManager();
        Intent main = new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> infos = pm.queryIntentActivities(main, 0);
        List<AppEntry> apps = new ArrayList<>();
        for (ResolveInfo info : infos) {
            String pkg = info.activityInfo.packageName;
            if (pkg.equals(context.getPackageName())) {
                continue;
            }
            ComponentName component = new ComponentName(pkg, info.activityInfo.name);
            apps.add(new AppEntry(String.valueOf(info.loadLabel(pm)), component, info.loadIcon(pm)));
        }
        Collator collator = Collator.getInstance(new Locale("tr", "TR"));
        apps.sort((a, b) -> collator.compare(a.label, b.label));
        return apps;
    }

    /** Picks a first set of pinned apps: phone, messages, browser, camera, gallery, settings. */
    public static List<String> defaultPinned(Context context, List<AppEntry> apps) {
        Intent[] intents = {
            new Intent(Intent.ACTION_DIAL),
            Intent.makeMainSelectorActivity(Intent.ACTION_MAIN, Intent.CATEGORY_APP_MESSAGING),
            new Intent(Intent.ACTION_VIEW, Uri.parse("https://hypernova.invalid")),
            new Intent(MediaStore.ACTION_IMAGE_CAPTURE),
            Intent.makeMainSelectorActivity(Intent.ACTION_MAIN, Intent.CATEGORY_APP_GALLERY),
            new Intent(Settings.ACTION_SETTINGS),
        };
        PackageManager pm = context.getPackageManager();
        List<String> pinned = new ArrayList<>();
        for (Intent intent : intents) {
            ResolveInfo info = pm.resolveActivity(intent, PackageManager.MATCH_DEFAULT_ONLY);
            if (info == null || info.activityInfo == null) {
                continue;
            }
            String pkg = info.activityInfo.packageName;
            for (AppEntry app : apps) {
                if (app.packageName().equals(pkg) && !pinned.contains(app.key())) {
                    pinned.add(app.key());
                    break;
                }
            }
        }
        if (pinned.isEmpty()) {
            for (int i = 0; i < Math.min(4, apps.size()); i++) {
                pinned.add(apps.get(i).key());
            }
        }
        return pinned;
    }
}
