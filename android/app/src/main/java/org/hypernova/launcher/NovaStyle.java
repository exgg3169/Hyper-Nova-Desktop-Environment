package org.hypernova.launcher;

/** The four HyperNova looks, mirroring the desktop styles. */
public enum NovaStyle {
    XP("xp", "Klasik XP", "Mavi görev çubuğu, yeşil Başlat düğmesi ve klasik Başlat menüsü."),
    WIN7("win7", "Aero 7", "Cam görünümlü görev çubuğu, yuvarlak Başlat küresi ve aramalı menü."),
    WIN10("win10", "Modern 10", "Düz koyu görev çubuğu, arama kutusu, kutucuklar ve uygulama listesi."),
    MAC("mac", "Nova Mac", "Ortalanmış Dock ve tam ekran uygulama başlatıcı.");

    public final String id;
    public final String title;
    public final String description;

    NovaStyle(String id, String title, String description) {
        this.id = id;
        this.title = title;
        this.description = description;
    }

    public static NovaStyle from(String id) {
        for (NovaStyle style : values()) {
            if (style.id.equals(id)) {
                return style;
            }
        }
        return WIN10;
    }

    public boolean hasTaskbar() {
        return this != MAC;
    }

    /** Colour of the system navigation bar so it blends with the taskbar or dock. */
    public int navigationBarColor() {
        switch (this) {
            case XP:
                return 0xFF1941A5;
            case WIN7:
                return 0xFF142A42;
            case WIN10:
                return 0xFF101010;
            default:
                return 0xFF2A1A45;
        }
    }
}
