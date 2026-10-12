"""Image Properties, preserving the original Delphi form's control layout."""
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog,QWidget,QLabel,QPushButton,QGroupBox,QRadioButton,QLineEdit
from .document import valid_size


class PropertiesDialog(QDialog):
    def __init__(self,window):
        super().__init__(window,Qt.WindowType.Dialog|Qt.WindowType.FramelessWindowHint)
        self.window = window
        self.setWindowTitle("Image Properties")
        self.setFixedSize(398,392)
        self.setFont(QFont("Segoe UI",9))
        self.setObjectName("propertiesDialog")
        self.setStyleSheet("QDialog#propertiesDialog{background:#f0f0f0;border:1px solid #888;}QGroupBox{border:1px solid #c0c0c0;margin-top:8px;padding-top:5px;}QGroupBox::title{subcontrol-origin:margin;left:9px;padding:0 3px;}QPushButton{background:#e1e1e1;border:1px solid #adadad;padding:3px;}QPushButton:hover{background:#e5f1fb;border-color:#0078d7;}QPushButton:default{border:2px solid #0078d7;}QLineEdit{background:white;border:1px solid #aaa;padding:3px;}")
        title = QLabel("Image Properties",self);title.setGeometry(12,1,345,31);title.setStyleSheet("background:white;")
        close = QPushButton("×",self);close.setGeometry(361,1,36,31);close.clicked.connect(self.reject);close.setStyleSheet("background:white;border:0;font-size:20px;")
        self.body = QWidget(self);self.body.setGeometry(1,33,396,358)
        attrs = QGroupBox("File Attributes",self.body);attrs.setGeometry(8,16,380,113)
        path = window.doc.path
        saved = datetime.fromtimestamp(path.stat().st_mtime).strftime("%x %X") if path and path.is_file() else "Not Available"
        size = f"{path.stat().st_size/1024:.2f} KB" if path and path.is_file() else "Not Available"
        self.dpi = max(1,round(window.doc.image.dotsPerMeterX()*0.0254))
        for y,name,value in [(32,"Last Saved:",saved),(53,"Size on disk:",size),(74,"Resolution:",f"{self.dpi} DPI")]:
            QLabel(name,attrs).setGeometry(16,y,130,20);QLabel(value,attrs).setGeometry(160,y,205,20)
        units = QGroupBox("Units",self.body);units.setGeometry(8,135,193,122)
        self.units = []
        for y,name in [(32,"Inches"),(55,"Centimeters"),(78,"Pixels")]:
            radio = QRadioButton(name,units);radio.setGeometry(16,y,140,19);self.units.append(radio)
        self.units[2].setChecked(True)
        colors = QGroupBox("Colors",self.body);colors.setGeometry(207,135,181,122)
        color = QRadioButton("Color",colors);color.setGeometry(16,32,113,19);color.setChecked(True)
        QLabel("Width:",self.body).setGeometry(8,280,52,20);QLabel("Height:",self.body).setGeometry(159,280,52,20)
        self.width_edit = QLineEdit(str(window.doc.image.width()),self.body);self.width_edit.setGeometry(64,275,89,25)
        self.height_edit = QLineEdit(str(window.doc.image.height()),self.body);self.height_edit.setGeometry(214,275,89,25)
        self.unit_index = 2
        for index,radio in enumerate(self.units):radio.toggled.connect(lambda checked,i=index:self.change_units(i) if checked else None)
        default = QPushButton("Default",self.body);default.setGeometry(313,276,75,25);default.clicked.connect(self.defaults)
        self.ok = QPushButton("OK",self.body);self.ok.setGeometry(234,327,75,25);self.ok.setDefault(True);self.ok.clicked.connect(self.apply)
        cancel = QPushButton("Cancel",self.body);cancel.setGeometry(315,327,75,25);cancel.clicked.connect(self.reject)
        self.width_edit.textChanged.connect(self.validate);self.height_edit.textChanged.connect(self.validate)
        self.validate()

    def factor(self,index):return (self.dpi,self.dpi/2.54,1)[index]

    def values(self):
        return (round(float(self.width_edit.text())*self.factor(self.unit_index)),round(float(self.height_edit.text())*self.factor(self.unit_index)))

    def change_units(self,index):
        try:width,height = self.values()
        except (ValueError,OverflowError):width,height = self.window.doc.image.width(),self.window.doc.image.height()
        self.unit_index = index
        self.width_edit.setText(f"{width/self.factor(index):.3f}".rstrip("0").rstrip(".") if index!=2 else str(width))
        self.height_edit.setText(f"{height/self.factor(index):.3f}".rstrip("0").rstrip(".") if index!=2 else str(height))

    def defaults(self):
        self.units[2].setChecked(True);self.width_edit.setText("1030");self.height_edit.setText("552")

    def validate(self):
        try:valid_size(*self.values());enabled = True
        except (ValueError,OverflowError):enabled = False
        self.ok.setEnabled(enabled)

    def apply(self):
        width,height = self.values()
        if self.window.safe(lambda:self.window.doc.resize(width,height,background=self.window.canvas.background)):
            self.window.display_units = ("in","cm","px")[self.unit_index]
            self.window.canvas.reset_transient();self.window.canvas.sync();self.accept()

    def showEvent(self,event):
        self.move(self.window.frameGeometry().center()-self.rect().center());super().showEvent(event)


ResizeDialog = PropertiesDialog
