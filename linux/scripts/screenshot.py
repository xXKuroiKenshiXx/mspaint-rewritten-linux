"""Render a real Paint window at the reference's size; all controls remain live."""
import math
import random
import sys
import tempfile
from pathlib import Path
from PySide6.QtCore import QPoint,QTimer,Qt,QSettings
from PySide6.QtGui import QColor,QPainter,QPen,QFont,QPolygon,QFontDatabase
from PySide6.QtWidgets import QApplication
from mspaint.app import Window

app = QApplication([])
app.setStyle("Fusion")
app.setFont(QFont("Segoe UI",9))
window = Window()
window.resize(1532,848)
window.doc.new(1030,552)
image = window.doc.image.copy()
p = QPainter(image)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setPen(QPen(QColor("#ff7f27"),4))
p.setBrush(QColor("#fff200"))
p.drawPolygon(QPolygon([QPoint(50,45),QPoint(50,130),QPoint(130,130)]))
for center,radius,points in [(QPoint(862,83),60,4),(QPoint(208,390),60,5)]:
    vertices=[]
    for i in range(points*2):
        r=radius if i%2==0 else radius*.32
        angle=i*math.tau/(points*2)-math.pi/2
        vertices.append(QPoint(round(center.x()+r*math.cos(angle)),round(center.y()+r*math.sin(angle))))
    p.drawPolygon(QPolygon(vertices))
p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor("#fff200"))
p.drawPolygon(QPolygon([QPoint(690,234),QPoint(800,168),QPoint(800,203),QPoint(908,203),QPoint(908,270),QPoint(800,270),QPoint(800,303)]))
p.setPen(QColor("black"))
font=QFont("Calibri");font.setPixelSize(86);p.setFont(font);p.drawText(140,248,"Hello world!")
p.setFont(QFont("Segoe UI",9));p.drawText(180,104,"sss")
p.fillRect(139,270,227,12,QColor("#ff0000"));p.fillRect(366,270,130,12,QColor("#22b14c"));p.fillRect(496,270,117,12,QColor("#00a2e8"))
rng=random.Random(12)
p.setRenderHint(QPainter.RenderHint.Antialiasing,False);p.setPen(QColor("#ff00dd"))
for _ in range(1000):
    angle=rng.random()*math.tau;r=math.sqrt(rng.random())*49
    p.drawPoint(round(555+r*math.cos(angle)),round(83+r*math.sin(angle)))
for _ in range(24000):
    x=rng.randrange(1030);y=round(478-130*(x/1030)**2+rng.gauss(0,39))
    if 360<=y<552:p.drawPoint(x,y)
p.end()
window.doc.commit(image)
temporary=tempfile.TemporaryDirectory(prefix="paint-preview-")
window.settings=QSettings(str(Path(temporary.name)/"settings.ini"),QSettings.Format.IniFormat)
window.settings.setValue("custom_colors",["#ff00dd"])
window.doc.save(Path(temporary.name)/"Test.png")
window.canvas.foreground=QColor("#ff00dd")
window.tool_combo.setCurrentText("Airbrush")
window.update_colors()
window.canvas.sync()
window.paint_status.showMessage("561, 86px")
window.workspace.pointer(QPoint(561,86))
window.show()

def capture():
    window.grab().save(sys.argv[1])
    window.doc.saved_key=window.doc.image.cacheKey()
    window.close();app.quit()

QTimer.singleShot(700,capture)
app.exec()
temporary.cleanup()
