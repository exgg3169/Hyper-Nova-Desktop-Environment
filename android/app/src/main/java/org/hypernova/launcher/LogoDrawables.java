package org.hypernova.launcher;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.RadialGradient;
import android.graphics.Rect;
import android.graphics.Shader;
import android.graphics.drawable.Drawable;

/** Vector-free drawables for the HyperNova star, the "window" logo and the Aero orb. */
public final class LogoDrawables {
    private LogoDrawables() {
    }

    private abstract static class Base extends Drawable {
        final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);

        @Override
        public void setAlpha(int alpha) {
            paint.setAlpha(alpha);
        }

        @Override
        public void setColorFilter(ColorFilter filter) {
            paint.setColorFilter(filter);
        }

        @Override
        public int getOpacity() {
            return PixelFormat.TRANSLUCENT;
        }
    }

    /** The eight-point HyperNova star; {@code mono} draws it in one flat colour. */
    public static Drawable star(final Integer mono) {
        return new Base() {
            @Override
            public void draw(Canvas canvas) {
                Rect b = getBounds();
                float s = Math.min(b.width(), b.height()) / 64f;
                canvas.save();
                canvas.translate(b.left + (b.width() - 64 * s) / 2, b.top + (b.height() - 64 * s) / 2);
                canvas.scale(s, s);
                Path path = new Path();
                for (int i = 0; i < 8; i++) {
                    double angle = -Math.PI / 2 + i * Math.PI / 4;
                    float radius = i % 2 == 0 ? 29 : 10;
                    float x = (float) (32 + radius * Math.cos(angle));
                    float y = (float) (32 + radius * Math.sin(angle));
                    if (i == 0) {
                        path.moveTo(x, y);
                    } else {
                        path.lineTo(x, y);
                    }
                }
                path.close();
                if (mono != null) {
                    paint.setShader(null);
                    paint.setColor(mono);
                    canvas.drawPath(path, paint);
                } else {
                    paint.setShader(new LinearGradient(0, 0, 64, 64, 0xFF22D3EE, 0xFFA855F7, Shader.TileMode.CLAMP));
                    canvas.drawPath(path, paint);
                    paint.setShader(new RadialGradient(32, 32, 15, new int[] {0xFFFFFFFF, 0xF2C4B5FD, 0x007C3AED},
                            new float[] {0f, 0.4f, 1f}, Shader.TileMode.CLAMP));
                    canvas.drawCircle(32, 32, 15, paint);
                }
                canvas.restore();
            }
        };
    }

    /** Four square panes (Modern 10 start button). */
    public static Drawable panes(final int color) {
        return new Base() {
            @Override
            public void draw(Canvas canvas) {
                Rect b = getBounds();
                float size = Math.min(b.width(), b.height());
                float gap = Math.max(1, size / 12f);
                float half = (size - gap) / 2f;
                float left = b.left + (b.width() - size) / 2f;
                float top = b.top + (b.height() - size) / 2f;
                paint.setColor(color);
                canvas.drawRect(left, top, left + half, top + half, paint);
                canvas.drawRect(left + half + gap, top, left + size, top + half, paint);
                canvas.drawRect(left, top + half + gap, left + half, top + size, paint);
                canvas.drawRect(left + half + gap, top + half + gap, left + size, top + size, paint);
            }
        };
    }

    /** Glossy blue orb with the HyperNova star (Aero 7 start button). */
    public static Drawable orb() {
        final Drawable star = star(null);
        return new Base() {
            @Override
            public void draw(Canvas canvas) {
                Rect b = getBounds();
                float r = Math.min(b.width(), b.height()) / 2f;
                float cx = b.exactCenterX();
                float cy = b.exactCenterY();
                paint.setShader(new RadialGradient(cx, cy - r * 0.2f, r, new int[] {0xFF8CD9FF, 0xFF1A66BF, 0xFF052659},
                        new float[] {0f, 0.6f, 1f}, Shader.TileMode.CLAMP));
                canvas.drawCircle(cx, cy, r, paint);
                paint.setShader(new LinearGradient(0, cy - r, 0, cy, 0x8CFFFFFF, 0x00FFFFFF, Shader.TileMode.CLAMP));
                canvas.drawOval(cx - r * 0.72f, cy - r * 0.92f, cx + r * 0.72f, cy - r * 0.05f, paint);
                paint.setShader(null);
                int inset = Math.round(r * 0.45f);
                star.setBounds(b.left + inset, b.top + inset, b.right - inset, b.bottom - inset);
                star.draw(canvas);
            }
        };
    }
}
