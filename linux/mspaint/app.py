"""Qt Widgets paint editor. Image mutations are committed once per gesture."""
import math
import os
import random
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QPoint, QRect, QSettings, QTimer
from PySide6.QtGui import (QAction, QActionGroup, QColor, QFont, QImage,
                          QImageReader, QImageWriter, QPainter, QPainterPath,
                          QPen, QPolygon, QTransform, QKeySequence)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QScrollArea,
    QToolBar, QComboBox, QSpinBox, QSlider, QColorDialog, QFileDialog,
    QMessageBox, QInputDialog, QFontDialog, QLabel, QDockWidget, QVBoxLayout)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog, QPageSetupDialog
from .document import Document, blank, valid_size


class Canvas(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.zoom = 1.0
        self.tool = "Select"
        self.pen_width = 1
        self.tool_sizes = {"Pencil":1,"Eraser":5,"Brush":4,"Shape":4}
        self.foreground, self.background = QColor("black"), QColor("white")
        self.font = QFont("Calibri", 11)
        self.text_opaque = False
        self.text_editor = None
        self.text_creating = False
        self.filled = False
        self.outlined = True
        self.transparent = False
        self.grid = self.rulers = False
        self.selection = QRect()
        self.selection_path = None
        self.drawing = False
        self.preview = None
        self.points = []
        self.polygon = []
        self.curve_pending = None
        self.shape_pending = None
        self.interaction = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sync()

    @property
    def doc(self):
        return self.window.doc

    def sync(self):
        self.setFixedSize(max(1, round(self.doc.image.width() * self.zoom)),
                          max(1, round(self.doc.image.height() * self.zoom)))
        self.update()
        if self.text_editor is not None:
            self.text_editor.sync_geometry()
        if hasattr(self.window, "workspace"):
            self.window.workspace.sync()
        self.window.refresh()

    def point(self, event):
        return QPoint(int(event.position().x() / self.zoom), int(event.position().y() / self.zoom))

    def reset_transient(self):
        self.cancel_text()
        self.preview = None
        self.drawing = False
        self.selection = QRect()
        self.selection_path = None
        self.polygon = []
        self.curve_pending = None
        self.shape_pending = None
        self.interaction = None
        self.update()

    def set_tool(self, tool):
        self.finish_text()
        self.finish_shape()
        self.finish_curve()
        self.tool_sizes[self.size_kind(self.tool)] = self.pen_width
        self.reset_transient()
        self.tool = tool
        self.pen_width = self.tool_sizes.get(self.size_kind(tool),1)
        if hasattr(self.window,"ribbon"):
            self.window.ribbon.sync_tool()

    def size_kind(self,tool):
        if tool in ("Pencil","Eraser"):return tool
        if tool in ("Brush","Airbrush","Watercolor","Marker","Crayon","Calligraphy"):return "Brush"
        return "Shape"

    def paintEvent(self, event):
        p = QPainter(self)
        p.scale(self.zoom, self.zoom)
        p.drawImage(0, 0, self.preview if self.preview is not None else self.doc.image)
        if self.grid and self.zoom >= 4:
            p.setPen(QPen(QColor(130, 130, 130, 100), 1 / self.zoom))
            visible = event.rect()
            for x in range(int(visible.left() / self.zoom), int(visible.right() / self.zoom) + 1):
                p.drawLine(x, int(visible.top() / self.zoom), x, int(visible.bottom() / self.zoom) + 1)
            for y in range(int(visible.top() / self.zoom), int(visible.bottom() / self.zoom) + 1):
                p.drawLine(int(visible.left() / self.zoom), y, int(visible.right() / self.zoom) + 1, y)
        if not self.selection.isEmpty():
            p.setPen(QPen(QColor("#0078d4"), 1 / self.zoom, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            if self.selection_path is not None:
                p.drawPath(self.selection_path)
            else:
                p.drawRect(self.selection)
            p.setPen(QPen(QColor("#444"),1/self.zoom))
            p.setBrush(QColor("white"))
            for point in self.selection_handles().values():
                size = 6/self.zoom
                from PySide6.QtCore import QRectF
                p.drawRect(QRectF(point.x()-size/2,point.y()-size/2,size,size))
            if self.shape_pending and "controls" in self.shape_pending:
                for point in self.shape_pending["controls"]:
                    p.drawRect(QRectF(point.x()-3/self.zoom,point.y()-3/self.zoom,6/self.zoom,6/self.zoom))
        if self.polygon:
            p.setPen(QPen(self.foreground, self.pen_width))
            p.drawPolyline(QPolygon(self.polygon))
            p.setPen(QPen(QColor("#444"),1/self.zoom));p.setBrush(QColor("white"))
            for point in self.polygon:p.drawRect(QRect(point-QPoint(3,3),point+QPoint(3,3)))
        if self.rulers:
            p.setPen(QPen(QColor("#777777"), 1 / self.zoom))
            for x in range(0, self.doc.image.width(), 50):
                p.drawLine(x, 0, x, 10)
                p.drawText(x + 2, 20, str(x))
            for y in range(50, self.doc.image.height(), 50):
                p.drawLine(0, y, 10, y)
                p.drawText(12, y + 5, str(y))
        if self.text_editor is not None and self.text_editor.isHidden():
            editor=self.text_editor
            if self.text_opaque:p.fillRect(editor.image_rect,self.background)
            p.setPen(self.foreground);p.setFont(self.font)
            p.drawText(editor.image_rect,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop|Qt.TextFlag.TextWordWrap,editor.toPlainText())
        p.end()

    @property
    def pending_dirty(self):
        return ((self.text_editor is not None and bool(self.text_editor.toPlainText())) or
                self.shape_pending is not None or self.curve_pending is not None or len(self.polygon)>1)

    def selection_handles(self):
        r = self.selection
        if r.isEmpty():return {}
        return {"tl":r.topLeft(),"top":QPoint(r.center().x(),r.top()),"tr":r.topRight(),
                "left":QPoint(r.left(),r.center().y()),"right":QPoint(r.right(),r.center().y()),
                "bl":r.bottomLeft(),"bottom":QPoint(r.center().x(),r.bottom()),"br":r.bottomRight()}

    def handle_at(self,point):
        for name,center in self.selection_handles().items():
            if abs(point.x()-center.x())<=5/self.zoom and abs(point.y()-center.y())<=5/self.zoom:return name
        return None

    def resized_rect(self,original,point,handle):
        r = QRect(original)
        if handle in ("tl","left","bl"):r.setLeft(min(point.x(),r.right()-1))
        if handle in ("tr","right","br"):r.setRight(max(point.x(),r.left()+1))
        if handle in ("tl","top","tr"):r.setTop(min(point.y(),r.bottom()-1))
        if handle in ("bl","bottom","br"):r.setBottom(max(point.y(),r.top()+1))
        return r

    def render_shape(self):
        shape = self.shape_pending
        if shape is None:return
        self.preview = shape["base"].copy()
        self.color = self.foreground
        self.draw_shape(self.preview,shape["start"],shape["end"])
        points=[shape["start"],shape["end"]]+shape.get("controls",[])
        self.selection = QPolygon(points).boundingRect()
        self.update()

    def snapshot(self):
        image=(self.preview if self.preview is not None else self.doc.image).copy()
        p=QPainter(image)
        if self.polygon:
            p.setPen(QPen(self.foreground,self.pen_width) if self.outlined else Qt.PenStyle.NoPen)
            p.setBrush(self.background if self.filled else Qt.BrushStyle.NoBrush)
            p.drawPolygon(QPolygon(self.polygon))
        if self.text_editor is not None:
            rect=self.text_editor.image_rect
            if self.text_opaque:p.fillRect(rect,self.background)
            p.setClipRect(rect);p.setPen(self.foreground);p.setFont(self.font)
            p.drawText(rect,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop|Qt.TextFlag.TextWordWrap,self.text_editor.toPlainText())
        p.end()
        return image

    def finish_shape(self):
        if self.shape_pending is not None:
            if self.preview is not None:self.doc.commit(self.preview)
            self.shape_pending = None
            self.preview = None
            self.selection = QRect()
            self.selection_path = None
            self.sync()

    def mousePressEvent(self, event):
        if event.button() not in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            return
        point = self.point(event)
        if not self.doc.image.rect().contains(point):
            return
        self.setFocus()
        if self.text_editor is not None:
            editor=self.text_editor
            if self.tool=="Text" and editor.image_rect.contains(point):
                editor.setTextCursor(editor.cursorForPosition(event.position().toPoint()-editor.pos()))
                self.setFocus() if editor.isHidden() else editor.setFocus()
                return
            self.finish_text()
        if self.tool == "Curve" and self.curve_pending is not None:
            self.curve_pending[2].append(point)
            self.preview = self.curve_pending[3].copy()
            self.draw_shape(self.preview, self.curve_pending[0], self.curve_pending[1])
            if len(self.curve_pending[2]) >= 2:
                start,end,controls,base=self.curve_pending
                self.shape_pending={"tool":"Curve","start":start,"end":end,"controls":controls,"base":base}
                self.curve_pending=None;self.render_shape()
            self.update()
            return
        self.start = self.last = point
        self.color = self.background if event.button() == Qt.MouseButton.RightButton else self.foreground
        self.points = [point]
        if self.shape_pending is not None:
            for index,node in enumerate(self.shape_pending.get("controls",[])):
                if (node-point).manhattanLength()<=6/self.zoom:
                    self.drawing=True;self.interaction="curve-node";self.node_index=index
                    return
            handle = self.handle_at(point)
            if handle or self.selection.contains(point):
                self.drawing = True
                self.interaction = "shape"
                self.resize_handle = handle
                self.old_selection = QRect(self.selection)
                self.original_shape_points=[QPoint(self.shape_pending["start"]),QPoint(self.shape_pending["end"])]+[QPoint(p) for p in self.shape_pending.get("controls",[])]
                self.shape_left = self.shape_pending["start"].x()<=self.shape_pending["end"].x()
                self.shape_top = self.shape_pending["start"].y()<=self.shape_pending["end"].y()
                return
            self.finish_shape()
        if self.tool == "Fill":
            self.window.safe(lambda: self.doc.fill(point, self.color))
            self.sync()
            return
        if self.tool == "Color picker":
            if event.button()==Qt.MouseButton.RightButton:self.background = self.doc.image.pixelColor(point)
            else:self.foreground = self.doc.image.pixelColor(point)
            self.window.update_colors()
            return
        if self.tool == "Zoom":
            self.window.set_zoom(self.zoom * (0.5 if event.button() == Qt.MouseButton.RightButton else 2))
            return
        if self.tool == "Text":
            self.text_creating = True
            self.selection = QRect(point,point)
            self.selection_path = None
            self.window.ribbon.tabs["Text"].show()
            self.window.ribbon.select_tab("Text")
            return
        if self.tool == "Polygon":
            if event.button() == Qt.MouseButton.RightButton:
                self.finish_polygon()
            else:
                for index,node in enumerate(self.polygon):
                    if (node-point).manhattanLength()<=6/self.zoom:
                        self.drawing=True;self.interaction="polygon-node";self.node_index=index
                        return
                self.polygon.append(point)
                self.update()
            return
        self.drawing = True
        self.original = self.doc.image.copy()
        self.preview = self.original.copy()
        handle = self.handle_at(point)
        if self.tool in ("Select", "Free select") and (handle or self.selection.contains(point)):
            self.moving = True
            self.resize_handle = handle
            self.old_selection = QRect(self.selection)
            self.old_selection_path = QPainterPath(self.selection_path) if self.selection_path is not None else None
            self.fragment = self.selected_image()
            p = QPainter(self.original)
            if self.selection_path is not None:
                p.setClipPath(self.selection_path)
            p.fillRect(self.selection, self.background)
            p.end()
        else:
            self.moving = False
            self.resize_handle = None
            self.selection = QRect()
            self.selection_path = None
            if self.tool in ("Pencil", "Brush", "Eraser", "Airbrush", "Calligraphy", "Marker", "Watercolor", "Crayon"):
                self.stroke(point, point)
        self.update()

    def stroke(self, a, b):
        p = QPainter(self.preview)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, self.tool != "Pencil")
        color = QColor(self.background if self.tool == "Eraser" else self.color)
        width = self.pen_width
        if self.tool in ("Marker", "Watercolor"):
            color.setAlpha(200 if self.tool=="Marker" else 100)
        p.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if self.tool in ("Airbrush", "Crayon"):
            p.setPen(QPen(color, 1))
            for _ in range(width*10 if self.tool=="Crayon" else 20):
                if self.tool == "Crayon":
                    textured = QColor(color)
                    h, s, v, a = textured.getHsv()
                    textured.setHsv(h, random.randrange(max(1, s + 1)), v, a)
                    p.setPen(textured)
                angle = random.random() * math.tau
                radius = math.sqrt(random.random()) * width
                p.drawPoint(round(b.x() + math.cos(angle) * radius), round(b.y() + math.sin(angle) * radius))
        elif self.tool == "Watercolor":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawEllipse(b, width / 2, width / 2)
        elif self.tool == "Eraser":
            p.setPen(QPen(color, width*2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap))
            p.drawLine(a, b)
        elif self.tool == "Calligraphy":
            p.setPen(QPen(color, max(1, width / 3)))
            for offset in range(-width // 2, width // 2 + 1):
                p.drawLine(a + QPoint(offset, -offset), b + QPoint(offset, -offset))
        elif a == b:
            p.drawPoint(a)
        else:
            p.drawLine(a, b)
        p.end()

    def mouseMoveEvent(self, event):
        point = self.point(event)
        self.window.statusBar().showMessage(f"{point.x()}, {point.y()} px")
        if hasattr(self.window,"workspace"):
            self.window.workspace.pointer(point)
        if self.text_creating:
            self.selection = QRect(self.start,point).normalized().intersected(self.doc.image.rect())
            self.update()
            return
        if not self.drawing:
            return
        if self.interaction == "polygon-node":
            self.polygon[self.node_index]=point;self.update();return
        if self.interaction == "curve-node":
            self.shape_pending["controls"][self.node_index]=point;self.render_shape();return
        if self.interaction == "shape":
            r = self.resized_rect(self.old_selection,point,self.resize_handle) if self.resize_handle else self.old_selection.translated(point-self.start)
            if "controls" in self.shape_pending:
                old=self.old_selection
                points=[QPoint(round(r.x()+(p.x()-old.x())*(r.width()-1)/max(1,old.width()-1)),round(r.y()+(p.y()-old.y())*(r.height()-1)/max(1,old.height()-1))) for p in self.original_shape_points]
                self.shape_pending["start"],self.shape_pending["end"]=points[:2]
                self.shape_pending["controls"]=points[2:]
            else:
                self.shape_pending["start"] = QPoint(r.left() if self.shape_left else r.right(),r.top() if self.shape_top else r.bottom())
                self.shape_pending["end"] = QPoint(r.right() if self.shape_left else r.left(),r.bottom() if self.shape_top else r.top())
            self.render_shape()
            self.last = point
            return
        if self.tool in ("Pencil", "Brush", "Eraser", "Airbrush", "Calligraphy", "Marker", "Watercolor", "Crayon"):
            self.stroke(self.last, point)
        elif self.tool in ("Select", "Free select"):
            if self.moving:
                delta = point - self.start
                self.selection = self.resized_rect(self.old_selection,point,self.resize_handle) if self.resize_handle else self.old_selection.translated(delta)
                if self.old_selection_path is not None:
                    sx=self.selection.width()/self.old_selection.width();sy=self.selection.height()/self.old_selection.height()
                    transform=QTransform().translate(self.selection.x(),self.selection.y()).scale(sx,sy).translate(-self.old_selection.x(),-self.old_selection.y())
                    self.selection_path = transform.map(self.old_selection_path)
                self.preview = self.original.copy()
                p = QPainter(self.preview)
                p.drawImage(self.selection,self.fragment)
                p.end()
            elif self.tool == "Free select":
                self.points.append(point)
                path = QPainterPath()
                path.addPolygon(QPolygon(self.points))
                path.closeSubpath()
                self.selection_path = path
                self.selection = path.boundingRect().toAlignedRect().intersected(self.doc.image.rect())
            else:
                self.selection = QRect(self.start, point).normalized().intersected(self.doc.image.rect())
        else:
            self.preview = self.original.copy()
            self.draw_shape(self.preview, self.start, point, event.modifiers())
        self.last = point
        self.update()

    def draw_shape(self, image, start, end, modifiers=Qt.KeyboardModifier.NoModifier):
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            side = max(abs(end.x() - start.x()), abs(end.y() - start.y()))
            end = start + QPoint(side if end.x() >= start.x() else -side,
                                  side if end.y() >= start.y() else -side)
        rect = QRect(start, end).normalized()
        p = QPainter(image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(self.color, self.pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if not self.outlined:
            p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.background if self.filled else Qt.BrushStyle.NoBrush)
        if self.tool == "Line":
            p.drawLine(start, end)
        elif self.tool == "Ellipse":
            p.drawEllipse(rect)
        elif self.tool == "Rounded rectangle":
            p.drawRoundedRect(rect, 15, 15)
        elif self.tool in ("Triangle", "Right triangle"):
            top = QPoint(rect.center().x(), rect.top()) if self.tool == "Triangle" else rect.topLeft()
            p.drawPolygon(QPolygon([top, rect.bottomRight(), rect.bottomLeft()]))
        elif self.tool == "Diamond":
            p.drawPolygon(QPolygon([QPoint(rect.center().x(), rect.top()), QPoint(rect.right(), rect.center().y()),
                                    QPoint(rect.center().x(), rect.bottom()), QPoint(rect.left(), rect.center().y())]))
        elif self.tool in ("Star", "Four-point star", "Six-point star", "Pentagon", "Hexagon"):
            count = {"Star": 10, "Four-point star": 8, "Six-point star": 12, "Pentagon": 5, "Hexagon": 6}[self.tool]
            points = []
            for i in range(count):
                factor = 0.35 if "star" in self.tool.lower() and i % 2 else 1
                angle = i * math.tau / count - math.pi / 2
                points.append(QPoint(round(rect.center().x() + rect.width() / 2 * factor * math.cos(angle)),
                                     round(rect.center().y() + rect.height() / 2 * factor * math.sin(angle))))
            p.drawPolygon(QPolygon(points))
        elif self.tool in ("Arrow", "Left arrow", "Up arrow", "Down arrow"):
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
            coords = [(0, 1/3), (2/3, 1/3), (2/3, 0), (1, 1/2), (2/3, 1), (2/3, 2/3), (0, 2/3)]
            if self.tool == "Left arrow":
                coords = [(1-a, b) for a, b in coords]
            elif self.tool == "Up arrow":
                coords = [(b, 1-a) for a, b in coords]
            elif self.tool == "Down arrow":
                coords = [(b, a) for a, b in coords]
            p.drawPolygon(QPolygon([QPoint(round(x+a*w), round(y+b*h)) for a, b in coords]))
        elif self.tool == "Curve":
            path = QPainterPath(start)
            controls = self.curve_pending[2] if self.curve_pending else self.shape_pending.get("controls",[]) if self.shape_pending else []
            first = controls[0] if controls else start
            second = controls[1] if len(controls) > 1 else end
            path.cubicTo(first.x(), first.y(), second.x(), second.y(), end.x(), end.y())
            p.drawPath(path)
        else:
            p.drawRect(rect)
        p.end()

    def mouseReleaseEvent(self, event):
        if self.text_creating:
            self.text_creating = False
            rect = QRect(self.selection)
            if rect.width()<20 or rect.height()<20:
                rect = QRect(self.start.x(),self.start.y(),min(250,self.doc.image.width()-self.start.x()),min(90,self.doc.image.height()-self.start.y()))
            from .textedit import PaintTextEdit
            self.text_editor = PaintTextEdit(self,rect)
            self.selection = QRect(self.text_editor.image_rect)
            self.update()
            return
        if not self.drawing:
            return
        self.mouseMoveEvent(event)
        self.drawing = False
        if self.interaction in ("polygon-node","curve-node"):
            self.interaction=None;self.sync();return
        if self.interaction == "shape":
            self.interaction = None
            self.sync()
            return
        if self.tool == "Curve":
            self.curve_pending = [self.start, self.last, [], self.original]
            self.window.statusBar().showMessage("Click two curve control points; Enter accepts; Escape cancels.")
            return
        shape_tools = {"Line","Rectangle","Rounded rectangle","Ellipse","Triangle","Right triangle","Diamond","Star","Four-point star","Six-point star","Pentagon","Hexagon","Arrow","Left arrow","Up arrow","Down arrow"}
        if self.tool in shape_tools:
            self.shape_pending = {"tool":self.tool,"start":QPoint(self.start),"end":QPoint(self.last),"base":self.original}
            self.selection = QRect(self.start,self.last).normalized()
            self.sync()
            return
        if self.tool not in ("Select", "Free select") or self.moving:
            self.doc.commit(self.preview)
        self.preview = None
        self.sync()

    def mouseDoubleClickEvent(self, event):
        if self.tool == "Polygon":
            self.finish_polygon()

    def finish_polygon(self):
        if len(self.polygon) >= 3:
            image = self.doc.image.copy()
            p = QPainter(image)
            p.setPen(QPen(self.foreground, self.pen_width) if self.outlined else Qt.PenStyle.NoPen)
            p.setBrush(self.background if self.filled else Qt.BrushStyle.NoBrush)
            p.drawPolygon(QPolygon(self.polygon))
            p.end()
            self.doc.commit(image)
        self.polygon = []
        self.sync()

    def finish_curve(self):
        if self.curve_pending is not None and self.preview is not None:
            self.doc.commit(self.preview)
            self.curve_pending = None
            self.preview = None
            self.sync()

    def finish_text(self):
        editor = self.text_editor
        if editor is None:return
        self.text_editor = None
        text = editor.toPlainText()
        if text:
            image = self.doc.image.copy()
            p = QPainter(image)
            rect = editor.image_rect
            if self.text_opaque:p.fillRect(rect,self.background)
            p.setClipRect(rect)
            p.setPen(self.foreground);p.setFont(self.font)
            p.drawText(rect,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop|Qt.TextFlag.TextWordWrap,text)
            p.end();self.doc.commit(image)
        editor.destroy_grips();editor.hide();editor.deleteLater()
        self.selection = QRect()
        self.sync()

    def cancel_text(self):
        editor = self.text_editor
        self.text_editor = None
        self.text_creating = False
        if editor is not None:
            editor.destroy_grips();editor.hide();editor.deleteLater()
            self.selection=QRect();self.update()

    def update_font(self,font=None):
        if font is not None:self.font = font
        if self.text_editor is not None:self.text_editor.update_style()

    def selected_image(self):
        rect = self.selection if not self.selection.isEmpty() else self.doc.image.rect()
        source = self.preview if self.preview is not None else self.doc.image
        image = source.copy(rect)
        if self.selection_path is not None:
            mask = QImage(image.size(), QImage.Format.Format_ARGB32)
            mask.fill(Qt.GlobalColor.transparent)
            p = QPainter(mask)
            p.translate(-rect.topLeft())
            p.setClipPath(self.selection_path)
            p.drawImage(rect.topLeft(), image)
            p.end()
            image = mask
        if self.transparent:
            # Qt's color mask runs in native code, avoiding a Python pixel loop.
            mask = image.createMaskFromColor(self.background.rgba(), Qt.MaskMode.MaskOutColor)
            image.setAlphaChannel(mask)
        return image

    def delete_selection(self):
        if self.selection.isEmpty():
            return
        image = self.doc.image.copy()
        p = QPainter(image)
        if self.selection_path is not None:
            p.setClipPath(self.selection_path)
        p.fillRect(self.selection, self.background)
        p.end()
        self.doc.commit(image)
        self.reset_transient()
        self.sync()

    def keyPressEvent(self, event):
        if self.text_editor is not None and self.text_editor.isHidden():
            QApplication.sendEvent(self.text_editor,event);self.update();return
        if event.key() == Qt.Key.Key_Escape:
            self.reset_transient()
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selection()
        elif event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.finish_shape()
            self.finish_curve()
            self.finish_polygon()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self,event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.window.set_zoom(self.zoom+(0.1 if event.angleDelta().y()>0 else -0.1));event.accept()
        else:super().wheelEvent(event)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        from .theme import install_fonts
        install_fonts()
        self.doc = Document()
        self.settings = QSettings("mspaint-rewritten", "linux")
        self.thumbnail = None
        self.thumbnail_preview = None
        self.fullscreen_preview = None
        self.printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self.size_label = QLabel()
        self.statusBar().addPermanentWidget(self.size_label)
        self.canvas = Canvas(self)
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.canvas)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setCentralWidget(self.scroll)
        self.setAcceptDrops(True)
        self.build_ui()
        self.mount_paint_ui()
        self.resize(1532, 848)
        geometry = self.settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        self.refresh()

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and not self.isMaximized():
            point=self.mapFromGlobal(event.globalPosition().toPoint())
            edges=Qt.Edge(0)
            if 0<=point.x()<3:edges|=Qt.Edge.LeftEdge
            elif self.width()-3<=point.x()<self.width():edges|=Qt.Edge.RightEdge
            if 0<=point.y()<3:edges|=Qt.Edge.TopEdge
            elif self.height()-3<=point.y()<self.height():edges|=Qt.Edge.BottomEdge
            if edges and self.windowHandle() and self.windowHandle().startSystemResize(edges):event.accept();return
        super().mousePressEvent(event)

    def action(self, menu, text, callback, shortcut=None, check=False):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.setCheckable(check)
        action.triggered.connect(lambda checked=False: callback(checked) if check else callback())
        menu.addAction(action)
        self.addAction(action)
        return action

    def build_ui(self):
        file = self.menuBar().addMenu("&File")
        self.action(file, "&New", self.new, "Ctrl+N")
        self.action(file, "&Open…", self.open, "Ctrl+O")
        self.recents = file.addMenu("Recent files")
        self.refresh_recents()
        self.action(file, "&Save", self.save, "Ctrl+S")
        self.action(file, "Save &as…", lambda: self.save(True), "Ctrl+Shift+S")
        file.addSeparator()
        self.action(file, "Print…", self.print_image, "Ctrl+P")
        self.action(file, "Print preview…", self.print_preview)
        self.action(file, "Page setup…", self.page_setup)
        self.action(file, "Export PDF…", self.export_pdf)
        self.action(file, "Set desktop wallpaper…", self.wallpaper)
        self.action(file, "Exit", self.close, "Ctrl+Q")
        edit = self.menuBar().addMenu("&Edit")
        self.undo_action = self.action(edit, "Undo", lambda: self.history(False), "Ctrl+Z")
        self.redo_action = self.action(edit, "Redo", lambda: self.history(True), "Ctrl+Shift+Z")
        self.action(edit, "Copy", self.copy, "Ctrl+C")
        self.action(edit, "Cut", self.cut, "Ctrl+X")
        self.action(edit, "Paste", self.paste, "Ctrl+V")
        self.action(edit, "Paste from file…", self.paste_file)
        self.action(edit, "Select all", self.select_all, "Ctrl+A")
        self.action(edit, "Delete selection", self.canvas.delete_selection, "Delete")
        image = self.menuBar().addMenu("&Image")
        self.action(image, "Crop to selection", self.crop)
        self.action(image, "Resize canvas…", lambda: self.resize_image(False))
        self.action(image, "Scale image…", lambda: self.resize_image(True))
        self.action(image, "Scale selection…", self.scale_selection)
        self.action(image, "Rotate right 90°", lambda: self.transform(QTransform().rotate(90)))
        self.action(image, "Rotate left 90°", lambda: self.transform(QTransform().rotate(-90)))
        self.action(image, "Rotate 180°", lambda: self.transform(QTransform().rotate(180)))
        self.action(image, "Flip horizontal", lambda: self.flip(True))
        self.action(image, "Flip vertical", lambda: self.flip(False))
        self.action(image, "Skew…", self.skew)
        self.action(image, "Invert colors", self.invert)
        self.action(image, "Clear canvas", self.clear)
        self.action(image, "Properties…", self.properties)
        view = self.menuBar().addMenu("&View")
        self.action(view, "Zoom in", lambda: self.set_zoom(self.canvas.zoom * 1.25), "Ctrl++")
        self.action(view, "Zoom out", lambda: self.set_zoom(self.canvas.zoom / 1.25), "Ctrl+-")
        self.action(view, "Actual size", lambda: self.set_zoom(1), "Ctrl+0")
        self.action(view, "Fit in window", self.fit)
        self.action(view, "Pixel grid (zoom ≥400%)", lambda v: self.toggle_canvas("grid", v), check=True)
        self.action(view, "Rulers", lambda v: self.toggle_canvas("rulers", v), check=True)
        self.action(view, "Thumbnail", self.show_thumbnail, check=True)
        self.action(view, "Fullscreen", self.fullscreen, "F11")
        help_menu = self.menuBar().addMenu("&Help")
        self.action(help_menu, "About", lambda: QMessageBox.about(self, "MSPaint Rewritten Linux",
            "Native Qt edition 0.1.0 (preview)\nBased on Codrut's MIT-licensed mspaint-rewritten.\n"
            "Polygon: Enter or right-click to finish. Shift constrains shapes.\n"
            "Uses Qt/PySide6 under LGPL-3.0; notices and sources accompany the release.\n"
            "See docs/PORTING.md for feature differences and test coverage."))
        tools = QToolBar("Tools", self)
        tools.setMovable(False)
        self.addToolBar(tools)
        self.tool_combo = QComboBox()
        self.tool_combo.addItems(["Pencil", "Brush", "Eraser", "Fill", "Color picker", "Text", "Zoom",
            "Select", "Free select", "Airbrush", "Calligraphy", "Marker", "Watercolor", "Crayon", "Line", "Curve", "Rectangle",
            "Rounded rectangle", "Ellipse", "Triangle", "Right triangle", "Diamond", "Star", "Four-point star", "Six-point star",
            "Pentagon", "Hexagon", "Arrow", "Left arrow", "Up arrow", "Down arrow", "Polygon"])
        self.tool_combo.currentTextChanged.connect(self.canvas.set_tool)
        self.tool_combo.setCurrentText(self.canvas.tool)
        tools.addWidget(self.tool_combo)
        tools.addWidget(QLabel("  Size "))
        width = QSpinBox()
        width.setRange(1, 100)
        width.setValue(3)
        width.valueChanged.connect(lambda value: setattr(self.canvas, "pen_width", value))
        tools.addWidget(width)
        self.primary = self.action(tools, "Color 1", lambda: self.choose_color(False))
        self.secondary = self.action(tools, "Color 2", lambda: self.choose_color(True))
        self.action(tools, "Swap", self.swap_colors, "X")
        self.action(tools, "Fill shapes", lambda value: setattr(self.canvas, "filled", value), check=True)
        outline = self.action(tools, "Shape outline", lambda value: setattr(self.canvas, "outlined", value), check=True)
        outline.setChecked(True)
        self.action(tools, "Transparent selection", lambda value: setattr(self.canvas, "transparent", value), check=True)
        self.action(tools, "Font…", self.choose_font)
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 1000)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setMaximumWidth(180)
        self.zoom_slider.valueChanged.connect(lambda value: self.set_zoom(value / 100))
        tools.addWidget(QLabel("  Zoom "))
        tools.addWidget(self.zoom_slider)
        self.addToolBarBreak()
        palette = QToolBar("Palette", self)
        self.addToolBar(palette)
        for color in ["#000000", "#808080", "#800000", "#ff0000", "#ff8000", "#ffff00", "#008000", "#00ff00",
                      "#008080", "#00ffff", "#000080", "#0000ff", "#800080", "#ff00ff", "#ffffff", "#c0c0c0"]:
            action = self.action(palette, "■", lambda c=color: self.palette_color(c))
            from PySide6.QtGui import QIcon, QPixmap
            pixmap = QPixmap(22, 22)
            pixmap.fill(QColor(color))
            action.setIcon(QIcon(pixmap))
            action.setToolTip(color)
        self.update_colors()

    def mount_paint_ui(self):
        from .ribbon import PaintRibbon,TitleBar,ASSETS
        from .workspace import PaintWorkspace,PaintStatusBar
        from PySide6.QtGui import QIcon
        self.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint)
        self.setWindowIcon(QIcon(str(ASSETS/"paint.ico")))
        self.setFont(QFont("Segoe UI",9))
        self.menuBar().hide()
        for toolbar in self.findChildren(QToolBar):toolbar.hide()
        self.scroll.takeWidget()
        old = self.takeCentralWidget()
        root = QWidget(self)
        layout = QVBoxLayout(root);layout.setContentsMargins(1,0,1,0);layout.setSpacing(0)
        self.title_bar = TitleBar(self)
        self.ribbon = PaintRibbon(self)
        self.workspace = PaintWorkspace(self)
        self.scroll = self.workspace.scroll
        layout.addWidget(self.title_bar);layout.addWidget(self.ribbon);layout.addWidget(self.workspace,1)
        self.setCentralWidget(root)
        if old:old.deleteLater()
        self.paint_status = PaintStatusBar(self)
        self.setStatusBar(self.paint_status)
        self.size_label = self.paint_status.dimensions
        self.ribbon.sync_tool()
        self.refresh()

    def safe(self, callback):
        try:
            callback()
            return True
        except (OSError, ValueError, MemoryError) as error:
            QMessageBox.warning(self, "Unable to complete operation", str(error))
            return False

    def refresh(self):
        name = self.doc.path.name if self.doc.path else "Untitled"
        self.setWindowTitle(f"{name} - Paint")
        if hasattr(self,"title_bar"):
            self.title_bar.label.setText(self.windowTitle())
        if hasattr(self,"paint_status"):
            self.paint_status.refresh_document()
        else:
            self.size_label.setText(f"{self.doc.image.width()} × {self.doc.image.height()} px")
        if hasattr(self, "undo_action"):
            self.undo_action.setEnabled(self.doc.position > 0)
            self.redo_action.setEnabled(self.doc.position + 1 < len(self.doc.history))
        if self.thumbnail_preview is not None:self.thumbnail_preview.refresh()

    def may_discard(self):
        if not self.doc.dirty and not self.canvas.pending_dirty:
            return True
        result = QMessageBox.question(self, "Unsaved changes", "Save changes before continuing?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if result == QMessageBox.StandardButton.Save:
            return self.save()
        return result == QMessageBox.StandardButton.Discard

    def new(self):
        if self.may_discard():
            self.doc.new()
            self.canvas.reset_transient()
            self.canvas.sync()

    def open(self, path=None):
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, "Open image", "", "Images (*.png *.bmp *.jpg *.jpeg *.gif *.webp);;All files (*)")
        if path and self.may_discard() and self.safe(lambda: self.doc.load(path)):
            self.canvas.reset_transient()
            self.canvas.sync()
            self.remember(path)

    def save(self, save_as=False):
        self.canvas.finish_text()
        self.canvas.finish_shape()
        self.canvas.finish_curve()
        self.canvas.finish_polygon()
        path = self.doc.path
        if save_as or path is None:
            formats = [bytes(f).decode() for f in QImageWriter.supportedImageFormats()] + ["gif"]
            filters = [f"{f.upper()} (*.{f})" for f in ("png", "bmp", "jpeg", "webp", "gif") if f in formats]
            selected, chosen = QFileDialog.getSaveFileName(self, "Save image", str(path or "Untitled.png"), ";;".join(filters))
            if not selected:
                return False
            path = Path(selected)
            if not path.suffix:
                suffix = chosen.split("*.")[-1].rstrip(")")
                path = path.with_suffix("." + suffix)
        if not self.safe(lambda: self.doc.save(path)):
            return False
        self.remember(str(path))
        self.refresh()
        return True

    def remember(self, path):
        path = str(Path(path).resolve())
        recents = self.settings.value("recents", [], type=list)
        self.settings.setValue("recents", [path] + [p for p in recents if p != path][:19])
        self.refresh_recents()

    def refresh_recents(self):
        self.recents.clear()
        for path in self.settings.value("recents", [], type=list):
            self.action(self.recents, path, lambda p=path: self.open(p))

    def history(self, redo):
        if self.canvas.text_editor is not None:
            self.canvas.text_editor.redo() if redo else self.canvas.text_editor.undo()
            return
        if self.canvas.pending_dirty and not redo:
            self.canvas.reset_transient();self.canvas.sync();return
        self.canvas.reset_transient()
        self.doc.redo() if redo else self.doc.undo()
        self.canvas.sync()

    def copy(self):
        if self.canvas.text_editor is not None:
            self.canvas.text_editor.copy();return
        QApplication.clipboard().setImage(self.canvas.selected_image())

    def cut(self):
        if self.canvas.text_editor is not None:
            self.canvas.text_editor.cut();return
        if self.canvas.selection.isEmpty():
            self.select_all()
        self.copy()
        self.canvas.delete_selection()

    def paste(self):
        if self.canvas.text_editor is not None:
            self.canvas.text_editor.paste();return
        image = QApplication.clipboard().image()
        point = self.canvas.selection.topLeft() if not self.canvas.selection.isEmpty() else QPoint()
        if self.safe(lambda: self.doc.paste(image, point)):
            self.canvas.reset_transient()
            self.canvas.sync()

    def paste_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Paste image")
        if path:
            def operation():
                other = Document()
                other.load(path)
                self.doc.paste(other.image)
            if self.safe(operation):
                self.canvas.sync()

    def select_all(self):
        if self.canvas.text_editor is not None:
            self.canvas.text_editor.selectAll();return
        self.tool_combo.setCurrentText("Select")
        self.canvas.selection = self.doc.image.rect()
        self.canvas.update()

    def crop(self):
        if not self.canvas.selection.isEmpty():
            self.doc.commit(self.canvas.selected_image())
            self.canvas.reset_transient()
            self.canvas.sync()

    def resize_image(self, scale):
        width, ok = QInputDialog.getInt(self, "Image size", "Width (px)", self.doc.image.width(), 1, 32767)
        if not ok:
            return
        height, ok = QInputDialog.getInt(self, "Image size", "Height (px)", self.doc.image.height(), 1, 32767)
        if ok and self.safe(lambda: self.doc.resize(width, height, scale, self.canvas.background)):
            self.canvas.reset_transient()
            self.canvas.sync()

    def scale_selection(self):
        if self.canvas.selection.isEmpty():
            return
        width, ok = QInputDialog.getInt(self, "Scale selection", "Width (px)", self.canvas.selection.width(), 1, 32767)
        if not ok:
            return
        height, ok = QInputDialog.getInt(self, "Scale selection", "Height (px)", self.canvas.selection.height(), 1, 32767)
        if ok:
            def operation():
                valid_size(width, height)
                self.apply_image(self.canvas.selected_image().scaled(width, height))
            self.safe(operation)

    def apply_image(self, image):
        valid_size(image.width(), image.height())
        if not self.canvas.selection.isEmpty():
            rect = self.canvas.selection
            width = max(self.doc.image.width(), rect.x() + image.width())
            height = max(self.doc.image.height(), rect.y() + image.height())
            result = blank(width, height, self.canvas.background)
            p = QPainter(result)
            p.drawImage(0, 0, self.doc.image)
            if self.canvas.selection_path is not None:
                p.setClipPath(self.canvas.selection_path)
            p.fillRect(rect, self.canvas.background)
            p.setClipping(False)
            p.drawImage(rect.topLeft(), image)
            p.end()
            self.doc.commit(result)
        else:
            self.doc.commit(image)
        self.canvas.reset_transient()
        self.canvas.sync()

    def transform(self, transform):
        def operation():
            image = self.canvas.selected_image()
            bounds = transform.mapRect(image.rect()).normalized()
            valid_size(bounds.width(), bounds.height())
            self.apply_image(image.transformed(transform))
        self.safe(operation)

    def flip(self, horizontal):
        orientation = Qt.Orientation.Horizontal if horizontal else Qt.Orientation.Vertical
        self.apply_image(self.canvas.selected_image().flipped(orientation))

    def skew(self):
        x, ok = QInputDialog.getInt(self, "Skew", "Horizontal angle (degrees)", 0, -80, 80)
        if not ok:
            return
        y, ok = QInputDialog.getInt(self, "Skew", "Vertical angle (degrees)", 0, -80, 80)
        if ok:
            self.transform(QTransform().shear(math.tan(math.radians(x)), math.tan(math.radians(y))))

    def invert(self):
        image = self.canvas.selected_image()
        image.invertPixels()
        self.apply_image(image)

    def clear(self):
        self.doc.commit(blank(self.doc.image.width(), self.doc.image.height(), self.canvas.background))
        self.canvas.reset_transient()
        self.canvas.sync()

    def properties(self):
        self.canvas.finish_text();self.canvas.finish_shape();self.canvas.finish_curve();self.canvas.finish_polygon()
        from .dialogs import PropertiesDialog
        PropertiesDialog(self).exec()

    def set_zoom(self, zoom):
        self.canvas.zoom = max(0.1, min(10, zoom))
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(round(self.canvas.zoom * 100))
        self.zoom_slider.blockSignals(False)
        self.canvas.sync()

    def fit(self):
        self.set_zoom(min(self.scroll.viewport().width() / self.doc.image.width(),
                          self.scroll.viewport().height() / self.doc.image.height()))

    def toggle_canvas(self, key, value):
        if key=="rulers" and hasattr(self,"workspace"):
            self.workspace.set_rulers(value);return
        setattr(self.canvas, key, value)
        self.canvas.update()

    def fullscreen(self):
        if self.fullscreen_preview is not None:
            self.fullscreen_preview.close();return
        from .previews import FullscreenPreview
        self.fullscreen_preview=FullscreenPreview(self)
        self.fullscreen_preview.showFullScreen()

    def show_thumbnail(self, visible):
        if not visible:
            if self.thumbnail_preview is not None:self.thumbnail_preview.close()
            return
        if self.thumbnail_preview is None:
            from .previews import ThumbnailPreview
            self.thumbnail_preview=ThumbnailPreview(self)
            self.thumbnail=self.thumbnail_preview.label
        self.thumbnail_preview.show()
        self.refresh()

    def choose_color(self, secondary):
        color = QColorDialog.getColor(self.canvas.background if secondary else self.canvas.foreground, self)
        if color.isValid():
            if secondary:
                self.canvas.background = color
            else:
                self.canvas.foreground = color
            self.update_colors()

    def palette_color(self, color):
        self.canvas.foreground = QColor(color)
        self.update_colors()

    def swap_colors(self):
        self.canvas.foreground, self.canvas.background = self.canvas.background, self.canvas.foreground
        self.update_colors()

    def update_colors(self):
        self.primary.setText("Color 1: " + self.canvas.foreground.name())
        self.secondary.setText("Color 2: " + self.canvas.background.name())
        if hasattr(self,"ribbon"):
            self.ribbon.colors.update_colors()
        if self.canvas.text_editor is not None:self.canvas.text_editor.update_style()
        self.canvas.render_shape()

    def about(self):
        QMessageBox.about(self,"About Paint","Paint\nLinux edition of mspaint-rewritten\n"
            "Copyright © Codrut. MIT license.\nQt/PySide6 libraries: LGPL-3.0.\n"
            "License notices and corresponding library sources accompany the distribution.")

    def email_image(self):
        if self.doc.dirty or self.doc.path is None:
            if not self.save():return
        from PySide6.QtCore import QProcess
        import shutil
        executable = shutil.which("xdg-email")
        if executable is None:
            QMessageBox.information(self,"Send in email","No desktop email helper is available. Open your email application and attach the saved picture.")
            return
        started,_ = QProcess.startDetached(executable,["--attach",str(self.doc.path)])
        if not started:QMessageBox.warning(self,"Send in email","The email application could not be opened.")

    def resize_skew(self):
        from .dialogs import ResizeDialog
        dialog = ResizeDialog(self)
        dialog.exec()

    def choose_font(self):
        ok, font = QFontDialog.getFont(self.canvas.font, self)
        if ok:
            self.canvas.font = font

    def render_printer(self, printer):
        p = QPainter(printer)
        if not p.isActive():
            raise OSError("Cannot initialize printer")
        rect = printer.pageLayout().paintRectPixels(printer.resolution())
        image = self.canvas.snapshot().scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        p.drawImage(rect.x() + (rect.width() - image.width()) // 2,
                    rect.y() + (rect.height() - image.height()) // 2, image)
        p.end()

    def print_image(self):
        if QPrintDialog(self.printer, self).exec():
            self.safe(lambda: self.render_printer(self.printer))

    def print_preview(self):
        preview = QPrintPreviewDialog(self.printer, self)
        preview.paintRequested.connect(lambda printer: self.safe(lambda: self.render_printer(printer)))
        preview.exec()

    def page_setup(self):
        QPageSetupDialog(self.printer, self).exec()

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "Drawing.pdf", "PDF (*.pdf)")
        if path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            self.safe(lambda: self.render_printer(printer))

    def wallpaper(self):
        # Use the desktop portal; sandbox compatible, no shell or arbitrary commands.
        if not self.save():
            return
        from .wallpaper import set_wallpaper
        self.safe(lambda: set_wallpaper(self, self.doc.path))

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if len(urls) == 1 and urls[0].isLocalFile():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if len(urls) == 1 and urls[0].isLocalFile():
            self.open(urls[0].toLocalFile())
            event.acceptProposedAction()

    def closeEvent(self, event):
        if self.may_discard():
            self.settings.setValue("geometry", self.saveGeometry())
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI",9))
    app.setApplicationName("MSPaint Rewritten Linux")
    if "--self-test" in sys.argv:
        from .selftest import run
        return run()
    window = Window()
    window.show()
    if "--smoke-test" in sys.argv:
        QTimer.singleShot(500, app.quit)
    elif len(sys.argv) > 1:
        window.open(sys.argv[1])
    return app.exec()
