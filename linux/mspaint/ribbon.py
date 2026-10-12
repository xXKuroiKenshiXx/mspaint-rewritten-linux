"""Paint's ribbon, built from the original DFM glyphs and control geometry."""
from pathlib import Path
from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygon, QFont
from PySide6.QtWidgets import (QAbstractButton, QWidget, QLabel, QFrame, QMenu,
    QHBoxLayout, QVBoxLayout, QSlider, QCheckBox, QComboBox, QSpinBox,
    QFontComboBox, QStackedWidget, QDialog, QPushButton)

ASSETS = Path(__file__).resolve().parent / "assets"
PALETTE = ["#000000", "#7f7f7f", "#880015", "#ff0000", "#ff7f27", "#fff200", "#22b14c", "#00a2e8", "#3f48cc", "#a349a4",
           "#ffffff", "#c3c3c3", "#b97a57", "#ffaec9", "#ffc90e", "#efe4b0", "#b5e61d", "#99d9ea", "#7092be", "#c8bfe7"]
SHAPES = [("Line", 6), ("Curve", 7), ("Ellipse", 64), ("Rectangle", 65),
          ("Rounded rectangle", 68), ("Polygon", 69), ("Triangle", 70), ("Right triangle", 71),
          ("Diamond", 74), ("Pentagon", 75), ("Hexagon", 76), ("Arrow", 77),
          ("Left arrow", 78), ("Up arrow", 79), ("Down arrow", 80), ("Four-point star", 81),
          ("Star", 82), ("Six-point star", 83)]


def glyph(name):
    return QPixmap(str(ASSETS / (name + ".png")))


