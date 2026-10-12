"""Wallpaper via freedesktop portal, with desktop-owned confirmation."""
from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusUnixFileDescriptor, QDBusMessage


def set_wallpaper(parent, path):
    bus = QDBusConnection.sessionBus()
    portal = QDBusInterface("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop",
                           "org.freedesktop.portal.Wallpaper", bus)
    if not portal.isValid():
        raise OSError("This desktop has no Wallpaper portal. Install a compatible xdg-desktop-portal backend.")
    # Empty parent identifier is allowed by the portal; do not fabricate Wayland/X11 handles.
    with open(path, "rb") as source:
        reply = portal.call("SetWallpaperFile", "", QDBusUnixFileDescriptor(source.fileno()),
                            {"show-preview": True, "set-on": "background"})
    if reply.type() == QDBusMessage.MessageType.ErrorMessage:
        raise OSError(reply.errorMessage())
