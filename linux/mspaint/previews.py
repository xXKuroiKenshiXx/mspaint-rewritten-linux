"""Independent thumbnail and fullscreen image windows, like the Delphi forms."""
from PySide6.QtCore import Qt,QPoint
from PySide6.QtGui import QPainter,QColor,QPixmap
from PySide6.QtWidgets import QWidget,QDialog,QLabel,QVBoxLayout


class FullscreenPreview(QWidget):
    def __init__(self,window):
        super().__init__(window,Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint)
        self.window=window;self.image=window.doc.image.copy()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor("black"))
        image=self.image.scaled(self.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        p.drawImage((self.width()-image.width())//2,(self.height()-image.height())//2,image);p.end()

    def mousePressEvent(self,event):self.close()

    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Escape,Qt.Key.Key_F11):self.close()
        else:super().keyPressEvent(event)

    def closeEvent(self,event):
        self.window.fullscreen_preview=None;super().closeEvent(event)


class ThumbnailPreview(QDialog):
    def __init__(self,window):
        super().__init__(window,Qt.WindowType.Tool)
        self.window=window;self.setWindowTitle("Thumbnail")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(753,439);self.setMinimumSize(120,90)
        self.label=QLabel(self);self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.addWidget(self.label)
        self.move(window.pos()+QPoint(60,60));self.refresh()

    def refresh(self):
        self.label.setPixmap(QPixmap.fromImage(self.window.doc.image).scaled(self.label.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self,event):
        super().resizeEvent(event);self.refresh()

    def closeEvent(self,event):
        self.window.thumbnail_preview=None;self.window.thumbnail=None;super().closeEvent(event)