class RibbonButton(QAbstractButton):
    def __init__(self, parent, text="", image=None, large=False, callback=None, check=False, arrow=False):
        super().__init__(parent)
        self.setText(text)
        self.setAccessibleName(text.replace("\n", " "))
        self.setToolTip(text.replace("\n", " "))
        self.image = glyph(image) if image else QPixmap()
        self.large, self.arrow = large, arrow
        self.icon_size = 20
        self.menu_callback = None
        self.hover = False
        self.setCheckable(check)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if callback:
            self.clicked.connect(lambda checked=False: callback(checked) if check else callback())

    def enterEvent(self, event):
        self.hover = True
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.update()

    def mouseReleaseEvent(self,event):
        if self.menu_callback is not None and self.large and event.position().y()>=50:
            self.setDown(False);self.update();self.menu_callback();event.accept();return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        if isinstance(self.parentWidget(),TitleBar):p.fillRect(self.rect(),QColor("white"))
        if self.isChecked() or self.isDown() or self.hover:
            p.fillRect(self.rect().adjusted(0, 0, -1, -1), QColor("#ffe2d5" if self.isChecked() else "#fff0e8"))
            p.setPen(QColor("#ffad8c"))
            p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        if not self.isEnabled():
            p.setOpacity(0.4)
        p.setPen(QColor("#151515"))
        if self.large:
            if not self.image.isNull():
                p.drawPixmap(QRect((self.width()-40)//2, 3, 40, 40), self.image)
            p.drawText(QRect(1, 47, self.width()-2, 31 if "\n" in self.text() else 18),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.text())
            if self.arrow:
                x, y = self.width()//2, 71
                p.setBrush(QColor("#000000"))
                p.drawPolygon(QPolygon([QPoint(x-4, y), QPoint(x+4, y), QPoint(x, y+4)]))
        else:
            if not self.image.isNull():
                x = 3 if self.text() else (self.width()-self.icon_size)//2
                p.drawPixmap(QRect(x, (self.height()-self.icon_size)//2, self.icon_size, self.icon_size), self.image)
            if self.text():
                left = 26 if not self.image.isNull() else 2
                alignment = Qt.AlignmentFlag.AlignVCenter if not self.image.isNull() else Qt.AlignmentFlag.AlignCenter
                p.drawText(QRect(left, 0, self.width()-left-2, self.height()), alignment, self.text())
            if self.arrow:
                x, y = self.width()-7, self.height()//2
                p.setBrush(QColor("#000000"))
                p.drawPolygon(QPolygon([QPoint(x-3, y-1), QPoint(x+3, y-1), QPoint(x, y+2)]))
        p.end()


class RibbonGroup(QWidget):
    def __init__(self, parent, x, width, caption):
        super().__init__(parent)
        self.setGeometry(x, 5, width, 99)
        label = QLabel(caption, self)
        label.setGeometry(0, 83, width, 16)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color:#253e59;background:transparent;")

    def button(self, rect, text, image, callback, large=False, check=False, arrow=False):
        button = RibbonButton(self, text, image, large, callback, check, arrow)
        button.setGeometry(*rect)
        return button


class TitleBar(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setFixedHeight(31)
        self.setStyleSheet("background:white;")
        self.label = QLabel("Untitled - Paint", self)
        self.label.setGeometry(158, 0, 900, 31)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.context = QLabel("Text Tools",self)
        self.context.setGeometry(195,3,65,28)
        self.context.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.context.setStyleSheet("background:#c3fba0;")
        self.context.hide()
        self.logo = QLabel(self)
        self.logo.setGeometry(6, 5, 22, 22)
        self.logo.setPixmap(QIcon(str(ASSETS / "paint.ico")).pixmap(18, 18))
        for x, name, callback, tip in [(44, "AboutBox", window.save, "Save"),
                                      (77, "FireMonkey-Metropolis-UI", lambda: window.history(False), "Undo"),
                                      (111, "Type", lambda: window.history(True), "Redo")]:
            button = RibbonButton(self, image="PaintForm_collection_" + name, callback=callback)
            button.setGeometry(x, 3, 26, 25)
            button.image = button.image.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            button.icon_size = 16
            button.setToolTip(tip)
            button.setAccessibleName(tip)
        self.controls = []
        for symbol, callback in [("—", window.showMinimized), ("□", self.maximize), ("×", window.close)]:
            button = RibbonButton(self, symbol, callback=callback)
            button.setFont(QFont("Segoe UI", 10))
            self.controls.append(button)

    def resizeEvent(self, event):
        for i, button in enumerate(self.controls):
            button.setGeometry(self.width()-138+i*46, 0, 46, 30)
        self.label.resize(max(1, self.width()-300), 31)

    def maximize(self):
        self.window.showNormal() if self.window.isMaximized() else self.window.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.window.windowHandle().startSystemMove()

    def mouseDoubleClickEvent(self, event):
        self.maximize()


class FilePanel(QFrame):
    def __init__(self, window):
        super().__init__(window, Qt.WindowType.Popup)
        self.window = window
        self.setFixedSize(660, 530)
        self.setObjectName("filePanel")
        self.setStyleSheet("QFrame#filePanel{background:white;border:1px solid #ababab;} QLabel{background:white;}")
        callbacks = [("New", 2, window.new), ("Open", 1, window.open), ("Save", 3, window.save),
                     ("Save as", 4, lambda: window.save(True)), ("Print", 5, window.print_image),
                     ("Send in email", 6, window.email_image), ("Set as desktop background", 7, window.wallpaper),
                     ("Properties", 8, window.properties), ("About Paint", 9, window.about), ("Exit", 10, window.close)]
        for i, (text, number, callback) in enumerate(callbacks):
            button = RibbonButton(self, text, "MenuForm_SpeedButton"+str(number), callback=lambda f=callback: self.invoke(f))
            button.setGeometry(5, 5+i*50, 268, 49)
        line = QFrame(self)
        line.setGeometry(278, 7, 1, 510)
        line.setStyleSheet("background:#c5c5c5;")
        title = QLabel("Recent pictures", self)
        title.setGeometry(292, 12, 330, 24)
        title.setStyleSheet("color:#253e59;font-weight:bold;")
        for i, path in enumerate(window.settings.value("recents", [], type=list)[:9]):
            button = RibbonButton(self, f"{i+1}   {Path(path).name}", callback=lambda p=path: self.invoke(lambda: window.open(p)))
            button.setGeometry(292, 44+i*32, 353, 30)

    def invoke(self, callback):
        self.hide()
        callback()


class ColorsGroup(RibbonGroup):
    def __init__(self, parent, window, x):
        super().__init__(parent, x, 430, "Colors")
        self.window = window
        self.active = 1
        self.first = self.button((0, 0, 55, 80), "Color\n1", None, lambda checked=False: self.activate(1), large=True, check=True)
        self.second = self.button((55, 0, 55, 80), "Color\n2", None, lambda checked=False: self.activate(2), large=True, check=True)
        self.first.setChecked(True)
        self.swatches = []
        for i, color in enumerate(PALETTE + ["#ffffff"]*10):
            swatch = RibbonButton(self, callback=lambda c=color, index=i: self.choose(c, index))
            swatch.setGeometry(112+(i%10)*25, 2+(i//10)*25, 23, 23)
            swatch.setToolTip(color if i<20 else "Custom color")
            self.swatches.append(swatch)
            swatch.paintEvent = self.swatch_painter(swatch, color)
        self.edit = self.button((370, 0, 55, 80), "Edit\ncolors", "PaintForm_SpeedButton63", self.edit_color, large=True)
        self.update_colors()

    def swatch_painter(self, button, color):
        def paint(event):
            p = QPainter(button)
            p.fillRect(button.rect(), QColor("#ffffff"))
            p.setPen(QColor("#9c9c9c"))
            p.drawRect(button.rect().adjusted(0,0,-1,-1))
            p.fillRect(button.rect().adjusted(2,2,-2,-2), QColor(color))
            if button.hover:
                p.setPen(QColor("#e95524"))
                p.drawRect(button.rect().adjusted(0,0,-1,-1))
            p.end()
        return paint

    def activate(self, number):
        self.active = number
        self.first.setChecked(number == 1)
        self.second.setChecked(number == 2)

    def choose(self, color, index):
        if index >= 20:
            custom = self.window.settings.value("custom_colors", [], type=list)
            if index-20 >= len(custom):
                self.edit_color()
                return
            color = custom[index-20]
        if self.active == 1:
            self.window.canvas.foreground = QColor(color)
        else:
            self.window.canvas.background = QColor(color)
        self.window.update_colors()

    def edit_color(self):
        self.window.choose_color(self.active == 2)
        color = (self.window.canvas.foreground if self.active == 1 else self.window.canvas.background).name()
        custom = self.window.settings.value("custom_colors", [], type=list)
        custom = [color] + [value for value in custom if value != color][:9]
        self.window.settings.setValue("custom_colors", custom)
        self.update_colors()

    def update_colors(self):
        for button, color, size in [(self.first, self.window.canvas.foreground, 38),
                                    (self.second, self.window.canvas.background, 28)]:
            pixmap = QPixmap(40,40)
            pixmap.fill(Qt.GlobalColor.transparent)
            p = QPainter(pixmap)
            rect = QRect((40-size)//2, (40-size)//2, size, size)
            p.setPen(QColor("#808080"))
            p.setBrush(QColor("white"))
            p.drawRect(rect)
            p.fillRect(rect.adjusted(2,2,-2,-2), color)
            p.end()
            button.image = pixmap
            button.update()
        custom = self.window.settings.value("custom_colors", [], type=list)
        for i, button in enumerate(self.swatches[20:]):
            button.paintEvent = self.swatch_painter(button, custom[i] if i < len(custom) else "#ffffff")
            button.update()


class PaintRibbon(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setObjectName("paintRibbon")
        self.setStyleSheet("QWidget#paintRibbon{background:#f0f0f0;}")
        self.setFixedHeight(133)
        self.page = "Home"
        self.tab_bar = QWidget(self)
        self.tab_bar.setGeometry(0,0,1284,25)
        self.tab_bar.setStyleSheet("background:white;")
        self.tabs = {}
        for i, name in enumerate(["File", "Home", "View", "Text"]):
            tab = RibbonButton(self.tab_bar, name, callback=lambda n=name: self.select_tab(n))
            tab.setGeometry(i*65,0,65,25)
            tab.paintEvent = self.tab_painter(tab, name)
            self.tabs[name] = tab
        self.tabs["Text"].hide()
        self.help = RibbonButton(self.tab_bar, image="PaintForm_CButton1", callback=window.about)
        self.help.setGeometry(1260,0,24,24)
        self.help.setStyleSheet("color:#0078d7;")
        self.home = QWidget(self)
        self.home.setGeometry(0,25,1284,108)
        self.view = QWidget(self)
        self.view.setGeometry(0,25,1284,108)
        self.text = QWidget(self)
        self.text.setGeometry(0,25,1284,108)
        self.tool_buttons = {}
        self.selection_kind = "Select"
        self.brush_kind = "Brush"
        self.make_home()
        self.make_view()
        self.make_text()
        self.select_tab("Home")

    def resizeEvent(self, event):
        self.tab_bar.resize(self.width(),25)
        self.help.move(self.width()-25,0)
        for page in (self.home,self.view,self.text):
            page.resize(self.width(),108)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setPen(QColor("#aaaaaa"))
        p.drawLine(0,24,self.width(),24)
        p.drawLine(0,132,self.width(),132)
        if self.page == "Home":
            for x in (129,278,390,456,753,819,1260):
                p.drawLine(x,30,x,128)
        elif self.page == "View":
            for x in (218,312,453):
                p.drawLine(x,30,x,128)
        p.end()

    def tab_painter(self, tab, name):
        def paint(event):
            p = QPainter(tab)
            if name == "File":
                p.fillRect(tab.rect(), QColor("#e83d00"))
                p.setPen(QColor("white"))
            elif name == self.page:
                p.fillRect(tab.rect(), QColor("#f0f0f0"))
                p.setPen(QColor("#aaaaaa"))
                p.drawRect(tab.rect().adjusted(0,0,-1,1))
                p.setPen(QColor("black"))
            else:
                p.fillRect(tab.rect(), QColor("#fff4ed" if tab.hover else "white"))
                p.setPen(QColor("black"))
            p.drawText(tab.rect(), Qt.AlignmentFlag.AlignCenter, name)
            p.end()
        return paint

    def select_tab(self, name):
        if name == "File":
            self.file_panel = FilePanel(self.window)
            self.file_panel.move(self.mapToGlobal(QPoint(0,25)))
            self.file_panel.show()
            return
        self.page = name
        self.home.setVisible(name == "Home")
        self.view.setVisible(name == "View")
        self.text.setVisible(name == "Text")
        if name == "Home":
            self.colors.setParent(self.home)
            self.colors.move(825,5)
        elif name == "Text":
            self.colors.setParent(self.text)
            self.colors.move(432,5)
        self.colors.show()
        self.update()
        for tab in self.tabs.values():
            tab.update()

    def choose_tool(self, name):
        self.window.tool_combo.setCurrentText(name)
        self.sync_tool()
        if name == "Text":
            self.tabs["Text"].show()
            self.select_tab("Text")

    def sync_tool(self):
        for name, button in self.tool_buttons.items():
            button.setChecked(name == self.window.canvas.tool)
        brush = self.window.canvas.tool in ("Brush","Airbrush","Watercolor","Marker","Crayon","Calligraphy")
        self.brush_button.setCheckable(True);self.brush_button.setChecked(brush)
        if brush:
            self.brush_kind = self.window.canvas.tool
            number={"Brush":95,"Airbrush":96,"Watercolor":99,"Marker":97,"Crayon":98,"Calligraphy":95}[self.brush_kind]
            self.brush_button.image=glyph("PaintForm_SpeedButton"+str(number));self.brush_button.update()
        self.select_button.setChecked(self.window.canvas.tool in ("Select","Free select"))
        if self.window.canvas.tool in ("Select","Free select"):self.selection_kind = self.window.canvas.tool
        if self.window.canvas.tool == "Text":
            self.tabs["Text"].show()
            self.window.title_bar.context.show();self.window.title_bar.label.move(275,0)
        else:
            self.tabs["Text"].hide()
            self.window.title_bar.context.hide();self.window.title_bar.label.move(158,0)
            if self.page == "Text":self.select_tab("Home")

    def popup(self, button, items):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu{background:#fff;border:1px solid #aaa;padding:3px;} QMenu::item{padding:8px 24px 8px 8px;} QMenu::item:selected{background:#ffe2d5;}")
        for title, icon, callback in items:
            action = menu.addAction(QIcon(str(ASSETS / (icon+".png"))) if icon else QIcon(), title)
            action.triggered.connect(lambda checked=False, f=callback: f())
        menu.exec(button.mapToGlobal(QPoint(0,button.height())))

    def make_home(self):
        win = self.window
        clip = RibbonGroup(self.home,4,120,"Clipboard")
        paste = clip.button((0,0,55,80),"Paste","PaintForm_SpeedButton9",win.paste,large=True,arrow=True)
        paste.menu_callback = lambda:self.popup(paste,[("Paste","PaintForm_SpeedButton84",win.paste),("Paste from","PaintForm_SpeedButton85",win.paste_file)])
        paste.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        paste.customContextMenuRequested.connect(lambda p: self.popup(paste,[("Paste", "PaintForm_SpeedButton84",win.paste), ("Paste from", "PaintForm_SpeedButton85",win.paste_file)]))
        clip.button((57,0,63,27),"Cut","PaintForm_SpeedButton10",win.cut)
        clip.button((57,27,63,27),"Copy","PaintForm_SpeedButton12",win.copy)
        image = RibbonGroup(self.home,135,138,"Image")
        select = image.button((0,0,55,80),"Select",None,lambda:self.choose_tool(self.selection_kind),large=True,arrow=True)
        select.setCheckable(True)
        select.menu_callback = lambda:self.selection_menu(select)
        self.select_button = select
        # The source uses ImageList3 for the selection glyph; its dashed rectangle
        # is also reproduced as the same simple native geometry.
        pix = QPixmap(40,40)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix);p.setPen(QPen(QColor("#0078d7"),1,Qt.PenStyle.DashLine));p.drawRect(2,5,36,30);p.end()
        select.image = pix
        image.button((57,0,81,25),"Crop","PaintForm_SpeedButton15",win.crop)
        image.button((57,25,81,25),"Resize","PaintForm_SpeedButton17",win.properties)
        rotate = image.button((57,50,81,25),"Rotate","PaintForm_SpeedButton16",lambda:self.rotate_menu(rotate),arrow=True)
        tools = RibbonGroup(self.home,284,101,"Tools")
        for i, (name, number) in enumerate([("Pencil",19),("Fill",18),("Text",20),("Eraser",23),("Color picker",24),("Zoom",25)]):
            button = tools.button((4+(i%3)*30,12+(i//3)*30,29,29),"","PaintForm_SpeedButton"+str(number),lambda checked=False,n=name:self.choose_tool(n),check=True)
            button.setToolTip({"Fill":"Fill with color", "Color picker":"Color picker"}.get(name,name))
            button.setAccessibleName(name)
            self.tool_buttons[name] = button
        brushes = RibbonGroup(self.home,396,55,"")
        brush = brushes.button((0,0,55,80),"Brushes","PaintForm_SpeedButton21",lambda:self.choose_tool(self.brush_kind),large=True,arrow=True)
        brush.menu_callback = lambda:self.brush_menu(brush)
        self.brush_button = brush
        shapes = RibbonGroup(self.home,462,286,"Shapes")
        box = QFrame(shapes);box.setGeometry(0,0,205,80);box.setStyleSheet("background:#fff;border:1px solid #a9a9a9;")
        for i,(name,number) in enumerate(SHAPES):
            button = RibbonButton(box,image="PaintForm_SpeedButton"+str(number),callback=lambda checked=False,n=name:self.choose_tool(n),check=True)
            button.setGeometry(2+(i%8)*25,2+(i//8)*25,25,25)
            button.setToolTip(name);button.setAccessibleName(name)
            self.tool_buttons[name] = button
        outline = shapes.button((207,0,79,25),"Outline","PaintForm_SpeedButton72",lambda value:self.shape_style("outlined",value),check=True)
        outline.setChecked(True)
        fill = shapes.button((207,25,79,25),"Fill","PaintForm_SpeedButton73",lambda value:self.shape_style("filled",value),check=True)
        size = RibbonGroup(self.home,759,55,"")
        self.size_button = size.button((0,0,55,80),"Size","PaintForm_SpeedButton26",self.size_menu,large=True,arrow=True)
        self.colors = ColorsGroup(self.home,win,825)
        self.sync_tool()

    def selection_menu(self, button):
        self.popup(button,[("Rectangular selection","PaintForm_SpeedButton86",lambda:self.choose_tool("Select")),
            ("Free-form selection","PaintForm_SpeedButton104",lambda:self.choose_tool("Free select")),
            ("Select all","PaintForm_SpeedButton87",self.window.select_all),
            ("Delete","PaintForm_SpeedButton88",self.window.canvas.delete_selection),
            ("Transparent selection","PaintForm_SpeedButton89",self.toggle_transparent)])

    def toggle_transparent(self):
        self.window.canvas.transparent = not self.window.canvas.transparent

    def rotate_menu(self, button):
        from PySide6.QtGui import QTransform
        self.popup(button,[("Rotate right 90°","PaintForm_SpeedButton90",lambda:self.window.transform(QTransform().rotate(90))),
            ("Rotate left 90°","PaintForm_SpeedButton91",lambda:self.window.transform(QTransform().rotate(-90))),
            ("Rotate 180°","PaintForm_SpeedButton92",lambda:self.window.transform(QTransform().rotate(180))),
            ("Flip horizontal","PaintForm_SpeedButton93",lambda:self.window.flip(True)),
            ("Flip vertical","PaintForm_SpeedButton94",lambda:self.window.flip(False))])

    def brush_menu(self, button):
        self.popup(button,[(name,"PaintForm_SpeedButton"+str(number),lambda n=name:self.choose_tool(n))
            for name,number in [("Brush",95),("Airbrush",96),("Watercolor",99),("Marker",97),("Crayon",98)]])

    def outline_menu(self, button):
        self.popup(button,[("No outline",None,lambda:setattr(self.window.canvas,"outlined",False)),
                           ("Solid color",None,lambda:setattr(self.window.canvas,"outlined",True))])

    def fill_menu(self, button):
        self.popup(button,[("No fill",None,lambda:setattr(self.window.canvas,"filled",False)),
                           ("Solid color",None,lambda:setattr(self.window.canvas,"filled",True))])

    def size_menu(self):
        popup = QFrame(self,Qt.WindowType.Popup)
        popup.setFixedSize(231,106)
        popup.setStyleSheet("background:white;border:1px solid #aaa;")
        label = QLabel(f"{self.window.canvas.pen_width} px",popup);label.setGeometry(14,10,200,25)
        slider = QSlider(Qt.Orientation.Horizontal,popup);slider.setGeometry(14,44,200,26)
        slider.setRange(1,100);slider.setValue(self.window.canvas.pen_width)
        slider.valueChanged.connect(lambda n:(setattr(self.window.canvas,"pen_width",n),label.setText(f"{n} px"),self.window.canvas.render_shape()))
        popup.move(self.size_button.mapToGlobal(QPoint(0,80)));popup.show()
        self.size_popup = popup

    def make_view(self):
        win = self.window
        zoom = RibbonGroup(self.view,4,209,"Zoom")
        for x,title,number,callback in [(0,"Zoom\nin",2,lambda:win.set_zoom(win.canvas.zoom*1.25)),
                                      (69,"Zoom\nout",1,lambda:win.set_zoom(win.canvas.zoom/1.25)),
                                      (138,"100%",5,lambda:win.set_zoom(1))]:
            zoom.button((x,0,68,80),title,"PaintForm_SpeedButton"+str(number),callback,large=True)
        show = RibbonGroup(self.view,224,83,"Show or hide")
        for i,(label,key,initial) in enumerate([("Rulers","rulers",True),("Gridlines","grid",False),("Status bar","status",True)]):
            check = QCheckBox(label,show);check.setGeometry(0,7+i*24,83,23);check.setChecked(initial)
            check.toggled.connect(lambda value,k=key:self.toggle_view(k,value))
            setattr(self,"check_"+key,check)
        display = RibbonGroup(self.view,318,130,"Display")
        display.button((0,0,65,80),"Full\nscreen","PaintForm_SpeedButton3",win.fullscreen,large=True)
        display.button((65,0,65,80),"Thumbnail","PaintForm_SpeedButton4",lambda:win.show_thumbnail(True),large=True)

    def toggle_view(self,key,value):
        if key == "status":
            self.window.statusBar().setVisible(value)
        elif key == "rulers":
            self.window.workspace.set_rulers(value)
        else:
            self.window.toggle_canvas(key,value)

    def make_text(self):
        win = self.window
        clipboard = RibbonGroup(self.text,4,124,"Clipboard")
        clipboard.button((0,0,55,80),"Paste","PaintForm_SpeedButton29",win.paste,large=True)
        clipboard.button((57,0,65,27),"Cut","PaintForm_SpeedButton31",win.cut)
        clipboard.button((57,27,65,27),"Copy","PaintForm_SpeedButton32",win.copy)
        font = RibbonGroup(self.text,139,173,"Font")
        combo = QFontComboBox(font);combo.setGeometry(3,14,170,24)
        combo.setCurrentFont(win.canvas.font)
        combo.currentFontChanged.connect(self.font_family)
        size = QComboBox(font);size.setGeometry(3,46,56,23);size.setEditable(True)
        size.addItems([str(n) for n in (8,9,10,11,12,14,16,18,20,22,24,26,28,36,48,72)])
        size.setCurrentText(str(win.canvas.font.pointSize()))
        size.currentTextChanged.connect(self.font_size)
        self.font_combo,self.font_size_combo = combo,size
        for i,(label,attribute) in enumerate([("B","Bold"),("I","Italic"),("U","Underline"),("abc","StrikeOut")]):
            button = font.button(((65,91,118,146)[i],46,23,23),label,None,lambda value,a=attribute:self.font_style(a,value),check=True)
            style=QFont("Segoe UI",9)
            getattr(style,"set"+attribute)(True);button.setFont(style)
        background = RibbonGroup(self.text,323,98,"Background")
        background.button((0,14,98,25),"Opaque","PaintForm_SpeedButton66",lambda:self.text_background(True))
        background.button((0,41,98,25),"Transparent","PaintForm_SpeedButton67",lambda:self.text_background(False))
        utilities = RibbonGroup(self.text,873,106,"Utilities")
        self.show_editor = QCheckBox("Show editor",utilities)
        self.show_editor.setGeometry(3,11,100,20);self.show_editor.setChecked(True)
        self.show_editor.toggled.connect(self.editor_visibility)

    def font_family(self,font):
        value = QFont(self.window.canvas.font);value.setFamily(font.family());self.window.canvas.update_font(value)

    def font_size(self,value):
        try:value=int(value)
        except ValueError:return
        if 1<=value<=999:
            self.window.canvas.font.setPointSize(value);self.window.canvas.update_font()

    def font_style(self,attribute,value):
        getattr(self.window.canvas.font,"set"+attribute)(value);self.window.canvas.update_font()

    def text_background(self,value):
        self.window.canvas.text_opaque = value;self.window.canvas.update_font()

    def editor_visibility(self,visible):
        editor=self.window.canvas.text_editor
        if editor is not None:
            editor.setVisible(visible)
            for grip in editor.grips.values():grip.setVisible(visible)
            if not visible:self.window.canvas.setFocus()
            else:editor.setFocus()
            self.window.canvas.update()

    def shape_style(self,key,value):
        setattr(self.window.canvas,key,value);self.window.canvas.render_shape()
