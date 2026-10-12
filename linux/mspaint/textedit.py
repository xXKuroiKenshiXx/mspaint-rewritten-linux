"""Inline Paint text box; text stays editable until the user commits it."""
from PySide6.QtCore import Qt,QPoint,QRect
from PySide6.QtGui import QColor,QPalette,QPainter,QFont
from PySide6.QtWidgets import QPlainTextEdit,QFrame,QWidget


class TextGrip(QWidget):
    def __init__(self,editor,name):
        super().__init__(editor.canvas)
        self.editor,self.name=editor,name
        self.setFixedSize(6,6)
        self.setStyleSheet("background:white;border:1px solid #555;")
        self.setCursor(Qt.CursorShape.SizeHorCursor if name in ("left","right") else Qt.CursorShape.SizeVerCursor if name in ("top","bottom") else Qt.CursorShape.SizeFDiagCursor if name in ("tl","br") else Qt.CursorShape.SizeBDiagCursor)

    def mousePressEvent(self,event):
        self.original=QRect(self.editor.image_rect)

    def mouseMoveEvent(self,event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            canvas=self.editor.canvas
            location=canvas.mapFromGlobal(event.globalPosition().toPoint())
            point=QPoint(round(location.x()/canvas.zoom),round(location.y()/canvas.zoom))
            self.editor.image_rect=canvas.resized_rect(self.original,point,self.name)
            canvas.selection=QRect(self.editor.image_rect)
            self.editor.sync_geometry();canvas.update()

    def mouseReleaseEvent(self,event):
        self.editor.canvas.window.refresh()


class PaintTextEdit(QPlainTextEdit):
    def __init__(self,canvas,rect):
        super().__init__(canvas)
        self.canvas = canvas
        self.image_rect = rect
        self.grips={name:TextGrip(self,name) for name in ("tl","top","tr","left","right","bl","bottom","br")}
        self.moving=False
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.document().setDocumentMargin(0)
        self.setFont(canvas.font)
        self.setStyleSheet("QPlainTextEdit{border:1px dashed #666;padding:1px;background:transparent;}")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.viewport().setAutoFillBackground(False)
        self.textChanged.connect(lambda:(canvas.update(),canvas.window.refresh()))
        self.update_style()
        self.sync_geometry()
        self.show();self.setFocus()
        self.canvas.selection=QRect(self.image_rect)

    def sync_geometry(self):
        r = self.image_rect;z = self.canvas.zoom
        self.setGeometry(round(r.x()*z),round(r.y()*z),max(2,round(r.width()*z)),max(2,round(r.height()*z)))
        self.canvas.selection=QRect(r)
        handles=self.canvas.selection_handles()
        for name,grip in self.grips.items():
            point=handles[name]
            grip.move(round(point.x()*z)-3,round(point.y()*z)-3);grip.show();grip.raise_()
        self.update_style()

    def destroy_grips(self):
        for grip in self.grips.values():grip.hide();grip.deleteLater()
        self.grips={}

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and event.position().y()<3:
            self.moving=True;self.start=event.globalPosition().toPoint();self.original=QRect(self.image_rect);event.accept()
        else:super().mousePressEvent(event)

    def mouseMoveEvent(self,event):
        if self.moving:
            delta=event.globalPosition().toPoint()-self.start
            self.image_rect=self.original.translated(round(delta.x()/self.canvas.zoom),round(delta.y()/self.canvas.zoom))
            self.sync_geometry();self.canvas.update()
        else:super().mouseMoveEvent(event)

    def mouseReleaseEvent(self,event):
        if self.moving:self.moving=False
        else:super().mouseReleaseEvent(event)

    def update_style(self):
        font = QFont(self.canvas.font)
        if font.pixelSize()>0:font.setPixelSize(max(1,round(font.pixelSize()*self.canvas.zoom)))
        else:font.setPointSizeF(max(1,font.pointSizeF()*self.canvas.zoom))
        self.setFont(font)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Text,self.canvas.foreground)
        palette.setColor(QPalette.ColorRole.Base,self.canvas.background if self.canvas.text_opaque else QColor(0,0,0,0))
        self.setPalette(palette)
        background = self.canvas.background.name() if self.canvas.text_opaque else "transparent"
        self.setStyleSheet(f"QPlainTextEdit{{border:1px dashed #666;padding:1px;background:{background};color:{self.canvas.foreground.name()};}}")

    def keyPressEvent(self,event):
        if event.key() == Qt.Key.Key_Escape:
            self.canvas.cancel_text()
        elif event.key() in (Qt.Key.Key_Enter,Qt.Key.Key_Return) and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.canvas.finish_text()
        else:
            super().keyPressEvent(event)
