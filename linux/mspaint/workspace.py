"""Paint canvas gutters, original rulers, resize grips and segmented status bar."""
import math
from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QPolygon
from PySide6.QtWidgets import QWidget, QGridLayout, QScrollArea, QStatusBar, QLabel, QSlider, QHBoxLayout, QFrame, QToolButton


class Ruler(QWidget):
    def __init__(self, workspace, vertical=False):
        super().__init__(workspace)
        self.workspace, self.vertical = workspace, vertical
        self.cursor = -100
        if vertical:
            self.setFixedWidth(20)
        else:
            self.setFixedHeight(20)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#f1f3f8"))
        p.setFont(QFont("Segoe UI",8))
        p.setPen(QColor("#7b8ba0"))
        full_width = self.workspace.width()
        step_size = 5
        while full_width//step_size > 15:
            step_size += 5
        steps = max(1,full_width//step_size)
        ticks = steps*10
        length = self.height() if self.vertical else full_width
        beginning = 4 if self.vertical else 24
        scroll = self.workspace.scroll.verticalScrollBar().value() if self.vertical else self.workspace.scroll.horizontalScrollBar().value()
        zoom = self.workspace.window.canvas.zoom
        for i in range(ticks+1):
            position = beginning+round(length/ticks*i)
            if not self.vertical:
                position -= 20
            major = i%10 == 0
            size = 20 if major else 4
            p.setPen(QColor("#7b8ba0"))
            if abs(position-self.cursor) < length/ticks/2:
                p.setPen(QColor("red"));size = 20
            if self.vertical:
                p.drawLine(20,position,20-size,position)
                if major:
                    value = round((position-4+scroll)/zoom)
                    p.save();p.translate(0,position+5);p.rotate(-90)
                    p.drawText(QRect(-35,0,35,16),Qt.AlignmentFlag.AlignRight,str(value));p.restore()
            else:
                p.drawLine(position,20,position,20-size)
                if major:
                    value = round((position-4+scroll)/zoom)
                    p.drawText(QRect(position+5,0,90,19),Qt.AlignmentFlag.AlignVCenter,str(value))
        p.end()


class ResizeGrip(QWidget):
    def __init__(self, holder, direction):
        super().__init__(holder)
        self.holder, self.direction = holder,direction
        self.setFixedSize(6,6)
        self.setCursor({"corner":Qt.CursorShape.SizeFDiagCursor,"right":Qt.CursorShape.SizeHorCursor,"bottom":Qt.CursorShape.SizeVerCursor}[direction])
        self.setStyleSheet("background:#fff;border:1px solid #555;")

    def mousePressEvent(self,event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start = event.globalPosition().toPoint()
            self.original = self.holder.canvas.doc.image.size()
            self.target = QSize(self.original)

    def mouseMoveEvent(self,event):
        if event.buttons() & Qt.MouseButton.LeftButton and hasattr(self,"start"):
            delta = event.globalPosition().toPoint()-self.start
            zoom = self.holder.canvas.zoom
            width = self.original.width()+round(delta.x()/zoom) if self.direction != "bottom" else self.original.width()
            height = self.original.height()+round(delta.y()/zoom) if self.direction != "right" else self.original.height()
            self.target = QSize(max(1,min(32767,width)),max(1,min(32767,height)))
            self.holder.preview_size = self.target
            self.holder.update()
            self.holder.window.paint_status.dimensions.setText(f"{width} x {height}px")

    def mouseReleaseEvent(self,event):
        if hasattr(self,"target"):
            self.holder.window.safe(lambda:self.holder.canvas.doc.resize(self.target.width(),self.target.height(),background=self.holder.canvas.background))
            self.holder.preview_size = None
            self.holder.canvas.sync()
            del self.start


class CanvasHolder(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window, self.canvas = window,window.canvas
        self.canvas.setParent(self)
        self.canvas.move(4,4)
        self.preview_size = None
        self.grips = {key:ResizeGrip(self,key) for key in ("right","bottom","corner")}
        self.sync()

    def sync(self):
        width,height = self.canvas.width(),self.canvas.height()
        self.setFixedSize(width+14,height+14)
        self.canvas.move(4,4)
        self.grips["right"].move(width+6,5+height//2)
        self.grips["bottom"].move(5+width//2,height+6)
        self.grips["corner"].move(width+6,height+6)
        for grip in self.grips.values():grip.raise_()
        self.update()

    def paintEvent(self,event):
        p = QPainter(self)
        p.fillRect(QRect(4,4,self.canvas.width()+4,self.canvas.height()+4),QColor("#bac4d6"))
        if self.preview_size:
            p.setPen(QPen(QColor("#333"),1,Qt.PenStyle.DotLine))
            p.drawRect(5,5,round(self.preview_size.width()*self.canvas.zoom),round(self.preview_size.height()*self.canvas.zoom))
        p.end()


class PaintWorkspace(QWidget):
    def __init__(self,window):
        super().__init__(window)
        self.window = window
        self.setStyleSheet("background:#ced7e6;")
        layout = QGridLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(0)
        self.corner = QWidget();self.corner.setFixedSize(20,20);self.corner.setStyleSheet("background:#f1f3f8;")
        self.horizontal = Ruler(self)
        self.vertical = Ruler(self,True)
        self.scroll = QScrollArea()
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.scroll.setStyleSheet("QScrollArea{background:#ced7e6;border:0;} QScrollArea>QWidget>QWidget{background:#ced7e6;}")
        self.holder = CanvasHolder(window)
        self.scroll.setWidget(self.holder)
        layout.addWidget(self.corner,0,0);layout.addWidget(self.horizontal,0,1)
        layout.addWidget(self.vertical,1,0);layout.addWidget(self.scroll,1,1)
        layout.setRowStretch(1,1);layout.setColumnStretch(1,1)
        self.scroll.horizontalScrollBar().valueChanged.connect(lambda _:self.horizontal.update())
        self.scroll.verticalScrollBar().valueChanged.connect(lambda _:self.vertical.update())
        self.set_rulers(True)

    def set_rulers(self,visible):
        for widget in (self.corner,self.horizontal,self.vertical):widget.setVisible(visible)
        self.window.canvas.rulers = False

    def sync(self):
        self.holder.sync()
        self.horizontal.update();self.vertical.update()

    def pointer(self,point):
        self.horizontal.cursor = 5+round(point.x()*self.window.canvas.zoom)-self.scroll.horizontalScrollBar().value()
        self.vertical.cursor = 5+round(point.y()*self.window.canvas.zoom)-self.scroll.verticalScrollBar().value()
        self.horizontal.update();self.vertical.update()


class PaintStatusBar(QStatusBar):
    def __init__(self,window):
        super().__init__(window)
        self.window = window
        self.setSizeGripEnabled(False)
        self.setFixedHeight(24)
        self.setStyleSheet("QStatusBar{background:#f0f0f0;border-top:1px solid #aaa;}QStatusBar::item{border:0;} QLabel{background:transparent;color:#111;}")
        contents = QWidget()
        layout = QHBoxLayout(contents);layout.setContentsMargins(4,0,5,0);layout.setSpacing(0)
        self.cursor_label = self.cell(layout,"⌖",148)
        self.selection = self.cell(layout,"▯",154)
        self.dimensions = self.cell(layout,"▦",154)
        self.file_size = self.cell(layout,"▣",154)
        layout.addStretch()
        line = QFrame();line.setFixedSize(1,20);line.setStyleSheet("background:#aaa;");layout.addWidget(line)
        self.percentage = QLabel("100%");self.percentage.setFixedWidth(62);self.percentage.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter);layout.addWidget(self.percentage)
        minus = QToolButton();minus.setText("−");minus.setFixedSize(25,20);minus.clicked.connect(lambda:window.set_zoom(window.canvas.zoom-0.1));layout.addWidget(minus)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(10,1000);self.slider.setValue(100);self.slider.setFixedWidth(125)
        self.slider.setStyleSheet("QSlider::groove:horizontal{height:6px;background:#e1e1e1;border:1px solid #bcbcbc;} QSlider::handle:horizontal{width:8px;background:#e64a10;border:1px solid #ce3800;margin:-4px 0;border-radius:3px;}")
        self.slider.valueChanged.connect(lambda value:window.set_zoom(value/100));layout.addWidget(self.slider)
        plus = QToolButton();plus.setText("+");plus.setFixedSize(25,20);plus.clicked.connect(lambda:window.set_zoom(window.canvas.zoom+0.1));layout.addWidget(plus)
        self.addWidget(contents,1)

    def cell(self,layout,icon,width):
        container = QWidget();container.setFixedWidth(width)
        row = QHBoxLayout(container);row.setContentsMargins(2,0,4,0);row.setSpacing(5)
        glyph = QLabel(icon);glyph.setFixedWidth(16);row.addWidget(glyph)
        label = QLabel();row.addWidget(label,1)
        divider = QFrame();divider.setFixedSize(1,20);divider.setStyleSheet("background:#aaa;");row.addWidget(divider)
        layout.addWidget(container)
        return label

    def showMessage(self,text,timeout=0):
        self.cursor_label.setText(text.replace(" px","px"))

    def refresh_document(self):
        doc = self.window.doc
        self.dimensions.setText(f"{doc.image.width()} x {doc.image.height()}px")
        selection = self.window.canvas.selection
        self.selection.setText(f"{selection.width()} x {selection.height()}px" if not selection.isEmpty() else "")
        path = doc.path
        self.file_size.setText(f"Size: {path.stat().st_size/1024:.2f} KB" if path and path.is_file() else "")
        self.percentage.setText(f"{round(self.window.canvas.zoom*100)}%")
        self.slider.blockSignals(True);self.slider.setValue(round(self.window.canvas.zoom*100));self.slider.blockSignals(False)
