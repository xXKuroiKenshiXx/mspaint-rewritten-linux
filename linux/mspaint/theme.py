"""Consistent typography across Linux distributions without Windows font files."""
from pathlib import Path
from PySide6.QtGui import QFont,QFontDatabase
from PySide6.QtWidgets import QApplication

_loaded=False

def install_fonts():
    global _loaded
    if not _loaded:
        directory=Path(__file__).resolve().parent/"assets/fonts"
        for path in sorted(directory.glob("*.ttf")):QFontDatabase.addApplicationFont(str(path))
        QFont.insertSubstitution("Segoe UI","Selawik")
        QFont.insertSubstitution("Calibri","Carlito")
        _loaded=True
    QApplication.instance().setFont(QFont("Segoe UI",9))
