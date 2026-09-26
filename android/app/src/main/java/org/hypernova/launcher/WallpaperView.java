package org.hypernova.launcher;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.view.View;

/** Draws the built-in wallpaper of each style (same scenes as the desktop). */
public class WallpaperView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private NovaStyle style;

    public WallpaperView(Context context, NovaStyle style) {
        super(context);
        this.style = style;
    }

    public void setStyle(NovaStyle style) {
        this.style = style;
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        float w = getWidth();
        float h = getHeight();
        switch (style) {
            case XP:
                bliss(canvas, w, h);
                break;
            case WIN7:
                harmony(canvas, w, h);
                break;
            case WIN10:
                hero(canvas, w, h);
                break;
            default:
                sierra(canvas, w, h);
                break;
        }
        paint.setShader(null);
    }

    private void fill(Canvas canvas, Shader shader, float w, float h) {
        paint.setShader(shader);
        canvas.drawRect(0, 0, w, h, paint);
    }

    private void softEllipse(Canvas canvas, float cx, float cy, float rx, float ry, int color) {
        canvas.save();
        canvas.translate(cx, cy);
        canvas.scale(rx, ry);
        paint.setShader(new RadialGradient(0, 0, 1, color, color & 0x00FFFFFF, Shader.TileMode.CLAMP));
        canvas.drawCircle(0, 0, 1, paint);
        canvas.restore();
    }

    private void bliss(Canvas canvas, float w, float h) {
        fill(canvas, new LinearGradient(0, 0, 0, h * 0.75f, new int[] {0xFF1B5BD4, 0xFF4F95EE, 0xFFB4D5FA},
                new float[] {0f, 0.55f, 1f}, Shader.TileMode.CLAMP), w, h);
        float[][] clouds = {{0.2f, 0.16f, 0.3f, 0.05f}, {0.75f, 0.24f, 0.35f, 0.05f}, {0.45f, 0.32f, 0.25f, 0.04f}};
        for (float[] c : clouds) {
            softEllipse(canvas, c[0] * w, c[1] * h, c[2] * w, c[3] * h, 0xD9FFFFFF);
        }
        Path back = new Path();
        back.moveTo(0, h * 0.64f);
        back.cubicTo(w * 0.28f, h * 0.52f, w * 0.62f, h * 0.57f, w, h * 0.62f);
        back.lineTo(w, h);
        back.lineTo(0, h);
        back.close();
        paint.setShader(new LinearGradient(0, h * 0.5f, 0, h, 0xFF5FAE2E, 0xFF23660B, Shader.TileMode.CLAMP));
        canvas.drawPath(back, paint);
        Path front = new Path();
        front.moveTo(0, h * 0.82f);
        front.cubicTo(w * 0.3f, h * 0.62f, w * 0.66f, h * 0.66f, w, h * 0.76f);
        front.lineTo(w, h);
        front.lineTo(0, h);
        front.close();
        paint.setShader(new LinearGradient(0, h * 0.62f, 0, h, new int[] {0xFF8FD44C, 0xFF56A824, 0xFF2F7D12},
                new float[] {0f, 0.5f, 1f}, Shader.TileMode.CLAMP));
        canvas.drawPath(front, paint);
    }

    private void harmony(Canvas canvas, float w, float h) {
        fill(canvas, new RadialGradient(w * 0.5f, h * 0.45f, Math.max(w, h) * 0.75f,
                new int[] {0xFF2A9BE8, 0xFF0E5AA7, 0xFF031A3D}, new float[] {0f, 0.45f, 1f}, Shader.TileMode.CLAMP), w, h);
        int[] colors = {0x5943C6FF, 0x597EE8FA, 0x593D7BFF, 0x59A0F0FF};
        paint.setStyle(Paint.Style.STROKE);
        for (int i = 0; i < colors.length; i++) {
            Path ribbon = new Path();
            float y = h * (0.42f + i * 0.05f);
            ribbon.moveTo(-w * 0.1f, y + h * 0.08f);
            ribbon.cubicTo(w * 0.25f, y - h * 0.12f, w * 0.6f, y + h * 0.14f, w * 1.1f, y - h * 0.02f);
            paint.setStrokeWidth(h * (0.03f - i * 0.005f));
            paint.setShader(new LinearGradient(0, 0, w, 0, new int[] {0, colors[i], 0}, null, Shader.TileMode.CLAMP));
            canvas.drawPath(ribbon, paint);
        }
        paint.setStyle(Paint.Style.FILL);
    }

    private void hero(Canvas canvas, float w, float h) {
        fill(canvas, new LinearGradient(0, 0, w, h, new int[] {0xFF00132E, 0xFF002F6C, 0xFF004A9F},
                new float[] {0f, 0.6f, 1f}, Shader.TileMode.CLAMP), w, h);
        float s = Math.min(w, h);
        float pw = s * 0.26f;
        float ph = s * 0.3f;
        float gap = s * 0.02f;
        float ox = w * 0.5f - pw * 0.6f;
        float oy = h * 0.3f;
        for (int col = 0; col < 2; col++) {
            for (int row = 0; row < 2; row++) {
                float x0 = ox + col * (pw + gap);
                float x1 = x0 + pw;
                float y0 = oy + row * (ph + gap) + col * s * 0.04f;
                Path pane = new Path();
                pane.moveTo(x0, y0);
                pane.lineTo(x1, y0 - s * 0.015f + s * 0.03f);
                pane.lineTo(x1, y0 + ph + s * 0.03f);
                pane.lineTo(x0, y0 + ph);
                pane.close();
                Path ray = new Path();
                ray.moveTo(0, h * 0.95f);
                ray.lineTo(x0, y0);
                ray.lineTo(x0, y0 + ph);
                ray.close();
                paint.setShader(new LinearGradient(0, h, x0, y0, 0x000A4EA8, 0x383A9BFF, Shader.TileMode.CLAMP));
                canvas.drawPath(ray, paint);
                paint.setShader(new LinearGradient(x0, y0, x1, y0 + ph, new int[] {0xFF8FD0FF, 0xFF2F8CFF, 0xFF0D5FD8},
                        null, Shader.TileMode.CLAMP));
                canvas.drawPath(pane, paint);
            }
        }
    }

    private void sierra(Canvas canvas, float w, float h) {
        fill(canvas, new LinearGradient(0, 0, 0, h, new int[] {0xFF2B2D6E, 0xFFB35F86, 0xFFF2A36B, 0xFFF7C98B},
                new float[] {0f, 0.45f, 0.75f, 1f}, Shader.TileMode.CLAMP), w, h);
        softEllipse(canvas, w * 0.7f, h * 0.52f, w * 0.4f, h * 0.15f, 0x73FFD9A0);
        float[][] ridges = {
            {0.55f, 0, .05f, .15f, .01f, .3f, .08f, .45f, .02f, .6f, .09f, .75f, .02f, .9f, .07f, 1, .04f},
            {0.66f, 0, .06f, .12f, .01f, .27f, .08f, .42f, .02f, .58f, .07f, .7f, .0f, .85f, .06f, 1, .03f},
            {0.8f, 0, .04f, .15f, .0f, .33f, .06f, .5f, .02f, .66f, .07f, .82f, .01f, 1, .05f},
        };
        int[] colors = {0xFF7A4A86, 0xFF4F2E6B, 0xFF2A1A45};
        paint.setShader(null);
        for (int r = 0; r < ridges.length; r++) {
            float base = ridges[r][0];
            Path path = new Path();
            path.moveTo(0, h);
            for (int i = 1; i + 1 < ridges[r].length; i += 2) {
                path.lineTo(ridges[r][i] * w, (base - 0.12f + ridges[r][i + 1]) * h);
            }
            path.lineTo(w, h);
            path.close();
            paint.setColor(colors[r]);
            canvas.drawPath(path, paint);
        }
    }
}
