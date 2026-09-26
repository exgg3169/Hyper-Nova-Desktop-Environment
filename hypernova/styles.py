"""The selectable desktop styles.

Each style decides the shell layout (a Windows-like taskbar or a Mac-like
menu bar + dock), which start menu is used, and which Openbox window theme
decorates application windows.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Style:
    id: str
    name: str
    description: str
    layout: str            # "taskbar" or "mac"
    menu: str              # start menu flavour
    panel_height: int      # taskbar height, or menu bar height for "mac"
    task_labels: bool      # task buttons show window titles
    task_icon_size: int
    openbox_theme: str
    title_layout: str      # Openbox titlebar button order
    wallpaper: str
    computer_label: str
    home_label: str
    trash_label: str
    dock_icon_size: int = 0


STYLES = {
    "xp": Style(
        id="xp", name="Klasik XP",
        description="Mavi görev çubuğu, yeşil Başlat düğmesi ve iki sütunlu Başlat menüsü.",
        layout="taskbar", menu="xp", panel_height=34, task_labels=True, task_icon_size=16,
        openbox_theme="HyperNova-XP", title_layout="NLIMC", wallpaper="bliss",
        computer_label="Bilgisayarım", home_label="Belgelerim", trash_label="Geri Dönüşüm Kutusu",
    ),
    "win7": Style(
        id="win7", name="Aero 7",
        description="Cam görünümlü süper çubuk, yuvarlak Başlat küresi ve aramalı menü.",
        layout="taskbar", menu="win7", panel_height=42, task_labels=False, task_icon_size=26,
        openbox_theme="HyperNova-7", title_layout="NLIMC", wallpaper="harmony",
        computer_label="Bilgisayar", home_label="Kişisel Klasör", trash_label="Geri Dönüşüm Kutusu",
    ),
    "win10": Style(
        id="win10", name="Modern 10",
        description="Düz koyu görev çubuğu, arama kutusu, uygulama listesi ve kutucuklar.",
        layout="taskbar", menu="win10", panel_height=42, task_labels=False, task_icon_size=24,
        openbox_theme="HyperNova-10", title_layout="NLIMC", wallpaper="hero",
        computer_label="Bu Bilgisayar", home_label="Kişisel Klasör", trash_label="Geri Dönüşüm Kutusu",
    ),
    "mac": Style(
        id="mac", name="Nova Mac",
        description="Üstte menü çubuğu, altta ortalanmış Dock ve tam ekran uygulama başlatıcı.",
        layout="mac", menu="launchpad", panel_height=28, task_labels=False, task_icon_size=0,
        openbox_theme="HyperNova-Mac", title_layout="CIML", wallpaper="sierra",
        computer_label="Nova HD", home_label="Ev", trash_label="Çöp Sepeti",
        dock_icon_size=52,
    ),
}

ORDER = ["xp", "win7", "win10", "mac"]
DEFAULT = "win10"


def get(style_id):
    return STYLES.get(style_id) or STYLES[DEFAULT]
