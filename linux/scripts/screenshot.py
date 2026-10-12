"""Create a deterministic preview and exercise a visible Qt window."""
import sys
from pathlib import Path
from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QApplication
from mspaint.app import Window

app = QApplication([])
window = Window()
window.doc.new(800, 480)
image = window.doc.image.copy()
p = QPainter(image)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.fillRect(image.rect(), QColor("#f4f7fc"))
p.setPen(QPen(QColor("#0078d4"), 7))
p.setBrush(QColor("#d9efff"))
p.drawRoundedRect(60, 60, 300, 220, 20, 20)
p.setBrush(QColor("#ffd452"))
p.drawEllipse(410, 70, 190, 190)
p.setPen(QColor("#263448"))
p.setFont(QFont("Sans Serif", 24))
p.drawText(65, 340, "MSPaint Rewritten Linux")
p.setFont(QFont("Sans Serif", 14))
p.drawText(65, 385, "Native Qt widgets · drawing · selections · undo")
p.end()
window.doc.commit(image)
window.canvas.sync()
window.show()

def capture():
    window.grab().save(sys.argv[1])
    window.doc.saved_key = window.doc.image.cacheKey()
    window.close()
    app.quit()

QTimer.singleShot(700, capture)
app.exec()
