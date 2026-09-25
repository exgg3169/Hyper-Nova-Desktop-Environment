package org.hypernova.launcher;

import android.content.Context;
import android.graphics.Color;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AbsListView;
import android.widget.BaseAdapter;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Adapter for app lists (rows), launchpad grids and Modern 10 tiles. */
public final class AppAdapter extends BaseAdapter {
    public enum Mode { LIST, GRID, TILE }

    private static final int[] TILE_COLORS = {0xFF0063B1, 0xFF00828A, 0xFF6B42B8, 0xFF107C10, 0xFFC75000, 0xFFB4282E};

    private final Context context;
    private final Mode mode;
    private final int textColor;
    private final List<AppEntry> all = new ArrayList<>();
    private final List<AppEntry> shown = new ArrayList<>();

    public AppAdapter(Context context, Mode mode, int textColor) {
        this.context = context;
        this.mode = mode;
        this.textColor = textColor;
    }

    public void setApps(List<AppEntry> apps) {
        all.clear();
        all.addAll(apps);
        filter("");
    }

    public void filter(String query) {
        String q = query.trim().toLowerCase(new Locale("tr"));
        shown.clear();
        for (AppEntry app : all) {
            if (q.isEmpty() || app.label.toLowerCase(new Locale("tr")).contains(q)) {
                shown.add(app);
            }
        }
        notifyDataSetChanged();
    }

    @Override
    public int getCount() {
        return shown.size();
    }

    @Override
    public AppEntry getItem(int position) {
        return shown.get(position);
    }

    @Override
    public long getItemId(int position) {
        return position;
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        AppEntry app = getItem(position);
        LinearLayout cell = (LinearLayout) convertView;
        if (cell == null) {
            cell = createCell();
        }
        ImageView icon = (ImageView) cell.getChildAt(0);
        TextView label = (TextView) cell.getChildAt(1);
        icon.setImageDrawable(app.icon);
        label.setText(app.label);
        if (mode == Mode.TILE) {
            cell.setBackgroundColor(TILE_COLORS[position % TILE_COLORS.length]);
        }
        return cell;
    }

    private LinearLayout createCell() {
        LinearLayout cell = new LinearLayout(context);
        ImageView icon = new ImageView(context);
        TextView label = new TextView(context);
        label.setTextColor(textColor);
        label.setSingleLine(true);
        label.setEllipsize(TextUtils.TruncateAt.END);
        int pad = Ui.dp(context, 6);
        switch (mode) {
            case LIST:
                cell.setOrientation(LinearLayout.HORIZONTAL);
                cell.setGravity(Gravity.CENTER_VERTICAL);
                cell.setPadding(pad * 2, pad, pad * 2, pad);
                cell.addView(icon, new LinearLayout.LayoutParams(Ui.dp(context, 36), Ui.dp(context, 36)));
                label.setTextSize(15);
                label.setPadding(pad * 2, 0, 0, 0);
                cell.addView(label, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
                break;
            case GRID:
                cell.setOrientation(LinearLayout.VERTICAL);
                cell.setGravity(Gravity.CENTER_HORIZONTAL);
                cell.setPadding(pad, pad * 2, pad, pad);
                cell.addView(icon, new LinearLayout.LayoutParams(Ui.dp(context, 56), Ui.dp(context, 56)));
                label.setTextSize(12);
                label.setGravity(Gravity.CENTER);
                label.setShadowLayer(4, 0, 1, Color.BLACK);
                label.setPadding(0, pad, 0, 0);
                cell.addView(label, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT));
                break;
            default:
                cell.setOrientation(LinearLayout.VERTICAL);
                cell.setGravity(Gravity.CENTER);
                cell.setPadding(pad, pad, pad, pad);
                cell.setLayoutParams(new AbsListView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                        Ui.dp(context, 84)));
                cell.addView(icon, new LinearLayout.LayoutParams(Ui.dp(context, 36), Ui.dp(context, 36)));
                label.setTextSize(11);
                label.setGravity(Gravity.CENTER);
                label.setPadding(0, pad, 0, 0);
                cell.addView(label, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT));
                break;
        }
        return cell;
    }
}
